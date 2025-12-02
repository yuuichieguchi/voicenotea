"""Tests for configuration management module."""

import pytest

from src.config import ConfigError, ConfigManager


class TestConfigManagerInitialization:
    """Test ConfigManager initialization."""

    def test_should_initialize_with_default_settings(self):
        """Test creating ConfigManager with defaults."""
        config = ConfigManager(tablet_size="7inch")

        assert config.tablet_size == "7inch"
        assert config.config is not None

    def test_should_initialize_with_10inch_preset(self):
        """Test creating ConfigManager for 10-inch tablet."""
        config = ConfigManager(tablet_size="10inch")

        assert config.tablet_size == "10inch"

    def test_should_load_from_yaml_file(self, yaml_config_file):
        """Test loading configuration from YAML file."""
        config = ConfigManager(config_path=str(yaml_config_file))

        assert config.config is not None
        assert "tablet" in config.config

    def test_should_raise_config_error_on_missing_yaml_file(self):
        """Test error when YAML file doesn't exist."""
        with pytest.raises(ConfigError):
            ConfigManager(config_path="/nonexistent/config.yaml")

    def test_should_raise_config_error_on_invalid_yaml(self, tmp_path):
        """Test error when YAML is malformed."""
        bad_yaml = tmp_path / "bad.yaml"
        bad_yaml.write_text("invalid: yaml: content: {")

        with pytest.raises(ConfigError):
            ConfigManager(config_path=str(bad_yaml))


class TestConfigManagerPresets:
    """Test tablet preset retrieval."""

    def test_should_get_7inch_preset(self):
        """Test getting 7-inch tablet preset."""
        config = ConfigManager(tablet_size="7inch")
        preset = config.get_tablet_preset()

        assert preset["width"] == 1080
        assert preset["height"] == 1920
        assert preset["dpi"] == 326

    def test_should_get_10inch_preset(self):
        """Test getting 10-inch tablet preset."""
        config = ConfigManager(tablet_size="10inch")
        preset = config.get_tablet_preset()

        assert preset["width"] == 1080
        assert preset["height"] == 1920
        assert preset["dpi"] == 216

    def test_should_override_tablet_size_in_get_preset(self):
        """Test overriding tablet size in get_tablet_preset."""
        config = ConfigManager(tablet_size="7inch")
        preset_10 = config.get_tablet_preset(tablet_size="10inch")

        assert preset_10["dpi"] == 216

    def test_should_raise_error_on_invalid_tablet_size(self):
        """Test error with invalid tablet size."""
        config = ConfigManager()

        with pytest.raises(ConfigError):
            config.get_tablet_preset(tablet_size="15inch")


class TestConfigManagerProcessing:
    """Test processing configuration."""

    def test_should_get_processing_config_with_defaults(self):
        """Test getting default processing configuration."""
        config = ConfigManager()
        processing = config.get_processing_config()

        assert processing["jpeg_quality"] == 95
        assert processing["background_color"] == [0, 0, 0]
        assert processing["size_threshold_mb"] == 8.0

    def test_should_get_logging_config(self):
        """Test getting logging configuration."""
        config = ConfigManager()
        logging_config = config.get_logging_config()

        assert "level" in logging_config

    def test_should_get_paths_from_config(self, yaml_config_file):
        """Test getting paths from loaded configuration."""
        config = ConfigManager(config_path=str(yaml_config_file))

        input_dir = config.get_input_dir()
        output_dir = config.get_output_dir()

        assert input_dir is not None
        assert output_dir is not None


class TestConfigManagerValidation:
    """Test configuration validation."""

    def test_should_validate_correct_config(self):
        """Test validation of correct configuration."""
        config = ConfigManager(tablet_size="7inch")

        assert config.validate_config() is True

    def test_should_raise_error_on_invalid_jpeg_quality(self):
        """Test validation error for invalid JPEG quality."""
        config = ConfigManager()
        config.config["processing"]["jpeg_quality"] = 150

        with pytest.raises(ConfigError):
            config.validate_config()

    def test_should_raise_error_on_invalid_size_threshold(self):
        """Test validation error for invalid size threshold."""
        config = ConfigManager()
        config.config["processing"]["size_threshold_mb"] = -5

        with pytest.raises(ConfigError):
            config.validate_config()

    def test_should_raise_error_on_invalid_tablet_size_in_config(self):
        """Test validation error for invalid tablet size."""
        config = ConfigManager()
        config.config["tablet"]["size"] = "15inch"

        with pytest.raises(ConfigError):
            config.validate_config()


class TestConfigManagerExport:
    """Test configuration export."""

    def test_should_export_to_dict(self):
        """Test exporting configuration to dictionary."""
        config = ConfigManager(tablet_size="7inch")
        config_dict = config.to_dict()

        assert isinstance(config_dict, dict)
        assert "tablet" in config_dict

    def test_should_export_to_json(self):
        """Test exporting configuration to JSON string."""
        config = ConfigManager(tablet_size="7inch")
        json_str = config.to_json()

        assert isinstance(json_str, str)
        assert "tablet" in json_str

    def test_should_not_modify_original_on_export(self):
        """Test that exported dict doesn't affect original."""
        config = ConfigManager(tablet_size="7inch")
        exported = config.to_dict()
        exported["tablet"]["size"] = "10inch"

        assert config.tablet_size == "7inch"
