"""Main orchestrator for screenshot generation workflow."""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from src.config import ConfigManager
from src.image_processor import ImageProcessor
from src.logger import ProcessingError, setup_logger
from src.models import ProcessingResult, ScreenshotConfig, TabletPreset
from src.path_manager import PathManager


class ScreenshotGenerator:
    """Orchestrate complete screenshot generation workflow.

    Coordinates configuration loading, path resolution, image processing,
    and result aggregation with comprehensive error handling.

    Examples:
        >>> config_dict = {"tablet": {"size": "7inch"}, ...}
        >>> generator = ScreenshotGenerator(config_dict)
        >>> results = generator.process_directory("/screenshots")
    """

    def __init__(
        self,
        config: Dict,
        logger: Optional[logging.Logger] = None,
    ) -> None:
        """Initialize generator with configuration.

        Args:
            config: Configuration dictionary (from ConfigManager).
            logger: Optional logger instance. Creates one if not provided.
        """
        self.config = config
        self.logger = logger or setup_logger(__name__)
        self.path_manager = PathManager()
        self.results: List[ProcessingResult] = []

    def validate_setup(self) -> bool:
        """Validate configuration and paths are ready.

        Returns:
            True if setup is valid.

        Raises:
            ProcessingError: If setup is invalid.
        """
        try:
            tablet_size = self.config.get("tablet", {}).get("size", "7inch")
            if tablet_size not in ("7inch", "10inch"):
                raise ProcessingError(f"Invalid tablet size: {tablet_size}")

            input_dir = self.config.get("paths", {}).get("input_dir")
            if not input_dir:
                raise ProcessingError("Input directory not configured")

            output_dir = self.config.get("paths", {}).get("output_dir")
            if not output_dir:
                raise ProcessingError("Output directory not configured")

            self.logger.info(f"Setup validated for {tablet_size} tablet")
            return True

        except ProcessingError as e:
            self.logger.error(f"Setup validation failed: {e}")
            raise

    def get_tablet_preset(self) -> TabletPreset:
        """Create TabletPreset from configuration.

        Returns:
            TabletPreset instance.

        Raises:
            ProcessingError: If tablet configuration is invalid.
        """
        tablet_config = self.config.get("tablet", {})
        tablet_size = tablet_config.get("size", "7inch")

        presets = {
            "7inch": TabletPreset("7inch", 1080, 1920, 326),
            "10inch": TabletPreset("10inch", 1080, 1920, 216),
        }

        if tablet_size not in presets:
            raise ProcessingError(f"Unknown tablet size: {tablet_size}")

        return presets[tablet_size]

    def process_image(self, input_path: str) -> ProcessingResult:
        """Process single image.

        Args:
            input_path: Path to input screenshot.

        Returns:
            ProcessingResult with outcome.
        """
        try:
            tablet_preset = self.get_tablet_preset()
            processing_config = self.config.get("processing", {})

            output_path = self._get_output_path(input_path)

            config = ScreenshotConfig(
                input_path=input_path,
                output_path=output_path,
                tablet_preset=tablet_preset,
                jpeg_quality=processing_config.get("jpeg_quality", 95),
                background_color=tuple(processing_config.get("background_color", [0, 0, 0])),
            )

            result = ImageProcessor.process_screenshot(config)

            if result.success:
                self.logger.info(
                    f"Processed: {Path(input_path).name} "
                    f"({result.scaled_dimensions}) -> {result.file_size_mb:.2f}MB"
                )
            else:
                self.logger.error(f"Failed to process {input_path}: {result.error}")

            return result

        except Exception as e:
            self.logger.exception(f"Unexpected error processing {input_path}")
            return ProcessingResult(
                input_file=input_path,
                output_file="",
                success=False,
                error=str(e),
            )

    def process_directory(self, input_dir: str) -> List[ProcessingResult]:
        """Process all screenshots in directory.

        Args:
            input_dir: Path to input screenshot directory.

        Returns:
            List of ProcessingResult objects.
        """
        self.results = []
        self.logger.info(f"Starting batch processing: {input_dir}")

        try:
            input_path = self.path_manager.validate_input_dir(input_dir)
        except Exception as e:
            self.logger.error(f"Cannot access input directory: {e}")
            return []

        screenshot_files = self.path_manager.get_screenshot_files(
            input_path,
            pattern="*.jpg",
        )

        if not screenshot_files:
            self.logger.warning(f"No screenshot files found in {input_dir}")

        for screenshot_path in screenshot_files:
            result = self.process_image(str(screenshot_path))
            self.results.append(result)

        return self.results

    def get_processing_stats(self) -> Dict[str, int]:
        """Get statistics from processing results.

        Returns:
            Dictionary with success_count and failure_count.
        """
        success_count = sum(1 for r in self.results if r.success)
        failure_count = len(self.results) - success_count

        return {
            "total": len(self.results),
            "success": success_count,
            "failed": failure_count,
        }

    def print_summary(self) -> int:
        """Print processing summary and return exit code.

        Returns:
            0 if all succeeded, 1 if any failed.
        """
        stats = self.get_processing_stats()

        self.logger.info("=" * 60)
        self.logger.info("Processing Summary")
        self.logger.info("=" * 60)
        self.logger.info(f"Total: {stats['total']}")
        self.logger.info(f"Successful: {stats['success']}")
        self.logger.info(f"Failed: {stats['failed']}")
        self.logger.info("=" * 60)

        if stats['failed'] > 0:
            self.logger.warning("Some images failed processing")
            return 1

        return 0

    def _get_output_path(self, input_path: str) -> str:
        """Generate output path from input path.

        Args:
            input_path: Input file path.

        Returns:
            Output file path in output directory.
        """
        output_dir = self.config.get("paths", {}).get("output_dir", "output")
        input_file = Path(input_path).name

        return str(Path(output_dir) / input_file)
