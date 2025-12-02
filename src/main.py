"""Command-line interface for tablet screenshot generation."""

import argparse
import sys
from pathlib import Path
from typing import Dict, Optional

from src.config import ConfigError, ConfigManager
from src.generator import ScreenshotGenerator
from src.logger import (
    FatalError,
    PathError,
    ProcessingError,
    log_exception,
    setup_logger,
)


def parse_arguments() -> argparse.Namespace:
    """Parse command-line arguments.

    Returns:
        Parsed arguments.

    Examples:
        >>> args = parse_arguments()
        >>> args.tablet_size
        '7inch'
    """
    parser = argparse.ArgumentParser(
        description="Generate tablet screenshots from mobile screenshots",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Process with default configuration
  python generate_tablet_screenshots.py

  # Specify tablet size
  python generate_tablet_screenshots.py --tablet-size 10inch

  # Custom paths
  python generate_tablet_screenshots.py --input docs/screenshots --output output/tablets

  # Use config file
  python generate_tablet_screenshots.py --config config.yaml --verbose
        """,
    )

    parser.add_argument(
        "--config",
        type=str,
        help="Path to YAML configuration file",
    )

    parser.add_argument(
        "--tablet-size",
        type=str,
        choices=["7inch", "10inch"],
        default="7inch",
        help="Target tablet size (default: 7inch)",
    )

    parser.add_argument(
        "--input",
        type=str,
        help="Input screenshots directory (overrides config)",
    )

    parser.add_argument(
        "--output",
        type=str,
        help="Output directory for processed screenshots (overrides config)",
    )

    parser.add_argument(
        "--quality",
        type=int,
        choices=range(1, 101),
        help="JPEG quality 1-100 (default: 95)",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging (DEBUG level)",
    )

    return parser.parse_args()


def merge_configs(
    yaml_config: Optional[Dict],
    cli_args: argparse.Namespace,
) -> Dict:
    """Merge YAML and CLI arguments into final configuration.

    Priority: CLI args > YAML config > defaults.

    Args:
        yaml_config: Configuration from YAML file (may be None).
        cli_args: Parsed CLI arguments.

    Returns:
        Merged configuration dictionary.
    """
    config = yaml_config or {}

    # Ensure nested dicts exist
    if "tablet" not in config:
        config["tablet"] = {}
    if "paths" not in config:
        config["paths"] = {}
    if "processing" not in config:
        config["processing"] = {}
    if "logging" not in config:
        config["logging"] = {}

    # Override with CLI arguments
    if cli_args.tablet_size:
        config["tablet"]["size"] = cli_args.tablet_size

    if cli_args.input:
        config["paths"]["input_dir"] = cli_args.input

    if cli_args.output:
        config["paths"]["output_dir"] = cli_args.output

    if cli_args.quality:
        config["processing"]["jpeg_quality"] = cli_args.quality

    if cli_args.verbose:
        config["logging"]["level"] = "DEBUG"
    else:
        config["logging"]["level"] = config["logging"].get("level", "INFO")

    return config


def main() -> int:
    """Main entry point with error handling.

    Returns:
        Exit code (0=success, non-zero=failure).
    """
    args = parse_arguments()

    # Setup logging
    log_level = "DEBUG" if args.verbose else "INFO"
    logger = setup_logger(__name__, level=log_level)

    try:
        # Load configuration
        if args.config:
            logger.info(f"Loading configuration from {args.config}")
            config_manager = ConfigManager(config_path=args.config, tablet_size=args.tablet_size)
        else:
            config_manager = ConfigManager(tablet_size=args.tablet_size)

        config_manager.validate_config()
        yaml_config = config_manager.to_dict()

        # Merge with CLI arguments
        final_config = merge_configs(yaml_config, args)

        # Validate required paths
        if not final_config.get("paths", {}).get("input_dir"):
            raise ConfigError("Input directory must be specified (--input or config)")

        if not final_config.get("paths", {}).get("output_dir"):
            raise ConfigError("Output directory must be specified (--output or config)")

        # Initialize generator
        generator = ScreenshotGenerator(final_config, logger=logger)

        # Validate setup
        if not generator.validate_setup():
            return 2

        # Process screenshots
        input_dir = final_config["paths"]["input_dir"]
        logger.info(f"Processing screenshots from: {input_dir}")

        results = generator.process_directory(input_dir)

        if not results:
            logger.warning("No screenshots were processed")
            return 1

        # Print summary and get exit code
        exit_code = generator.print_summary()

        return exit_code

    except ConfigError as e:
        return log_exception(logger, e)
    except PathError as e:
        return log_exception(logger, e)
    except ProcessingError as e:
        return log_exception(logger, e)
    except FatalError as e:
        return log_exception(logger, e)
    except Exception as e:
        logger.exception(f"Unexpected error: {e}")
        return 10


if __name__ == "__main__":
    sys.exit(main())
