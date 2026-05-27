"""Configuration loading for Replicate wrapper."""

import yaml
from pathlib import Path
from typing import Dict, Any, List
from loguru import logger

from ..processing.discovery import InputDiscovery


class ConfigLoader:
    """Load and manage configuration files."""

    def __init__(self, config_dir: Path | None = None):
        """
        Initialize config loader.

        Args:
            config_dir: Directory containing config files, defaults to USER-FILES/01.CONFIG
        """
        if config_dir is None:
            config_dir = Path("USER-FILES/01.CONFIG")
        self.config_dir = Path(config_dir)
        self.config: Dict[str, Any] = {}

    def load_config(self) -> Dict[str, Any]:
        """
        Load main configuration from config.yaml.

        Returns:
            Configuration dictionary

        Raises:
            FileNotFoundError: If config.yaml not found
            yaml.YAMLError: If config is invalid
        """
        config_path = self.config_dir / "config.yaml"

        if not config_path.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")

        try:
            with open(config_path, "r") as f:
                self.config = yaml.safe_load(f) or {}
            logger.info(f"Loaded configuration from {config_path}")
            return self.config
        except yaml.YAMLError as e:
            raise yaml.YAMLError(f"Invalid YAML in {config_path}: {e}")

    def _create_discovery(self) -> InputDiscovery:
        """Create InputDiscovery with standard paths."""
        return InputDiscovery(
            Path("USER-FILES/04.INPUT"), Path("USER-FILES/03.PROFILES")
        )

    def load_profiles(self) -> Dict[str, Dict[str, Any]]:
        """
        Load all raw profiles.

        Returns:
            Dictionary of profile contents
        """
        return self._create_discovery().discover_profiles()

    def load_active_profiles(self) -> List[Dict[str, Any]]:
        """
        Load and return active profiles using InputDiscovery.

        Returns:
            List of profile dictionaries
        """
        discovery = self._create_discovery()
        profiles = discovery.discover_profiles()
        return discovery.get_all_models(profiles)
