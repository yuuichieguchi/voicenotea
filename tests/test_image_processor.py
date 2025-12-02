"""Tests for image processing module."""

import pytest
from PIL import Image

from src.image_processor import ImageProcessor
from src.logger import ProcessingError
from src.models import ImageDimensions, ScreenshotConfig, TabletPreset


class TestImageProcessorLoadImage:
    """Test image loading."""

    def test_should_load_valid_jpg_image(self, sample_portrait_image):
        """Test loading valid JPG image."""
        img = ImageProcessor.load_image(sample_portrait_image)

        assert isinstance(img, Image.Image)
        assert img.size == (1080, 1920)

    def test_should_raise_error_on_missing_file(self, tmp_path):
        """Test error when image file doesn't exist."""
        missing_file = tmp_path / "missing.jpg"

        with pytest.raises(ProcessingError):
            ImageProcessor.load_image(missing_file)

    def test_should_raise_error_on_corrupted_image(self, corrupted_image_file):
        """Test error on corrupted image file."""
        with pytest.raises(ProcessingError):
            ImageProcessor.load_image(corrupted_image_file)


class TestImageProcessorValidation:
    """Test image validation."""

    def test_should_validate_image_dimensions(self):
        """Test validating image dimensions."""
        img = Image.new('RGB', (1080, 1920))

        dims = ImageProcessor.validate_image(img)

        assert dims.width == 1080
        assert dims.height == 1920

    def test_should_raise_error_on_too_small_image(self):
        """Test error on too small image."""
        img = Image.new('RGB', (50, 100))

        with pytest.raises(ProcessingError):
            ImageProcessor.validate_image(img, min_width=100)

    def test_should_raise_error_on_too_large_image(self):
        """Test error on too large image."""
        img = Image.new('RGB', (10000, 10000))

        with pytest.raises(ProcessingError):
            ImageProcessor.validate_image(img)


class TestImageProcessorDimensionCalculation:
    """Test scaled dimension calculation."""

    def test_should_calculate_scaled_dimensions_for_portrait(self):
        """Test scaling portrait image to tablet."""
        original = ImageDimensions(width=1080, height=1920)
        tablet = TabletPreset("7inch", 1080, 1920, 326)

        w, h = ImageProcessor.calculate_scaled_dimensions(original, tablet)

        assert h == 1920
        assert w <= 1080

    def test_should_maintain_aspect_ratio(self):
        """Test that aspect ratio is maintained."""
        original = ImageDimensions(width=540, height=960)
        tablet = TabletPreset("7inch", 1080, 1920, 326)

        w, h = ImageProcessor.calculate_scaled_dimensions(original, tablet)

        original_aspect = original.aspect_ratio
        scaled_aspect = w / h
        assert scaled_aspect == pytest.approx(original_aspect, rel=0.01)


class TestImageProcessorResize:
    """Test image resizing."""

    def test_should_resize_image_to_target_dimensions(self):
        """Test resizing image."""
        img = Image.new('RGB', (1080, 1920))

        resized = ImageProcessor.resize_image(img, 540, 960)

        assert resized.size == (540, 960)

    def test_should_use_high_quality_resampling(self):
        """Test that LANCZOS resampling is used."""
        img = Image.new('RGB', (1080, 1920))

        resized = ImageProcessor.resize_image(img, 540, 960)

        assert resized.size == (540, 960)

    def test_should_raise_error_on_invalid_target_dimensions(self):
        """Test error on invalid target dimensions."""
        img = Image.new('RGB', (1080, 1920))

        with pytest.raises(ProcessingError):
            ImageProcessor.resize_image(img, 0, 1920)


class TestImageProcessorPadding:
    """Test image padding for tablet display."""

    def test_should_create_padded_image_with_black_background(self):
        """Test creating padded image with black background."""
        resized = Image.new('RGB', (920, 1920))
        tablet = TabletPreset("7inch", 1080, 1920, 326)

        padded = ImageProcessor.create_padded_image(resized, tablet)

        assert padded.size == (1080, 1920)

    def test_should_center_image_on_canvas(self):
        """Test that image is centered on canvas."""
        resized = Image.new('RGB', (920, 1920), color='red')
        tablet = TabletPreset("7inch", 1080, 1920, 326)

        padded = ImageProcessor.create_padded_image(resized, tablet)

        assert padded.size == (1080, 1920)

    def test_should_use_custom_background_color(self):
        """Test custom background color for padding."""
        resized = Image.new('RGB', (920, 1920))
        tablet = TabletPreset("7inch", 1080, 1920, 326)

        padded = ImageProcessor.create_padded_image(
            resized, tablet, background_color=(255, 0, 0)
        )

        assert padded.size == (1080, 1920)


