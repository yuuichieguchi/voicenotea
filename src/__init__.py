"""Tablet screenshot generator - Production-grade image processing tool."""

__version__ = "2.0.0"
__author__ = "Voicenotea Team"

from src.config import ConfigManager
from src.logger import setup_logger
from src.path_manager import PathManager
from src.models import TabletPreset, ScreenshotConfig, ImageDimensions
from src.image_processor import ImageProcessor
from src.generator import ScreenshotGenerator

__all__ = [
    "ConfigManager",
    "setup_logger",
    "PathManager",
    "TabletPreset",
    "ScreenshotConfig",
    "ImageDimensions",
    "ImageProcessor",
    "ScreenshotGenerator",
]
