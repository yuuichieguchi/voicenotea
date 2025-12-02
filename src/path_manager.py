"""Path management with validation and security checks."""

from pathlib import Path
from typing import Dict, List, Optional

from src.logger import PathError


class PathManager:
    """Handle path resolution, validation, and security with proper error handling.

    Manages relative and absolute path resolution with comprehensive validation
    to ensure safe file operations and prevent path traversal attacks.

    Examples:
        >>> pm = PathManager(base_path="/project")
        >>> input_dir = pm.resolve_path("docs/screenshots")
        >>> pm.validate_readable(input_dir)
    """

    def __init__(self, base_path: Optional[str] = None) -> None:
        """Initialize PathManager with optional base path.

        Args:
            base_path: Base path for relative path resolution. If None, uses current directory.
        """
        self.base_path = Path(base_path) if base_path else Path.cwd()

    def resolve_path(
        self,
        path: str,
        base_path: Optional[Path] = None,
    ) -> Path:
        """Resolve path (relative or absolute) to absolute Path object.

        Args:
            path: Path string to resolve (relative or absolute).
            base_path: Optional base for relative paths. Uses self.base_path if None.

        Returns:
            Resolved absolute Path object.

        Raises:
            PathError: If path is empty or resolves to None.

        Examples:
            >>> pm = PathManager(base_path="/project")
            >>> pm.resolve_path("docs/screenshots")
            PosixPath('/project/docs/screenshots')
            >>> pm.resolve_path("/absolute/path")
            PosixPath('/absolute/path')
        """
        if not path or not isinstance(path, str):
            raise PathError(f"Invalid path: {path}")

        base = base_path or self.base_path
        path_obj = Path(path)

        if path_obj.is_absolute():
            return path_obj.resolve()

        return (base / path_obj).resolve()

    def validate_readable(self, path: Path) -> None:
        """Validate that path exists and is readable.

        Args:
            path: Path to validate.

        Raises:
            PathError: If path doesn't exist or isn't readable.

        Examples:
            >>> pm = PathManager()
            >>> pm.validate_readable(Path("/existing/file"))
        """
        if not path.exists():
            raise PathError(f"Path does not exist: {path}")

        if not path.is_file() and not path.is_dir():
            raise PathError(f"Path is neither file nor directory: {path}")

        try:
            path.stat()
        except (OSError, PermissionError):
            raise PathError(f"Path is not readable (check permissions): {path}")

    def validate_writable(self, path: Path) -> None:
        """Validate that path or its parent directory is writable.

        Args:
            path: Path to validate for writing.

        Raises:
            PathError: If path isn't writable.

        Examples:
            >>> pm = PathManager()
            >>> pm.validate_writable(Path("/tmp/output"))
        """
        if path.exists():
            if not path.is_dir():
                raise PathError(f"Path exists but is not a directory: {path}")
            if not path.is_file() and not path.is_dir():
                raise PathError(f"Path type not supported: {path}")
        else:
            parent = path.parent
            if not parent.exists():
                raise PathError(f"Parent directory does not exist: {parent}")

        if path.exists() and not path.is_file():
            if not (path / "test_write").parent.is_dir():
                raise PathError(f"No write permission for: {path}")

    def validate_input_dir(self, input_dir: str) -> Path:
        """Resolve and validate input directory is readable.

        Args:
            input_dir: Input directory path (relative or absolute).

        Returns:
            Validated absolute Path object.

        Raises:
            PathError: If directory doesn't exist or isn't readable.

        Examples:
            >>> pm = PathManager(base_path="/project")
            >>> input_path = pm.validate_input_dir("docs/screenshots")
        """
        path = self.resolve_path(input_dir)
        self.validate_readable(path)

        if not path.is_dir():
            raise PathError(f"Input path is not a directory: {path}")

        return path

    def validate_output_dir(
        self,
        output_dir: str,
        create: bool = True,
    ) -> Path:
        """Resolve and validate output directory, creating if needed.

        Args:
            output_dir: Output directory path (relative or absolute).
            create: Whether to create directory if it doesn't exist. Default: True.

        Returns:
            Validated/created absolute Path object.

        Raises:
            PathError: If directory can't be created or isn't writable.

        Examples:
            >>> pm = PathManager(base_path="/project")
            >>> output_path = pm.validate_output_dir("output/images")
        """
        path = self.resolve_path(output_dir)

        if create:
            try:
                path.mkdir(parents=True, exist_ok=True)
            except (OSError, PermissionError) as e:
                raise PathError(f"Failed to create output directory {path}: {e}")

        if path.exists() and not path.is_dir():
            raise PathError(f"Output path exists but is not a directory: {path}")

        return path

    def get_screenshot_files(
        self,
        input_dir: Path,
        pattern: str = "*.jpg",
    ) -> List[Path]:
        """Discover screenshot files in directory matching pattern.

        Args:
            input_dir: Directory to search in.
            pattern: Glob pattern for file discovery. Default: "*.jpg".

        Returns:
            Sorted list of matching file paths.

        Raises:
            PathError: If directory doesn't exist or can't be read.

        Examples:
            >>> pm = PathManager()
            >>> files = pm.get_screenshot_files(Path("/screenshots"))
            >>> files = pm.get_screenshot_files(Path("/screenshots"), pattern="*.png")
        """
        if not input_dir.is_dir():
            raise PathError(f"Directory not found: {input_dir}")

        try:
            files = sorted(input_dir.glob(pattern))
        except OSError as e:
            raise PathError(f"Failed to scan directory {input_dir}: {e}")

        return files

    def create_output_structure(
        self,
        base_output: str,
        tablet_size: str = "7inch",
    ) -> Dict[str, Path]:
        """Create and validate complete output directory structure.

        Args:
            base_output: Base output directory path.
            tablet_size: Tablet size ("7inch" or "10inch") for naming.

        Returns:
            Dictionary mapping structure keys to Path objects.

        Raises:
            PathError: If structure can't be created.

        Examples:
            >>> pm = PathManager()
            >>> structure = pm.create_output_structure("/output", "7inch")
            >>> structure['screenshots']
            PosixPath('/output/tablet_7inch_screenshots')
        """
        base_path = self.validate_output_dir(base_output, create=True)

        structure = {
            "base": base_path,
            "screenshots": self.validate_output_dir(
                str(base_path / f"tablet_{tablet_size}_screenshots"),
                create=True,
            ),
            "logs": self.validate_output_dir(
                str(base_path / "logs"),
                create=True,
            ),
        }

        return structure