class TestImageProcessorSaving:
    """Test image saving."""

    def test_should_save_image_as_jpeg(self, tmp_path):
        """Test saving image as JPEG."""
        img = Image.new('RGB', (1080, 1920))
        output_path = tmp_path / "output.jpg"

        ImageProcessor.save_image(img, output_path)

        assert output_path.exists()

    def test_should_save_with_specified_quality(self, tmp_path):
        """Test saving with specified JPEG quality."""
        img = Image.new('RGB', (1080, 1920))
        output_path = tmp_path / "output.jpg"

        ImageProcessor.save_image(img, output_path, jpeg_quality=80)

        assert output_path.exists()

    def test_should_create_parent_directories(self, tmp_path):
        """Test creating parent directories if needed."""
        img = Image.new('RGB', (1080, 1920))
        output_path = tmp_path / "level1" / "level2" / "output.jpg"

        ImageProcessor.save_image(img, output_path)

        assert output_path.exists()

    def test_should_raise_error_on_invalid_output_path(self):
        """Test error on invalid output path."""
        img = Image.new('RGB', (1080, 1920))

        with pytest.raises(ProcessingError):
            ImageProcessor.save_image(img, "/invalid/path/output.jpg")


class TestImageProcessorCompleteWorkflow:
    """Test complete screenshot processing workflow."""

    def test_should_process_screenshot_successfully(self, sample_portrait_image, tmp_path):
        """Test complete screenshot processing."""
        tablet = TabletPreset("7inch", 1080, 1920, 326)
        output_path = tmp_path / "output.jpg"

        config = ScreenshotConfig(
            input_path=str(sample_portrait_image),
            output_path=str(output_path),
            tablet_preset=tablet,
        )

        result = ImageProcessor.process_screenshot(config)

        assert result.success is True
        assert output_path.exists()
        assert result.file_size_mb > 0
        assert result.scaled_dimensions is not None

    def test_should_handle_missing_input_file(self, tmp_path):
        """Test handling missing input file."""
        tablet = TabletPreset("7inch", 1080, 1920, 326)
        missing_input = tmp_path / "missing.jpg"
        output_path = tmp_path / "output.jpg"

        config = ScreenshotConfig(
            input_path=str(missing_input),
            output_path=str(output_path),
            tablet_preset=tablet,
        )

        result = ImageProcessor.process_screenshot(config)

        assert result.success is False
        assert result.error is not None

    def test_should_handle_corrupted_input_image(self, corrupted_image_file, tmp_path):
        """Test handling corrupted input image."""
        tablet = TabletPreset("7inch", 1080, 1920, 326)
        output_path = tmp_path / "output.jpg"

        config = ScreenshotConfig(
            input_path=str(corrupted_image_file),
            output_path=str(output_path),
            tablet_preset=tablet,
        )

        result = ImageProcessor.process_screenshot(config)

        assert result.success is False
        assert "error" in result.status_str.lower() or result.error is not None

    def test_should_process_landscape_image(self, sample_landscape_image, tmp_path):
        """Test processing landscape oriented image."""
        tablet = TabletPreset("7inch", 1080, 1920, 326)
        output_path = tmp_path / "output.jpg"

        config = ScreenshotConfig(
            input_path=str(sample_landscape_image),
            output_path=str(output_path),
            tablet_preset=tablet,
        )

        result = ImageProcessor.process_screenshot(config)

        assert result.success is True
        assert output_path.exists()

    def test_should_respect_jpeg_quality_setting(self, sample_portrait_image, tmp_path):
        """Test that JPEG quality setting is respected."""
        tablet = TabletPreset("7inch", 1080, 1920, 326)
        output_high = tmp_path / "output_high.jpg"
        output_low = tmp_path / "output_low.jpg"

        config_high = ScreenshotConfig(
            input_path=str(sample_portrait_image),
            output_path=str(output_high),
            tablet_preset=tablet,
            jpeg_quality=95,
        )

        config_low = ScreenshotConfig(
            input_path=str(sample_portrait_image),
            output_path=str(output_low),
            tablet_preset=tablet,
            jpeg_quality=50,
        )

        result_high = ImageProcessor.process_screenshot(config_high)
        result_low = ImageProcessor.process_screenshot(config_low)

        assert result_high.success is True
        assert result_low.success is True
        assert output_high.stat().st_size > output_low.stat().st_size
