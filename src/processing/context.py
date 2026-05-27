"""Processing context dataclasses for encapsulating parameters."""

from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Any, List, Optional


@dataclass
class ProcessingContext:
    """Encapsulates all parameters needed for processing a single file."""

    prompt_file: Path
    relative_path: Path
    prompts: List[str]
    model_id: str
    params: Dict[str, Any]  # All profile parameters passed through unchanged
    pricing: Dict[str, Any]
    profile_name: str
    output_dir: Path
    prompt_prefix: str = ""
    prompt_suffix: str = ""
    delay_between_requests: float = 0


@dataclass
class ProcessorConfig:
    """Configuration for FileProcessor initialization."""

    api_client: Any  # ReplicateClient
    output_writer: Any  # OutputWriter
    reporter: Any  # Reporter
    save_payloads: bool = True
    dry_run: bool = False
    no_progress: bool = False
