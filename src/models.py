"""Data models and type definitions for tablet screenshot generation."""

from dataclasses import dataclass, field
from typing import Optional, Tuple

from src.logger import ProcessingError


@dataclass
class TabletPreset:
    """Tablet device specifications.

    Attributes:
        size: Tablet size identifier ("7inch" or "10inch").
        width: Screen width in pixels.
        height: Screen height in pixels.
        dpi: Screen pixel density (dots per inch).

    Examples:
        >>> tablet = TabletPreset(size="7inch", width=1080, height=1920, dpi=326)
        >>> tablet.aspect_ratio
        0.5625
    """

    size: str
    width: int
    height: int
    dpi: int

    def __post_init__(self) -> None:
        """Validate tablet preset after initialization."""
        if self.width <= 0 or self.height <= 0:
            raise ProcessingError(
                f"Invalid tablet dimensions: {self.width}x{self.height}. "
                "Both must be positive integers."
            )
        if self.dpi <= 0:
            raise ProcessingError(f"Invalid DPI: {self.dpi}. Must be positive.")
        if self.size not in ("7inch", "10inch"):
            raise ProcessingError(
                f"Invalid tablet size: {self.size}. Must be '7inch' or '10inch'."
            )

    @property
    def aspect_ratio(self) -> float:
        """Get tablet screen aspect ratio (width/height).

        Returns:
            Aspect ratio as float.
        """
        return self.width / self.height

    @property
    def resolution_str(self) -> str:
        """Get human-readable resolution string.

        Returns:
            Resolution formatted as "WIDTHxHEIGHT".
        """
        return f"{self.width}x{self.height}"


@dataclass
class ImageDimensions:
    """Image dimensions with aspect ratio calculation.

    Attributes:
        width: Image width in pixels.
        height: Image height in pixels.

    Examples:
        >>> dims = ImageDimensions(width=1080, height=1920)
        >>> dims.aspect_ratio
        0.5625
    """

    width: int
    height: int

    def __post_init__(self) -> None:
        """Validate dimensions after initialization."""
        if self.width <= 0 or self.height <= 0:
            raise ProcessingError(
                f"Invalid image dimensions: {self.width}x{self.height}. "
                "Both must be positive integers."
            )

    @property
    def aspect_ratio(self) -> float:
        """Get image aspect ratio (width/height).

        Returns:
            Aspect ratio as float.
        """
        return self.width / self.height

    @property
    def is_portrait(self) -> bool:
        """Check if image is in portrait orientation (height > width).

        Returns:
            True if portrait, False otherwise.
        """
        return self.height > self.width

    @property
    def is_landscape(self) -> bool:
        """Check if image is in landscape orientation (width > height).

        Returns:
            True if landscape, False otherwise.
        """
        return self.width > self.height

    def scale_to_fit(
        self,
        max_width: int,
        max_height: int,
    ) -> "ImageDimensions":
        """Calculate scaled dimensions to fit within bounds.

        Maintains aspect ratio while fitting within max dimensions.

        Args:
            max_width: Maximum width in pixels.
            max_height: Maximum height in pixels.

        Returns:
            New ImageDimensions scaled to fit.

        Raises:
            ProcessingError: If max dimensions are invalid.
        """
        if max_width <= 0 or max_height <= 0:
            raise ProcessingError(
                f"Invalid max dimensions: {max_width}x{max_height}. "
                "Both must be positive."
            )

        width_scale = max_width / self.width
        height_scale = max_height / self.height
        scale = min(width_scale, height_scale)

        return ImageDimensions(
            width=round(self.width * scale),
            height=round(self.height * scale),
        )


@dataclass
class ScreenshotConfig:
    """Configuration for processing a single screenshot.

    Attributes:
        input_path: Path to input screenshot file.
        output_path: Path to output screenshot file.
        tablet_preset: Target tablet specifications.
        jpeg_quality: JPEG compression quality (1-100).
        background_color: RGB background color tuple.

    Examples:
        >>> tablet = TabletPreset("7inch", 1080, 1920, 326)
        >>> config = ScreenshotConfig(
        ...     input_path="/input/screenshot.jpg",
        ...     output_path="/output/screenshot.jpg",
        ...     tablet_preset=tablet,
        ...     jpeg_quality=95,
        ... )
    """

    input_path: str
    output_path: str
    tablet_preset: TabletPreset
    jpeg_quality: int = 95
    background_color: Tuple[int, int, int] = field(default=(0, 0, 0))

    def __post_init__(self) -> None:
        """Validate configuration after initialization."""
        if not self.input_path:
            raise ProcessingError("Input path cannot be empty")
        if not self.output_path:
            raise ProcessingError("Output path cannot be empty")
        if not (1 <= self.jpeg_quality <= 100):
            raise ProcessingError(
                f"JPEG quality must be 1-100, got {self.jpeg_quality}"
            )
        if len(self.background_color) != 3:
            raise ProcessingError(
                f"Background color must be RGB tuple, got {self.background_color}"
            )
        for channel in self.background_color:
            if not (0 <= channel <= 255):
                raise ProcessingError(
                    f"RGB channel must be 0-255, got {channel}"
                )


@dataclass
class ProcessingResult:
    """Result of processing a single screenshot.

    Attributes:
        input_file: Path to processed input file.
        output_file: Path to generated output file.
        success: Whether processing succeeded.
        error: Error message if processing failed. None if successful.
        file_size_mb: Output file size in MB. None if failed.
        scaled_dimensions: Output dimensions. None if failed.

    Examples:
        >>> result = ProcessingResult(
        ...     input_file="/input/screenshot.jpg",
        ...     output_file="/output/screenshot.jpg",
        ...     success=True,
        ...     error=None,
        ...     file_size_mb=0.5,
        ...     scaled_dimensions=(920, 1920),
        ... )
    """

    input_file: str
    output_file: str
    success: bool
    error: Optional[str] = None
    file_size_mb: Optional[float] = None
    scaled_dimensions: Optional[Tuple[int, int]] = None

    def __post_init__(self) -> None:
        """Validate result after initialization."""
        if self.success and self.error is not None:
            raise ProcessingError("Success result cannot have error message")
        if not self.success and self.error is None:
            raise ProcessingError("Failed result must have error message")
        if self.file_size_mb is not None and self.file_size_mb < 0:
            raise ProcessingError(f"File size cannot be negative: {self.file_size_mb}")

    @property
    def status_str(self) -> str:
        """Get human-readable status string.

        Returns:
            Status string ("SUCCESS", "FAILED", or error message).
        """
        if self.success:
            return "SUCCESS"
        return f"FAILED: {self.error}"
