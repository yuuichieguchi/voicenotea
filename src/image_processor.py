"""Image processing and transformation operations."""

from pathlib import Path
from typing import Tuple

from PIL import Image

from src.logger import ProcessingError
from src.models import ImageDimensions, ProcessingResult, ScreenshotConfig, TabletPreset


class ImageProcessor:
    """Process and transform images for tablet display.

    Handles image loading, validation, resizing, and saving with proper
    error handling and quality preservation.

    Examples:
        >>> processor = ImageProcessor()
        >>> processor.process_screenshot(
        ...     config=ScreenshotConfig(...),
        ... )
    """

    SUPPORTED_FORMATS = {"jpg", "jpeg", "png"}
    MAX_IMAGE_DIMENSION = 8000

    @staticmethod
    def load_image(input_path: Path) -> Image.Image:
        """Load image from file.

        Args:
            input_path: Path to image file.

        Returns:
            PIL Image object.

        Raises:
            ProcessingError: If file doesn't exist or can't be opened.

        Examples:
            >>> img = ImageProcessor.load_image(Path("/screenshot.jpg"))
        """
        if not input_path.exists():
            raise ProcessingError(f"Input file not found: {input_path}")

        try:
            with Image.open(input_path) as img:
                img.load()
                return img.copy()
        except FileNotFoundError as e:
            raise ProcessingError(f"Cannot find image file: {input_path}") from e
        except (IOError, OSError, ValueError) as e:
            raise ProcessingError(f"Corrupted or invalid image file {input_path}: {e}") from e

    @staticmethod
    def validate_image(img: Image.Image, min_width: int = 100) -> ImageDimensions:
        """Validate image and return dimensions.

        Args:
            img: PIL Image object to validate.
            min_width: Minimum acceptable width in pixels.

        Returns:
            ImageDimensions object.

        Raises:
            ProcessingError: If image is invalid.

        Examples:
            >>> img = Image.new('RGB', (1080, 1920))
            >>> dims = ImageProcessor.validate_image(img)
        """
        try:
            width, height = img.size
        except (AttributeError, TypeError) as e:
            raise ProcessingError(f"Cannot determine image size: {e}") from e

        if width < min_width or height < min_width:
            raise ProcessingError(
                f"Image too small: {width}x{height}. Minimum: {min_width}x{min_width}"
            )

        if width > ImageProcessor.MAX_IMAGE_DIMENSION or height > ImageProcessor.MAX_IMAGE_DIMENSION:
            raise ProcessingError(
                f"Image too large: {width}x{height}. "
                f"Maximum: {ImageProcessor.MAX_IMAGE_DIMENSION}x{ImageProcessor.MAX_IMAGE_DIMENSION}"
            )

        return ImageDimensions(width=width, height=height)

    @staticmethod
    def calculate_scaled_dimensions(
        original_dims: ImageDimensions,
        tablet_preset: TabletPreset,
    ) -> Tuple[int, int]:
        """Calculate dimensions for scaling to tablet.

        Maintains aspect ratio while fitting within tablet bounds.

        Args:
            original_dims: Original image dimensions.
            tablet_preset: Target tablet specifications.

        Returns:
            Tuple of (scaled_width, scaled_height).

        Raises:
            ProcessingError: If calculation fails.

        Examples:
            >>> original = ImageDimensions(width=1080, height=1920)
            >>> tablet = TabletPreset("7inch", 1080, 1920, 326)
            >>> w, h = ImageProcessor.calculate_scaled_dimensions(original, tablet)
        """
        try:
            scaled = original_dims.scale_to_fit(
                tablet_preset.width,
                tablet_preset.height,
            )
            return scaled.width, scaled.height
        except (ValueError, ZeroDivisionError) as e:
            raise ProcessingError(f"Failed to calculate scaled dimensions: {e}") from e

    @staticmethod
    def resize_image(
        img: Image.Image,
        target_width: int,
        target_height: int,
    ) -> Image.Image:
        """Resize image using high-quality resampling.

        Args:
            img: PIL Image to resize.
            target_width: Target width in pixels.
            target_height: Target height in pixels.

        Returns:
            Resized PIL Image.

        Raises:
            ProcessingError: If resizing fails.

        Examples:
            >>> img = Image.new('RGB', (1080, 1920))
            >>> resized = ImageProcessor.resize_image(img, 920, 1920)
        """
        try:
            return img.resize(
                (target_width, target_height),
                Image.Resampling.LANCZOS,
            )
        except Exception as e:
            raise ProcessingError(f"Failed to resize image: {e}") from e

    @staticmethod
    def create_padded_image(
        resized_img: Image.Image,
        tablet_preset: TabletPreset,
        background_color: Tuple[int, int, int] = (0, 0, 0),
    ) -> Image.Image:
        """Create tablet-sized image with resized image centered and padded.

        Args:
            resized_img: Resized PIL Image.
            tablet_preset: Target tablet specifications.
            background_color: RGB tuple for padding background.

        Returns:
            Padded PIL Image in tablet dimensions.

        Raises:
            ProcessingError: If padding fails.

        Examples:
            >>> resized = Image.new('RGB', (920, 1920))
            >>> tablet = TabletPreset("7inch", 1080, 1920, 326)
            >>> padded = ImageProcessor.create_padded_image(resized, tablet)
        """
        try:
            tablet_img = Image.new(
                'RGB',
                (tablet_preset.width, tablet_preset.height),
                color=background_color,
            )

            resized_width, resized_height = resized_img.size
            x_offset = (tablet_preset.width - resized_width) // 2
            y_offset = (tablet_preset.height - resized_height) // 2

            tablet_img.paste(resized_img, (x_offset, y_offset))
            return tablet_img
        except (ValueError, TypeError, MemoryError) as e:
            raise ProcessingError(f"Failed to create padded image: {e}") from e

    @staticmethod
    def save_image(
        img: Image.Image,
        output_path: Path,
        jpeg_quality: int = 95,
    ) -> None:
        """Save image with quality optimization.

        Args:
            img: PIL Image to save.
            output_path: Path for output file.
            jpeg_quality: JPEG compression quality (1-100).

        Raises:
            ProcessingError: If saving fails.

        Examples:
            >>> img = Image.new('RGB', (1080, 1920))
            >>> ImageProcessor.save_image(img, Path("/output/screenshot.jpg"))
        """
        try:
            output_path.parent.mkdir(parents=True, exist_ok=True)

            img.save(
                output_path,
                'JPEG',
                quality=jpeg_quality,
                optimize=True,
            )
        except (IOError, OSError) as e:
            raise ProcessingError(f"Failed to save image to {output_path}: {e}") from e
        except Exception as e:
            raise ProcessingError(f"Unexpected error saving image: {e}") from e

    @staticmethod
    def process_screenshot(
        config: ScreenshotConfig,
    ) -> ProcessingResult:
        """Process single screenshot from configuration.

        Complete workflow: load, validate, resize, pad, save.

        Args:
            config: Screenshot processing configuration.

        Returns:
            ProcessingResult with outcome details.

        Examples:
            >>> config = ScreenshotConfig(
            ...     input_path="/input/screenshot.jpg",
            ...     output_path="/output/screenshot.jpg",
            ...     tablet_preset=TabletPreset("7inch", 1080, 1920, 326),
            ... )
            >>> result = ImageProcessor.process_screenshot(config)
        """
        input_path = Path(config.input_path)
        output_path = Path(config.output_path)

        try:
            img = ImageProcessor.load_image(input_path)
            original_dims = ImageProcessor.validate_image(img)

            scaled_width, scaled_height = ImageProcessor.calculate_scaled_dimensions(
                original_dims,
                config.tablet_preset,
            )

            resized_img = ImageProcessor.resize_image(
                img,
                scaled_width,
                scaled_height,
            )

            padded_img = ImageProcessor.create_padded_image(
                resized_img,
                config.tablet_preset,
                config.background_color,
            )

            ImageProcessor.save_image(
                padded_img,
                output_path,
                config.jpeg_quality,
            )

            file_size_mb = output_path.stat().st_size / (1024 * 1024)

            return ProcessingResult(
                input_file=str(input_path),
                output_file=str(output_path),
                success=True,
                error=None,
                file_size_mb=file_size_mb,
                scaled_dimensions=(scaled_width, scaled_height),
            )

        except ProcessingError as e:
            return ProcessingResult(
                input_file=str(input_path),
                output_file=str(output_path),
                success=False,
                error=str(e),
                file_size_mb=None,
                scaled_dimensions=None,
            )
        except Exception as e:
            return ProcessingResult(
                input_file=str(input_path),
                output_file=str(output_path),
                success=False,
                error=f"Unexpected error: {e}",
                file_size_mb=None,
                scaled_dimensions=None,
            )
