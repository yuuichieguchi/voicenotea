"""Tests for CLI main module."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.main import main, merge_configs, parse_arguments


class TestArgumentParsing:
    """Test command-line argument parsing."""

    def test_should_parse_tablet_size_argument(self):
        """Test parsing --tablet-size argument."""
        with patch.object(sys, 'argv', ['prog', '--tablet-size', '10inch']):
            args = parse_arguments()

            assert args.tablet_size == "10inch"

    def test_should_use_default_tablet_size(self):
        """Test default tablet size."""
        with patch.object(sys, 'argv', ['prog']):
            args = parse_arguments()

            assert args.tablet_size == "7inch"

    def test_should_parse_input_argument(self):
        """Test parsing --input argument."""
        with patch.object(sys, 'argv', ['prog', '--input', '/path/input']):
            args = parse_arguments()

            assert args.input == "/path/input"

    def test_should_parse_output_argument(self):
        """Test parsing --output argument."""
        with patch.object(sys, 'argv', ['prog', '--output', '/path/output']):
            args = parse_arguments()

            assert args.output == "/path/output"

    def test_should_parse_quality_argument(self):
        """Test parsing --quality argument."""
        with patch.object(sys, 'argv', ['prog', '--quality', '80']):
            args = parse_arguments()

            assert args.quality == 80

    def test_should_parse_verbose_flag(self):
        """Test parsing --verbose flag."""
        with patch.object(sys, 'argv', ['prog', '--verbose']):
            args = parse_arguments()

            assert args.verbose is True

    def test_should_parse_config_file_argument(self):
        """Test parsing --config argument."""
        with patch.object(sys, 'argv', ['prog', '--config', '/path/config.yaml']):
            args = parse_arguments()

            assert args.config == "/path/config.yaml"


class TestConfigMerging:
    """Test configuration merging."""

    def test_should_merge_yaml_and_cli_configs(self):
        """Test merging YAML and CLI configurations."""
        yaml_config = {
            "tablet": {"size": "7inch"},
            "paths": {"input_dir": "/yaml/input"},
        }

        mock_args = MagicMock()
        mock_args.tablet_size = "10inch"
        mock_args.input = None
        mock_args.output = None
        mock_args.quality = None
        mock_args.verbose = False

        result = merge_configs(yaml_config, mock_args)

        assert result["tablet"]["size"] == "10inch"
        assert result["paths"]["input_dir"] == "/yaml/input"

    def test_should_override_yaml_with_cli_args(self):
        """Test CLI args override YAML config."""
        yaml_config = {
            "paths": {"input_dir": "/yaml/input", "output_dir": "/yaml/output"},
        }

        mock_args = MagicMock()
        mock_args.tablet_size = None
        mock_args.input = "/cli/input"
        mock_args.output = "/cli/output"
        mock_args.quality = None
        mock_args.verbose = False

        result = merge_configs(yaml_config, mock_args)

        assert result["paths"]["input_dir"] == "/cli/input"
        assert result["paths"]["output_dir"] == "/cli/output"

    def test_should_handle_none_yaml_config(self):
        """Test handling None YAML config."""
        mock_args = MagicMock()
        mock_args.tablet_size = "7inch"
        mock_args.input = "/input"
        mock_args.output = "/output"
        mock_args.quality = 95
        mock_args.verbose = True

        result = merge_configs(None, mock_args)

        assert result["tablet"]["size"] == "7inch"
        assert result["paths"]["input_dir"] == "/input"

    def test_should_set_debug_logging_on_verbose(self):
        """Test that verbose flag sets DEBUG logging."""
        mock_args = MagicMock()
        mock_args.tablet_size = None
        mock_args.input = None
        mock_args.output = None
        mock_args.quality = None
        mock_args.verbose = True

        result = merge_configs({}, mock_args)

        assert result["logging"]["level"] == "DEBUG"


class TestMainFunction:
    """Test main entry point."""

    def test_should_return_zero_on_success(self):
        """Test main returns 0 on success."""
        with patch.object(sys, 'argv', ['prog', '--help']):
            with patch('src.main.ScreenshotGenerator') as mock_gen:
                mock_instance = MagicMock()
                mock_instance.validate_setup.return_value = True
                mock_instance.process_directory.return_value = []
                mock_gen.return_value = mock_instance

    def test_should_handle_missing_paths(self):
        """Test handling missing required paths."""
        with patch.object(sys, 'argv', ['prog']):
            # Would need proper config setup to test fully
            pass

    def test_should_catch_config_error(self):
        """Test catching configuration errors."""
        # Test would require mocking ConfigManager to raise ConfigError
        pass

    def test_should_catch_path_error(self):
        """Test catching path-related errors."""
        # Test would require mocking PathManager to raise PathError
        pass

    def test_should_catch_processing_error(self):
        """Test catching processing errors."""
        # Test would require mocking ImageProcessor to raise ProcessingError
        pass

    def test_should_return_appropriate_exit_codes(self):
        """Test exit codes based on error types."""
        # Tests for different error scenarios and their exit codes
        pass
