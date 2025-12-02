"""Pytest fixtures and configuration for tablet screenshot tests."""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from PIL import Image


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create temporary project directory structure.

    Returns:
        Dictionary with paths to various directories.
    """
    dirs = {
        'root': tmp_path,
        'input': tmp_path / 'input_screenshots',
        'output': tmp_path / 'output_screenshots',
        'logs': tmp_path / 'logs',
    }

    for dir_path in dirs.values():
        if isinstance(dir_path, Path):
            dir_path.mkdir(parents=True, exist_ok=True)

    return dirs


@pytest.fixture
def sample_portrait_image(tmp_project_dir):
    """Create sample portrait screenshot image (1080x1920).

    Returns:
        Path to created image file.
    """
    img = Image.new('RGB', (1080, 1920), color='blue')
    output_path = tmp_project_dir['input'] / 'sample_portrait.jpg'
    img.save(output_path, 'JPEG')
    return output_path


@pytest.fixture
def sample_landscape_image(tmp_project_dir):
    """Create sample landscape screenshot image (1920x1080).

    Returns:
        Path to created image file.
    """
    img = Image.new('RGB', (1920, 1080), color='red')
    output_path = tmp_project_dir['input'] / 'sample_landscape.jpg'
    img.save(output_path, 'JPEG')
    return output_path


@pytest.fixture
def corrupted_image_file(tmp_project_dir):
    """Create a corrupted image file.

    Returns:
        Path to corrupted file.
    """
    corrupted_path = tmp_project_dir['input'] / 'corrupted.jpg'
    with open(corrupted_path, 'wb') as f:
        f.write(b'This is not a valid JPEG image')
    return corrupted_path


@pytest.fixture
def sample_config():
    """Create sample configuration dictionary.

    Returns:
        Configuration dict.
    """
    return {
        'tablet': {'size': '7inch'},
        'paths': {
            'input_dir': 'tests/fixtures/input',
            'output_dir': 'tests/fixtures/output',
        },
        'processing': {
            'jpeg_quality': 95,
            'background_color': [0, 0, 0],
            'size_threshold_mb': 8.0,
        },
        'logging': {'level': 'INFO'},
    }


@pytest.fixture
def mock_logger():
    """Create mock logger for testing.

    Returns:
        MagicMock logger instance.
    """
    logger = MagicMock()
    logger.info = MagicMock()
    logger.warning = MagicMock()
    logger.error = MagicMock()
    logger.debug = MagicMock()
    logger.exception = MagicMock()
    return logger


@pytest.fixture
def yaml_config_content():
    """YAML configuration content as string.

    Returns:
        YAML formatted configuration string.
    """
    return """
tablet:
  size: 7inch

paths:
  input_dir: docs/mobile_screenshots
  output_dir: docs/tablet_7inch_screenshots

processing:
  jpeg_quality: 95
  background_color: [0, 0, 0]
  size_threshold_mb: 8.0

logging:
  level: INFO
"""


@pytest.fixture
def yaml_config_file(tmp_project_dir, yaml_config_content):
    """Create temporary YAML configuration file.

    Returns:
        Path to YAML config file.
    """
    config_path = tmp_project_dir['root'] / 'config.yaml'
    config_path.write_text(yaml_config_content)
    return config_path
