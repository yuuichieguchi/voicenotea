"""Tests for CLI main module."""

import sys
from unittest.mock import MagicMock, patch

import pytest

from src.config import ConfigError
from src.logger import PathError, ProcessingError
from src.main import main, merge_configs, parse_arguments
from src.models import ProcessingResult


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
        with patch.object(sys, 'argv', ['prog', '--input', '/tmp/input', '--output', '/tmp/output']):
            with patch('src.main.ConfigManager') as mock_config_mgr:
                with patch('src.main.ScreenshotGenerator') as mock_gen:
                    # Setup ConfigManager mock
                    mock_config = MagicMock()
                    mock_config.validate_config.return_value = None
                    mock_config.to_dict.return_value = {
                        'tablet': {'size': '7inch'},
                        'paths': {'input_dir': '/tmp/input', 'output_dir': '/tmp/output'},
                        'processing': {'jpeg_quality': 95},
                        'logging': {'level': 'INFO'}
                    }
                    mock_config_mgr.return_value = mock_config

                    # Setup ScreenshotGenerator mock
                    mock_instance = MagicMock()
                    mock_instance.validate_setup.return_value = True
                    mock_instance.process_directory.return_value = [
                        ProcessingResult(
                            input_file="test.jpg",
                            output_file="test_out.jpg",
                            success=True,
                            file_size_mb=0.5,
                            scaled_dimensions=(920, 1920),
                        )
                    ]
                    mock_instance.print_summary.return_value = 0
                    mock_gen.return_value = mock_instance

                    # ACT
                    result = main()

                    # ASSERT
                    assert result == 0
                    mock_instance.validate_setup.assert_called_once()
                    mock_instance.process_directory.assert_called_once()
                    mock_instance.print_summary.assert_called_once()

    def test_should_return_one_on_partial_failure(self):
        """Test main returns 1 when some images fail."""
        with patch.object(sys, 'argv', ['prog', '--input', '/tmp/input', '--output', '/tmp/output']):
            with patch('src.main.ConfigManager') as mock_config_mgr:
                with patch('src.main.ScreenshotGenerator') as mock_gen:
                    # Setup ConfigManager mock
                    mock_config = MagicMock()
                    mock_config.validate_config.return_value = None
                    mock_config.to_dict.return_value = {
                        'tablet': {'size': '7inch'},
                        'paths': {'input_dir': '/tmp/input', 'output_dir': '/tmp/output'},
                        'processing': {'jpeg_quality': 95},
                        'logging': {'level': 'INFO'}
                    }
                    mock_config_mgr.return_value = mock_config

                    # Setup ScreenshotGenerator mock with one failure
                    mock_instance = MagicMock()
                    mock_instance.validate_setup.return_value = True
                    mock_instance.process_directory.return_value = [
                        ProcessingResult(
                            input_file="test1.jpg",
                            output_file="test1_out.jpg",
                            success=True,
                            file_size_mb=0.5,
                            scaled_dimensions=(920, 1920),
                        ),
                        ProcessingResult(
                            input_file="test2.jpg",
                            output_file="test2_out.jpg",
                            success=False,
                            error="File corrupted",
                        )
                    ]
                    mock_instance.print_summary.return_value = 1
                    mock_gen.return_value = mock_instance

                    # ACT
                    result = main()

                    # ASSERT
                    assert result == 1

    def test_should_catch_config_error(self):
        """Test catching configuration errors."""
        with patch.object(sys, 'argv', ['prog', '--input', '/tmp/input', '--output', '/tmp/output']):
            with patch('src.main.ConfigManager') as mock_config_mgr:
                # Setup ConfigManager to raise ConfigError during initialization
                mock_config_mgr.side_effect = ConfigError("Invalid configuration")

                # ACT
                result = main()

                # ASSERT
                assert result == 1  # ConfigError exit code

    def test_should_catch_path_error(self):
        """Test catching path-related errors."""
        with patch.object(sys, 'argv', ['prog', '--input', '/tmp/input', '--output', '/tmp/output']):
            with patch('src.main.ConfigManager') as mock_config_mgr:
                with patch('src.main.ScreenshotGenerator') as mock_gen:
                    # Setup ConfigManager mock
                    mock_config = MagicMock()
                    mock_config.validate_config.return_value = None
                    mock_config.to_dict.return_value = {
                        'tablet': {'size': '7inch'},
                        'paths': {'input_dir': '/nonexistent', 'output_dir': '/tmp/output'},
                        'processing': {'jpeg_quality': 95},
                        'logging': {'level': 'INFO'}
                    }
                    mock_config_mgr.return_value = mock_config

                    # Setup ScreenshotGenerator to raise PathError
                    mock_gen.return_value.validate_setup.side_effect = PathError(
                        "Input directory not found"
                    )

                    # ACT
                    result = main()

                    # ASSERT
                    assert result == 2  # PathError exit code

    def test_should_catch_processing_error(self):
        """Test catching processing errors."""
        with patch.object(sys, 'argv', ['prog', '--input', '/tmp/input', '--output', '/tmp/output']):
            with patch('src.main.ConfigManager') as mock_config_mgr:
                with patch('src.main.ScreenshotGenerator') as mock_gen:
                    # Setup ConfigManager mock
                    mock_config = MagicMock()
                    mock_config.validate_config.return_value = None
                    mock_config.to_dict.return_value = {
                        'tablet': {'size': '7inch'},
                        'paths': {'input_dir': '/tmp/input', 'output_dir': '/tmp/output'},
                        'processing': {'jpeg_quality': 95},
                        'logging': {'level': 'INFO'}
                    }
                    mock_config_mgr.return_value = mock_config

                    # Setup ScreenshotGenerator to raise ProcessingError
                    mock_gen.return_value.validate_setup.return_value = True
                    mock_gen.return_value.process_directory.side_effect = ProcessingError(
                        "Image processing failed"
                    )

                    # ACT
                    result = main()

                    # ASSERT
                    assert result == 3  # ProcessingError exit code
