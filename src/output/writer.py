"""Image writer with validation."""

import requests
import re
import json
from pathlib import Path
from typing import Any, Optional, Dict, Union, Tuple
from datetime import datetime
from PIL import Image
from io import BytesIO
from loguru import logger
from .context import ImageSaveContext
from ..constants import DEFAULT_IMAGE_DOWNLOAD_TIMEOUT


class OutputWriter:
    """Handle image saving and validation."""

    def __init__(self, output_dir: Path, force_png: bool = False):
        """
        Initialize output writer.

        Args:
            output_dir: Base output directory
            force_png: Convert all images to PNG format
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.force_png = force_png

    def save_image(self, context: ImageSaveContext) -> str:
        """
        Download, validate, and save image using context.

        Args:
            context: ImageSaveContext with all required parameters

        Returns:
            Saved filename
        """
        logger.debug(
            f"Saving image: {context.prompt_file_name}, model={context.model_name}, "
            f"url={context.image_url}"
        )

        image_data = self._download_image(context.image_url)
        img, format_ext = self._process_image(image_data)

        save_path = self._determine_save_path(context, format_ext)
        self._save_to_disk(img, save_path)
        logger.info(f"Successfully saved image to: {save_path}")

        if context.payload:
            self._save_payload(context, save_path)

        return str(save_path)

    def _download_image(self, image_url: str) -> bytes:
        """
        Download image from URL.

        Args:
            image_url: URL to download from

        Returns:
            Image data as bytes

        Raises:
            requests.RequestException: If download fails
        """
        response = requests.get(image_url, timeout=DEFAULT_IMAGE_DOWNLOAD_TIMEOUT)
        logger.debug(
            f"Downloaded {len(response.content)} bytes, "
            f"status={response.status_code}, "
            f"content-type={response.headers.get('content-type', 'unknown')}"
        )

        response.raise_for_status()

        content_length = len(response.content)
        logger.debug(f"Content length: {content_length} bytes")

        return response.content

    def _process_image(self, image_data: bytes) -> Tuple[Image.Image, str]:
        """
        Validate and optionally convert image.

        Args:
            image_data: Raw image bytes

        Returns:
            Tuple of (PIL Image, format extension)

        Raises:
            ValueError: If image is invalid
        """
        # Validate image
        try:
            img = Image.open(BytesIO(image_data))
            img.verify()
            # Re-open for actual processing (verify closes the file)
            img = Image.open(BytesIO(image_data))
        except Exception as e:
            raise ValueError(f"Invalid image received: {e}")

        # Determine format
        original_format = img.format.lower() if img.format else "png"

        # Convert to PNG if needed
        if self.force_png and original_format != "png":
            img, format_ext = self._convert_to_png(img, original_format)
        else:
            format_ext = original_format

        return img, format_ext

    def _convert_to_png(
        self, img: Image.Image, original_format: str
    ) -> Tuple[Image.Image, str]:
        """
        Convert image to PNG format.

        Args:
            img: PIL Image object
            original_format: Original format name

        Returns:
            Tuple of (converted Image, 'png')
        """
        logger.debug(f"Converting {original_format.upper()} to PNG")
        png_buffer = BytesIO()

        try:
            # Save to PNG format (preserves alpha if present)
            img.save(png_buffer, "PNG")

            # Reload as PNG
            png_buffer.seek(0)
            img = Image.open(png_buffer)
            logger.info(f"Converted {original_format.upper()} to PNG format")

            return img, "png"

        except Exception as e:
            logger.error(f"Failed to convert image to PNG: {e}")
            raise ValueError(f"PNG conversion failed: {e}")

    def _determine_save_path(self, context: ImageSaveContext, format_ext: str) -> Path:
        """
        Determine full save path for image.

        Args:
            context: ImageSaveContext with all parameters
            format_ext: File extension

        Returns:
            Full path for saving
        """
        # Build filename: filename-YYMMDD_HHMMSS.png format (PRD Section 04.7)
        # Get date prefix from output_dir (YYMMDD format)
        date_str = (
            context.output_dir.name
            if context.output_dir.name.isdigit() and len(context.output_dir.name) >= 6
            else datetime.now().strftime("%y%m%d")
        )
        filename = (
            f"{context.prompt_file_name}-{date_str}_{context.timestamp}.{format_ext}"
        )

        # Create nested directory structure if needed
        save_dir = context.output_dir

        if context.relative_path:
            parent_path = context.relative_path.parent
            if parent_path != Path("."):
                sanitized_path = self._sanitize_path(str(parent_path))
                save_dir = save_dir / sanitized_path
                save_dir.mkdir(parents=True, exist_ok=True)

        return save_dir / filename

    def _save_to_disk(self, img: Image.Image, save_path: Path) -> None:
        """
        Save image to disk.

        Args:
            img: PIL Image object
            save_path: Path to save to
        """
        img.save(save_path)
        logger.info(f"Saved valid image: {save_path}")

    def _save_payload(self, context: ImageSaveContext, image_path: Path) -> None:
        """
        Save API payload as Markdown file.

        Args:
            context: ImageSaveContext with payload
            image_path: Path where image was saved
        """
        payload_path = image_path.with_suffix(".md")
        payload_data = context.payload

        has_filtering_info = (
            isinstance(payload_data, dict) and "intended_request" in payload_data
        )

        if has_filtering_info:
            markdown_content = self._build_filtering_payload_markdown(
                payload_data, image_path.name, context.timestamp
            )
        else:
            markdown_content = self._build_simple_payload_markdown(
                payload_data, image_path.name, context.timestamp
            )

        with open(payload_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)

        logger.debug(f"Saved payload to {payload_path}")

    def _build_filtering_payload_markdown(
        self, payload_data: Dict[str, Any], image_name: str, timestamp: str
    ) -> str:
        """Build markdown for payload with filtering detection info."""
        intended = payload_data.get("intended_request", {})
        actual = payload_data.get("actual_request", {})
        filtering_detected = payload_data.get("api_filtering_detected", False)

        title = "API Payload Analysis"
        sections = [
            ("Parameter Filtering Status", self._filtering_status(filtering_detected)),
            ("Intended Request (What We Tried to Send)", intended),
            ("Actual Request (What Was Actually Sent)", actual),
        ]

        lines = self._build_payload_base(title, image_name, timestamp, sections)

        if filtering_detected:
            model_id = payload_data.get("model_id", "unknown")
            lines.extend([
                "",
                "## Potential Issues",
                f"- Some parameters may not be supported by the `{model_id}` model",
                "- Check model documentation for supported parameters",
                "- Consider using a different model if image inputs are required",
            ])

        return "\n".join(lines) + "\n"

    def _build_simple_payload_markdown(
        self, payload_data: Dict[str, Any], image_name: str, timestamp: str
    ) -> str:
        """Build markdown for simple payload without filtering info."""
        title = "API Payload"
        sections = [("Request Details", payload_data)]
        lines = self._build_payload_base(title, image_name, timestamp, sections)
        return "\n".join(lines) + "\n"

    def _filtering_status(self, detected: bool) -> str:
        """Build filtering status section content."""
        if detected:
            return "**API FILTERING DETECTED**\n\nThe API likely filtered out unsupported parameters. See comparison below."
        return "**No Filtering Detected**\n\nAll intended parameters appear to be supported by the model."

    def _build_payload_base(
        self,
        title: str,
        image_name: str,
        timestamp: str,
        sections: list,
    ) -> list:
        """Build common payload markdown structure."""
        lines = [
            f"# {title}",
            "",
            "## Image File",
            f"`{image_name}`",
            "",
        ]

        for section_title, content in sections:
            lines.extend([
                f"## {section_title}",
                "```json",
                json.dumps(content, indent=2, ensure_ascii=False),
                "```",
                "",
            ])

        lines.extend([
            "## Timestamp",
            f"Generated at: {timestamp}",
        ])

        return lines

    def _sanitize_path(self, path_str: str) -> str:
        """
        Sanitize path string for filesystem safety.

        Args:
            path_str: Path string to sanitize

        Returns:
            Sanitized path string
        """
        # Replace problematic characters with underscores
        problematic_chars = r"[\'()[\]{}@#&]"
        sanitized = re.sub(problematic_chars, "_", path_str)

        # Replace multiple underscores with single
        sanitized = re.sub(r"_+", "_", sanitized)

        # Remove leading/trailing underscores from each component
        parts = sanitized.split("/")
        parts = [p.strip("_") for p in parts if p]

        return "/".join(parts)

    def write_report(self, content: str, filename: str) -> None:
        """
        Write a markdown report to output directory.

        Args:
            content: Report content
            filename: Report filename
        """
        report_path = self.output_dir / filename
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(content)
        logger.info(f"Report saved: {report_path}")
