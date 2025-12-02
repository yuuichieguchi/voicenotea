"""Tests for screenshot generator orchestration."""

import pytest

from src.generator import ScreenshotGenerator
from src.logger import ProcessingError, setup_logger
from src.models import ProcessingResult, TabletPreset


class TestGeneratorInitialization:
    """Test ScreenshotGenerator initialization."""

    def test_should_initialize_with_config(self, sample_config):
        """Test initializing generator with config."""
        generator = ScreenshotGenerator(sample_config)

        assert generator.config == sample_config
        assert generator.logger is not None

    def test_should_initialize_with_custom_logger(self, sample_config, mock_logger):
        """Test initializing with custom logger."""
        generator = ScreenshotGenerator(sample_config, logger=mock_logger)

        assert generator.logger == mock_logger


class TestGeneratorValidation:
    """Test setup validation."""

    def test_should_validate_correct_setup(self, sample_config):
        """Test validation of correct setup."""
        generator = ScreenshotGenerator(sample_config)

        assert generator.validate_setup() is True

    def test_should_raise_error_on_missing_input_dir(self, sample_config):
        """Test error when input dir not configured."""
        sample_config["paths"] = {"output_dir": "output"}
        generator = ScreenshotGenerator(sample_config)

        with pytest.raises(ProcessingError):
            generator.validate_setup()

    def test_should_raise_error_on_missing_output_dir(self, sample_config):
        """Test error when output dir not configured."""
        sample_config["paths"] = {"input_dir": "input"}
        generator = ScreenshotGenerator(sample_config)

        with pytest.raises(ProcessingError):
            generator.validate_setup()


class TestGeneratorTabletPreset:
    """Test getting tablet preset from config."""

    def test_should_get_7inch_preset(self, sample_config):
        """Test getting 7-inch preset."""
        sample_config["tablet"]["size"] = "7inch"
        generator = ScreenshotGenerator(sample_config)

        preset = generator.get_tablet_preset()

        assert isinstance(preset, TabletPreset)
        assert preset.width == 1080
        assert preset.height == 1920

    def test_should_get_10inch_preset(self, sample_config):
        """Test getting 10-inch preset."""
        sample_config["tablet"]["size"] = "10inch"
        generator = ScreenshotGenerator(sample_config)

        preset = generator.get_tablet_preset()

        assert isinstance(preset, TabletPreset)
        assert preset.dpi == 216

    def test_should_raise_error_on_unknown_tablet_size(self, sample_config):
        """Test error on unknown tablet size."""
        sample_config["tablet"]["size"] = "15inch"
        generator = ScreenshotGenerator(sample_config)

        with pytest.raises(ProcessingError):
            generator.get_tablet_preset()


class TestGeneratorProcessing:
    """Test screenshot processing."""

    def test_should_process_single_image(self, sample_config, sample_portrait_image, tmp_path):
        """Test processing single image."""
        sample_config["paths"]["input_dir"] = str(sample_portrait_image.parent)
        sample_config["paths"]["output_dir"] = str(tmp_path)

        generator = ScreenshotGenerator(sample_config)
        result = generator.process_image(str(sample_portrait_image))

        assert isinstance(result, ProcessingResult)

    def test_should_handle_missing_input_file(self, sample_config, tmp_path):
        """Test handling missing input file."""
        sample_config["paths"]["input_dir"] = str(tmp_path)
        sample_config["paths"]["output_dir"] = str(tmp_path)

        generator = ScreenshotGenerator(sample_config)
        result = generator.process_image("/nonexistent/file.jpg")

        assert isinstance(result, ProcessingResult)


class TestGeneratorBatchProcessing:
    """Test batch directory processing."""

    def test_should_process_directory(self, sample_config, tmp_project_dir, sample_portrait_image):
        """Test processing directory of images."""
        sample_config["paths"]["input_dir"] = str(tmp_project_dir["input"])
        sample_config["paths"]["output_dir"] = str(tmp_project_dir["output"])

        generator = ScreenshotGenerator(sample_config)
        results = generator.process_directory(str(tmp_project_dir["input"]))

        assert isinstance(results, list)
        assert all(isinstance(r, ProcessingResult) for r in results)

    def test_should_handle_empty_directory(self, sample_config, tmp_project_dir):
        """Test handling empty directory."""
        sample_config["paths"]["input_dir"] = str(tmp_project_dir["input"])
        sample_config["paths"]["output_dir"] = str(tmp_project_dir["output"])

        generator = ScreenshotGenerator(sample_config)
        results = generator.process_directory(str(tmp_project_dir["input"]))

        assert isinstance(results, list)


class TestGeneratorStatistics:
    """Test processing statistics."""

    def test_should_get_processing_stats(self, sample_config, tmp_project_dir):
        """Test getting processing statistics."""
        sample_config["paths"]["input_dir"] = str(tmp_project_dir["input"])
        sample_config["paths"]["output_dir"] = str(tmp_project_dir["output"])

        generator = ScreenshotGenerator(sample_config)
        generator.results = [
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
                error="File not found",
            ),
        ]

        stats = generator.get_processing_stats()

        assert stats["total"] == 2
        assert stats["success"] == 1
        assert stats["failed"] == 1

    def test_should_return_zero_stats_for_empty_results(self, sample_config):
        """Test stats for empty results."""
        generator = ScreenshotGenerator(sample_config)
        generator.results = []

        stats = generator.get_processing_stats()

        assert stats["total"] == 0
        assert stats["success"] == 0
        assert stats["failed"] == 0


class TestGeneratorSummary:
    """Test summary reporting."""

    def test_should_return_zero_exit_code_on_success(self, sample_config):
        """Test exit code 0 on success."""
        generator = ScreenshotGenerator(sample_config)
        generator.results = [
            ProcessingResult(
                input_file="test1.jpg",
                output_file="test1_out.jpg",
                success=True,
                file_size_mb=0.5,
                scaled_dimensions=(920, 1920),
            ),
        ]

        exit_code = generator.print_summary()

        assert exit_code == 0

    def test_should_return_one_exit_code_on_failure(self, sample_config):
        """Test exit code 1 on failure."""
        generator = ScreenshotGenerator(sample_config)
        generator.results = [
            ProcessingResult(
                input_file="test1.jpg",
                output_file="test1_out.jpg",
                success=False,
                error="Processing failed",
            ),
        ]

        exit_code = generator.print_summary()

        assert exit_code == 1
