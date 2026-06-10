"""Replicate API client wrapper with sequential processing."""

import os
import time
import json
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
from loguru import logger
import replicate
from ..auth import get_api_key
from ..constants import (
    DEFAULT_TIMEOUT,
    DEFAULT_MAX_RETRIES,
    DEFAULT_MAX_WAIT_TIME,
    DEFAULT_RATE_LIMIT_RETRY_DELAY,
)


class ReplicateClient:
    """Wrapper for Replicate with sequential processing and error handling."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        max_retries: int = DEFAULT_MAX_RETRIES,
        max_wait_time: int = DEFAULT_MAX_WAIT_TIME,
        rate_limit_retry_delay: int = DEFAULT_RATE_LIMIT_RETRY_DELAY,
    ):
        """
        Initialize Replicate client.

        Args:
            api_key: Replicate API token (optional, will use env var if not provided)
            timeout: Request timeout in seconds
            max_retries: Number of retry attempts
            max_wait_time: Max time to wait for predictions
            rate_limit_retry_delay: Delay when rate limited
        """
        # Use provided key or get from environment
        if api_key:
            self.api_key = api_key
        else:
            self.api_key = get_api_key()

        self.timeout = timeout
        self.max_retries = max_retries
        self.max_wait_time = max_wait_time
        self.rate_limit_retry_delay = rate_limit_retry_delay

        # Set API token in environment for replicate
        os.environ["REPLICATE_API_TOKEN"] = self.api_key

    def generate_image(
        self, model_id: str, prompt: str, params: Dict[str, Any], debug: bool = False
    ) -> Dict[str, Any]:
        """
        Generate an image using Replicate API with pure parameter pass-through.

        Args:
            model_id: Replicate model identifier
            prompt: Text prompt
            params: All model parameters from profile (passed through unchanged)
            debug: Save debug information

        Returns:
            API response dictionary

        Raises:
            Exception: On API failure after retries
        """
        payload = self._build_payload(prompt, params)

        if debug:
            self._save_debug_request(model_id, payload)

        result, actual_payload = self._call_with_retry(model_id, payload, debug)

        intended_payload = self._build_tracking_info(model_id, payload, actual_payload)

        return {"result": result, "payload": intended_payload}

    def _build_payload(self, prompt: str, params: Dict[str, Any]) -> Dict[str, Any]:
        """Build request payload with cleaned prompt."""
        clean_prompt = prompt.replace('\\"', '"')
        payload = {**params, "prompt": clean_prompt}

        logger.debug(
            f"Payload: {json.dumps(payload, indent=2)}, prompt: {clean_prompt}"
        )

        return payload

    def _build_tracking_info(
        self, model_id: str, payload: Dict[str, Any], actual_payload: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Build payload tracking information."""
        return {
            "model_id": model_id,
            "timestamp": datetime.now().isoformat(),
            "intended_request": payload.copy(),
            "actual_request": actual_payload,
            "api_filtering_detected": False,
        }

    def _call_with_retry(
        self, model_id: str, payload: Dict[str, Any], debug: bool
    ) -> tuple[Dict[str, Any], Dict[str, Any]]:
        """
        Call Replicate API with retry logic.

        Args:
            model_id: Model identifier
            payload: Request payload
            debug: Save debug information

        Returns:
            Tuple of (API response, actual payload sent)

        Raises:
            Exception: After all retries exhausted
        """
        last_error = None

        for attempt in range(1, self.max_retries + 1):
            try:
                logger.debug(
                    f"API call attempt {attempt}/{self.max_retries}, "
                    f"model={model_id}, input_keys={list(payload.keys())}"
                )

                # Use replicate.run for synchronous execution
                output = replicate.run(model_id, input=payload)

                logger.debug(f"API call successful, output type: {type(output)}")

                # Convert output to consistent format
                result = self._format_output(output)

                # Save debug response if needed
                if debug:
                    self._save_debug_response(model_id, result)

                # Return both result and actual payload that was sent
                return result, payload

            except Exception as e:
                last_error = e

                # Check if it's a rate limit error
                if "429" in str(e) or "rate" in str(e).lower():
                    logger.warning(
                        f"Rate limited, waiting {self.rate_limit_retry_delay}s..."
                    )
                    time.sleep(self.rate_limit_retry_delay)
                    continue

                # Other errors
                logger.error(f"Error on attempt {attempt}: {e}")

                if attempt < self.max_retries:
                    wait_time = 2**attempt  # Exponential backoff
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    raise

        # All retries exhausted
        raise Exception(f"Failed after {self.max_retries} attempts: {last_error}")

    def _format_output(self, output: Any) -> Dict[str, Any]:
        """
        Format Replicate output to consistent structure.

        Args:
            output: Raw output from Replicate

        Returns:
            Formatted output dictionary
        """
        # Handle different output formats from Replicate
        if isinstance(output, list):
            # Multiple outputs or single output in list
            images = []
            for item in output:
                if hasattr(item, "read"):
                    # FileOutput object
                    images.append({"url": str(item)})
                else:
                    # URL string
                    images.append({"url": str(item)})
            return {"images": images}
        elif hasattr(output, "read"):
            # Single FileOutput object
            return {"images": [{"url": str(output)}]}
        else:
            # Single URL or other format
            return {"images": [{"url": str(output)}]}

    def _save_debug_file(
        self, prefix: str, model_id: str, data: Dict[str, Any]
    ) -> None:
        """Save debug data to JSON file."""
        debug_dir = Path("debug")
        debug_dir.mkdir(exist_ok=True)

        timestamp = time.strftime("%Y%m%d_%H%M%S")
        safe_model_id = model_id.replace("/", "_").replace(":", "_")
        filename = debug_dir / f"{prefix}_{timestamp}_{safe_model_id}.json"

        with open(filename, "w") as f:
            json.dump(data, f, indent=2)

        logger.debug(f"Saved debug {prefix} to {filename}")

    def _save_debug_request(self, model_id: str, payload: Dict[str, Any]) -> None:
        """Save debug request to file."""
        self._save_debug_file(
            "request",
            model_id,
            {"model_id": model_id, "payload": payload, "timestamp": time.strftime("%Y%m%d_%H%M%S")},
        )

    def _save_debug_response(self, model_id: str, response: Dict[str, Any]) -> None:
        """Save debug response to file."""
        self._save_debug_file(
            "response",
            model_id,
            {"model_id": model_id, "response": response, "timestamp": time.strftime("%Y%m%d_%H%M%S")},
        )


