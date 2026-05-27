"""Main processing loop for input files."""

from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
import time
from loguru import logger

from ..api.client import ReplicateClient
from ..output.writer import OutputWriter
from ..output.reporter import Reporter
from ..output.context import ImageSaveContext
from .discovery import InputDiscovery
from .context import ProcessingContext, ProcessorConfig
from .validator import GenericValidator
from ..exceptions import ValidationError
from .markdown_parser import extract_all_image_urls


class FileProcessor:
    """Process input files against a single profile."""

    def __init__(self, config: ProcessorConfig):
        """
        Initialize processor with configuration.

        Args:
            config: ProcessorConfig containing all initialization parameters
        """
        self.replicate_client = config.api_client
        self.output_writer = config.output_writer
        self.reporter = config.reporter
        self.dry_run = config.dry_run
        self.debug = False
        self.save_payloads = config.save_payloads
        self.total_cost = 0.0
        self.processed_count = 0
        self.failed_count = 0
        self.validator = GenericValidator()

    def process_all(
        self,
        prompt_files: List[Tuple[Path, Path]],
        profile: Dict[str, Any],
        progress: Optional[Any] = None,
    ) -> bool:
        """
        Process all input files against a single profile.

        Args:
            prompt_files: List of tuples (absolute_path, relative_path)
            profile: Single profile info dictionary
            progress: Optional rich Progress bar

        Returns:
            True if all successful, False if any failures
        """
        self.validator.validate_operational_requirements([profile])

        total_files = len(prompt_files)
        profile_name = profile["profile_name"]
        logger.info(f"Processing {total_files} files with profile '{profile_name}'")

        task_id = self._init_progress(progress, total_files, profile_name)

        success = True

        for i, prompt_file_tuple in enumerate(prompt_files):
            success = self._process_single_file(
                prompt_file_tuple, profile, i + 1, total_files, progress, task_id
            )

        return success

    def _init_progress(
        self, progress: Optional[Any], total: int, profile_name: str
    ) -> Optional[int]:
        """Initialize progress bar if available."""
        if progress:
            return progress.add_task(
                f"Processing files with '{profile_name}'", total=total
            )
        return None

    def _process_single_file(
        self,
        prompt_file_tuple: Tuple[Path, Path],
        profile: Dict[str, Any],
        file_num: int,
        total_files: int,
        progress: Optional[Any],
        task_id: Optional[int],
    ) -> bool:
        """Process a single file."""
        prompt_file, relative_path = prompt_file_tuple
        profile_name = profile["profile_name"]

        with open(prompt_file, "r", encoding="utf-8") as f:
            markdown_content = f.read()

        try:
            image_urls = extract_all_image_urls(markdown_content)
            logger.debug(
                f"Extracted {len(image_urls)} image URL(s) from markdown: {image_urls}"
            )
        except ValueError as e:
            logger.error(f"No image URLs found in {prompt_file.name}")
            raise

        discovery = InputDiscovery(prompt_file.parent, Path("dummy"))
        prompts = discovery.load_prompts(prompt_file)

        logger.info(f"Processing file {file_num}/{total_files}: {relative_path}")

        if progress and task_id is not None:
            progress.update(
                task_id,
                advance=1,
                description=f"[{file_num}/{total_files}] {relative_path}",
            )

        params = profile.get("parameters", {}).copy()
        params["image_input"] = image_urls

        context = ProcessingContext(
            prompt_file=prompt_file,
            relative_path=relative_path,
            prompts=prompts,
            model_id=profile.get("model_id", profile.get("endpoint", "")),
            params=params,
            pricing=profile.get("pricing", {}),
            profile_name=profile_name,
            output_dir=self.output_writer.output_dir,
            prompt_prefix=profile.get("prompt_prefix", ""),
            prompt_suffix=profile.get("prompt_suffix", ""),
            delay_between_requests=profile.get("delay_between_requests", 0),
        )

        try:
            self._process_with_context(context)
        except Exception as e:
            logger.error(f"Failed processing {relative_path}: {e}")
            self.failed_count += 1
            raise

        return True

    def _process_with_context(self, context: ProcessingContext) -> None:
        """
        Process prompt using ProcessingContext.

        Args:
            context: ProcessingContext with all required parameters
        """
        base_cost = context.pricing.get("base_cost", 0.0)

        if not context.prompts:
            logger.warning(f"Skipping empty prompt file: {context.relative_path}")
            return

        prompt = context.prompts[0]

        prompt = self._apply_prompt_fixes(
            prompt, context.prompt_prefix, context.prompt_suffix
        )

        logger.debug(f"Processing {context.relative_path}: {prompt[:50]}...")

        if self.dry_run:
            logger.info(f"[DRY RUN] Would generate image for {context.relative_path}")
            return

        self._generate_and_save_image(prompt, context, base_cost)

        if context.delay_between_requests > 0:
            logger.info(
                f"Waiting {context.delay_between_requests} seconds before next request"
            )
            time.sleep(context.delay_between_requests)

    def _apply_prompt_fixes(self, prompt: str, prefix: str, suffix: str) -> str:
        """Apply prefix and suffix to prompt."""
        if prefix:
            prompt = f"{prefix} {prompt}"
            logger.debug(f"Added prefix to prompt: {prefix}")

        if suffix:
            prompt = f"{prompt} {suffix}"
            logger.debug(f"Added suffix to prompt: {suffix}")

        return prompt

    def _generate_and_save_image(
        self, prompt: str, context: ProcessingContext, base_cost: float
    ) -> None:
        """Generate image and save to disk."""
        try:
            response = self.replicate_client.generate_image(
                model_id=context.model_id,
                prompt=prompt,
                params=context.params,
                debug=self.debug,
            )

            result = response["result"]
            payload = response["payload"]

            timestamp = datetime.now().strftime("%H%M%S")

            save_context = ImageSaveContext(
                image_url=result["images"][0]["url"],
                timestamp=timestamp,
                prompt_file_name=context.prompt_file.stem,
                model_name=context.profile_name,
                output_dir=context.output_dir,
                relative_path=context.relative_path,
                payload=payload if self.save_payloads else None,
            )

            filename = self.output_writer.save_image(save_context)

            self.processed_count += 1
            self.total_cost += base_cost

            logger.info(f"Saved image: {filename}")

        except Exception as e:
            logger.error(f"Failed to generate image for {context.relative_path}: {e}")
            self.failed_count += 1
            raise

    def get_summary(self) -> Dict[str, Any]:
        """Get processing summary."""
        return {
            "processed": self.processed_count,
            "failed": self.failed_count,
            "total_cost": self.total_cost,
        }
