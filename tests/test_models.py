"""Tests for data models module."""

import pytest

from src.logger import ProcessingError
from src.models import (
    ImageDimensions,
    ProcessingResult,
    ScreenshotConfig,
    TabletPreset,
)


class TestTabletPreset:
    """Test TabletPreset data model."""

    def test_should_create_valid_tablet_preset(self):
        """Test creating valid tablet preset."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)

        assert tablet.size == "7inch"
        assert tablet.width == 1080
        assert tablet.height == 1920

    def test_should_calculate_aspect_ratio(self):
        """Test aspect ratio calculation."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)

        assert tablet.aspect_ratio == pytest.approx(1080 / 1920, rel=1e-6)

    def test_should_generate_resolution_string(self):
        """Test resolution string formatting."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)

        assert tablet.resolution_str == "1080x1920"

    def test_should_raise_error_on_negative_width(self):
        """Test error on negative width."""
        with pytest.raises(ProcessingError):
            TabletPreset(size="7inch", width=-100, height=1920, dpi=326)

    def test_should_raise_error_on_zero_height(self):
        """Test error on zero height."""
        with pytest.raises(ProcessingError):
            TabletPreset(size="7inch", width=1080, height=0, dpi=326)

    def test_should_raise_error_on_invalid_dpi(self):
        """Test error on invalid DPI."""
        with pytest.raises(ProcessingError):
            TabletPreset(size="7inch", width=1080, height=1920, dpi=-1)

    def test_should_raise_error_on_invalid_size_string(self):
        """Test error on invalid tablet size."""
        with pytest.raises(ProcessingError):
            TabletPreset(size="15inch", width=1080, height=1920, dpi=200)


class TestImageDimensions:
    """Test ImageDimensions data model."""

    def test_should_create_valid_image_dimensions(self):
        """Test creating valid image dimensions."""
        dims = ImageDimensions(width=1080, height=1920)

        assert dims.width == 1080
        assert dims.height == 1920

    def test_should_calculate_aspect_ratio(self):
        """Test aspect ratio calculation."""
        dims = ImageDimensions(width=1080, height=1920)

        assert dims.aspect_ratio == pytest.approx(1080 / 1920, rel=1e-6)

    def test_should_identify_portrait_orientation(self):
        """Test portrait orientation detection."""
        dims = ImageDimensions(width=1080, height=1920)

        assert dims.is_portrait is True
        assert dims.is_landscape is False

    def test_should_identify_landscape_orientation(self):
        """Test landscape orientation detection."""
        dims = ImageDimensions(width=1920, height=1080)

        assert dims.is_portrait is False
        assert dims.is_landscape is True

    def test_should_raise_error_on_zero_width(self):
        """Test error on zero width."""
        with pytest.raises(ProcessingError):
            ImageDimensions(width=0, height=1920)

    def test_should_raise_error_on_negative_height(self):
        """Test error on negative height."""
        with pytest.raises(ProcessingError):
            ImageDimensions(width=1080, height=-100)

    def test_should_scale_to_fit_maintaining_aspect_ratio(self):
        """Test scaling to fit within bounds."""
        dims = ImageDimensions(width=1080, height=1920)

        scaled = dims.scale_to_fit(max_width=1080, max_height=1920)

        assert scaled.aspect_ratio == pytest.approx(dims.aspect_ratio, rel=1e-6)
        assert scaled.width <= 1080
        assert scaled.height <= 1920

    def test_should_scale_down_oversized_image(self):
        """Test scaling down oversized image."""
        dims = ImageDimensions(width=2160, height=3840)

        scaled = dims.scale_to_fit(max_width=1080, max_height=1920)

        assert scaled.width == 1080
        assert scaled.height == 1920

    def test_should_raise_error_on_invalid_max_dimensions(self):
        """Test error on invalid max dimensions."""
        dims = ImageDimensions(width=1080, height=1920)

        with pytest.raises(ProcessingError):
            dims.scale_to_fit(max_width=0, max_height=1920)

    def test_should_handle_square_dimensions(self):
        """Test square image dimensions."""
        dims = ImageDimensions(width=1000, height=1000)

        assert dims.aspect_ratio == pytest.approx(1.0)
        assert dims.is_portrait is False
        assert dims.is_landscape is False


class TestScreenshotConfig:
    """Test ScreenshotConfig data model."""

    def test_should_create_valid_screenshot_config(self):
        """Test creating valid screenshot config."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)
        config = ScreenshotConfig(
            input_path="/input/screenshot.jpg",
            output_path="/output/screenshot.jpg",
            tablet_preset=tablet,
        )

        assert config.input_path == "/input/screenshot.jpg"
        assert config.output_path == "/output/screenshot.jpg"
        assert config.jpeg_quality == 95

    def test_should_use_default_jpeg_quality(self):
        """Test default JPEG quality."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)
        config = ScreenshotConfig(
            input_path="/input/screenshot.jpg",
            output_path="/output/screenshot.jpg",
            tablet_preset=tablet,
        )

        assert config.jpeg_quality == 95

    def test_should_use_custom_jpeg_quality(self):
        """Test custom JPEG quality."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)
        config = ScreenshotConfig(
            input_path="/input/screenshot.jpg",
            output_path="/output/screenshot.jpg",
            tablet_preset=tablet,
            jpeg_quality=80,
        )

        assert config.jpeg_quality == 80

    def test_should_use_default_background_color(self):
        """Test default background color."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)
        config = ScreenshotConfig(
            input_path="/input/screenshot.jpg",
            output_path="/output/screenshot.jpg",
            tablet_preset=tablet,
        )

        assert config.background_color == (0, 0, 0)

    def test_should_raise_error_on_empty_input_path(self):
        """Test error on empty input path."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)

        with pytest.raises(ProcessingError):
            ScreenshotConfig(
                input_path="",
                output_path="/output/screenshot.jpg",
                tablet_preset=tablet,
            )

    def test_should_raise_error_on_invalid_jpeg_quality(self):
        """Test error on invalid JPEG quality."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)

        with pytest.raises(ProcessingError):
            ScreenshotConfig(
                input_path="/input/screenshot.jpg",
                output_path="/output/screenshot.jpg",
                tablet_preset=tablet,
                jpeg_quality=150,
            )

    def test_should_raise_error_on_invalid_rgb_color(self):
        """Test error on invalid RGB color."""
        tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)

        with pytest.raises(ProcessingError):
            ScreenshotConfig(
                input_path="/input/screenshot.jpg",
                output_path="/output/screenshot.jpg",
                tablet_preset=tablet,
                background_color=(256, 0, 0),
            )


class TestProcessingResult:
    """Test ProcessingResult data model."""

    def test_should_create_successful_result(self):
        """Test creating successful processing result."""
        result = ProcessingResult(
            input_file="/input/screenshot.jpg",
            output_file="/output/screenshot.jpg",
            success=True,
            error=None,
            file_size_mb=0.5,
            scaled_dimensions=(920, 1920),
        )

        assert result.success is True
        assert result.error is None
        assert result.file_size_mb == 0.5

    def test_should_create_failed_result(self):
        """Test creating failed processing result."""
        result = ProcessingResult(
            input_file="/input/screenshot.jpg",
            output_file="/output/screenshot.jpg",
            success=False,
            error="Image file corrupted",
            file_size_mb=None,
            scaled_dimensions=None,
        )

        assert result.success is False
        assert "corrupted" in result.error.lower()

    def test_should_generate_status_string_for_success(self):
        """Test status string for successful result."""
        result = ProcessingResult(
            input_file="/input/screenshot.jpg",
            output_file="/output/screenshot.jpg",
            success=True,
            error=None,
        )

        assert result.status_str == "SUCCESS"

    def test_should_generate_status_string_for_failure(self):
        """Test status string for failed result."""
        result = ProcessingResult(
            input_file="/input/screenshot.jpg",
            output_file="/output/screenshot.jpg",
            success=False,
            error="Test error",
        )

        assert "FAILED" in result.status_str
        assert "Test error" in result.status_str

    def test_should_raise_error_on_success_with_error_message(self):
        """Test error when success=True but error message present."""
        with pytest.raises(ProcessingError):
            ProcessingResult(
                input_file="/input/screenshot.jpg",
                output_file="/output/screenshot.jpg",
                success=True,
                error="Should not have error message",
            )

    def test_should_raise_error_on_failure_without_error_message(self):
        """Test error when success=False but no error message."""
        with pytest.raises(ProcessingError):
            ProcessingResult(
                input_file="/input/screenshot.jpg",
                output_file="/output/screenshot.jpg",
                success=False,
                error=None,
            )

    def test_should_raise_error_on_negative_file_size(self):
        """Test error on negative file size."""
        with pytest.raises(ProcessingError):
            ProcessingResult(
                input_file="/input/screenshot.jpg",
                output_file="/output/screenshot.jpg",
                success=True,
                error=None,
                file_size_mb=-1.0,
            )
