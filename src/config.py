"""Configuration management for tablet screenshot generation."""

import json
from pathlib import Path
from typing import Any, Dict, Optional

try:
    import yaml
except ImportError:
    yaml = None


class ConfigError(Exception):
    """Configuration loading or validation error."""

    exit_code = 1


class ConfigManager:
    """Manage configuration from YAML, environment variables, or defaults.

    Handles loading and validation of tablet screenshot generation configuration
    with support for multiple sources with proper precedence.

    Examples:
        >>> config = ConfigManager(tablet_size="7inch")
        >>> preset = config.get_tablet_preset()
        {'width': 1080, 'height': 1920, 'dpi': 326}
    """

    DEFAULT_PRESETS: Dict[str, Dict[str, int]] = {
        "7inch": {"width": 1080, "height": 1920, "dpi": 326},
        "10inch": {"width": 1080, "height": 1920, "dpi": 216},
    }

    def __init__(
        self,
        config_path: Optional[str] = None,
        tablet_size: str = "7inch",
    ) -> None:
        """Initialize ConfigManager.

        Args:
            config_path: Path to YAML configuration file. Optional.
            tablet_size: Tablet size preset ("7inch" or "10inch"). Default: "7inch".

        Raises:
            ConfigError: If config_path is provided but file doesn't exist or is invalid.
        """
        self.config_path = config_path
        self.tablet_size = tablet_size
        self.config: Dict[str, Any] = {}

        if config_path:
            self._load_from_yaml(config_path)
        else:
            self._load_defaults()

    def _load_from_yaml(self, config_path: str) -> None:
        """Load configuration from YAML file.

        Args:
            config_path: Path to YAML configuration file.

        Raises:
            ConfigError: If file not found or YAML parsing fails.
        """
        if yaml is None:
            raise ConfigError(
                "PyYAML is required to load YAML config. Install: pip install pyyaml"
            )

        path = Path(config_path)
        if not path.exists():
            raise ConfigError(f"Configuration file not found: {config_path}")

        try:
            with open(path, "r", encoding="utf-8") as f:
                self.config = yaml.safe_load(f) or {}
        except yaml.YAMLError as e:
            raise ConfigError(f"Failed to parse YAML configuration: {e}")
        except IOError as e:
            raise ConfigError(f"Failed to read configuration file: {e}")

    def _load_defaults(self) -> None:
        """Load default configuration values."""
        self.config = {
            "tablet": {"size": self.tablet_size},
            "processing": {
                "jpeg_quality": 95,
                "background_color": [0, 0, 0],
                "size_threshold_mb": 8.0,
            },
            "logging": {"level": "INFO"},
        }

    def get_tablet_preset(self, tablet_size: Optional[str] = None) -> Dict[str, int]:
        """Get tablet preset dimensions.

        Args:
            tablet_size: Tablet size ("7inch" or "10inch"). If None, uses configured size.

        Returns:
            Dictionary with width, height, and dpi keys.

        Raises:
            ConfigError: If tablet size is invalid.

        Examples:
            >>> config = ConfigManager(tablet_size="7inch")
            >>> config.get_tablet_preset()
            {'width': 1080, 'height': 1920, 'dpi': 326}
        """
        size = tablet_size or self.tablet_size

        if size not in self.DEFAULT_PRESETS:
            raise ConfigError(f"Invalid tablet size: {size}. Must be '7inch' or '10inch'")

        return self.DEFAULT_PRESETS[size]

    def get_processing_config(self) -> Dict[str, Any]:
        """Get processing configuration.

        Returns:
            Dictionary with jpeg_quality, background_color, size_threshold_mb.
        """
        return self.config.get("processing", {
            "jpeg_quality": 95,
            "background_color": [0, 0, 0],
            "size_threshold_mb": 8.0,
        })

    def get_logging_config(self) -> Dict[str, Any]:
        """Get logging configuration.

        Returns:
            Dictionary with logging level and optional file path.
        """
        return self.config.get("logging", {"level": "INFO"})

    def get_input_dir(self) -> Optional[str]:
        """Get configured input directory.

        Returns:
            Input directory path or None if not configured.
        """
        return self.config.get("paths", {}).get("input_dir")

    def get_output_dir(self) -> Optional[str]:
        """Get configured output directory.

        Returns:
            Output directory path or None if not configured.
        """
        return self.config.get("paths", {}).get("output_dir")

    def validate_config(self) -> bool:
        """Validate configuration values.

        Returns:
            True if configuration is valid.

        Raises:
            ConfigError: If any configuration value is invalid.
        """
        # Validate tablet size
        tablet_size = self.config.get("tablet", {}).get("size", self.tablet_size)
        if tablet_size not in self.DEFAULT_PRESETS:
            raise ConfigError(f"Invalid tablet size in config: {tablet_size}")

        # Validate processing config
        processing = self.get_processing_config()
        jpeg_quality = processing.get("jpeg_quality", 95)
        if not (1 <= jpeg_quality <= 100):
            raise ConfigError(f"JPEG quality must be 1-100, got {jpeg_quality}")

        size_threshold = processing.get("size_threshold_mb", 8.0)
        if size_threshold <= 0:
            raise ConfigError(f"Size threshold must be positive, got {size_threshold}")

        return True

    def to_dict(self) -> Dict[str, Any]:
        """Export configuration as dictionary.

        Returns:
            Full configuration dictionary.
        """
        return self.config.copy()

    def to_json(self) -> str:
        """Export configuration as JSON string.

        Returns:
            JSON representation of configuration.
        """
        return json.dumps(self.config, indent=2)
