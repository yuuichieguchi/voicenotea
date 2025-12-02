"""Tests for path management module."""

import pytest

from src.logger import PathError
from src.path_manager import PathManager


class TestPathManagerInitialization:
    """Test PathManager initialization."""

    def test_should_initialize_with_base_path(self, tmp_path):
        """Test creating PathManager with base path."""
        pm = PathManager(base_path=str(tmp_path))

        assert pm.base_path == tmp_path

    def test_should_initialize_with_current_directory(self):
        """Test creating PathManager without base path."""
        pm = PathManager()

        assert pm.base_path is not None


class TestPathResolution:
    """Test path resolution functionality."""

    def test_should_resolve_relative_path(self, tmp_path):
        """Test resolving relative path."""
        pm = PathManager(base_path=str(tmp_path))

        resolved = pm.resolve_path("subdir/file.txt")

        assert resolved.parent.name == "subdir"

    def test_should_resolve_absolute_path(self, tmp_path):
        """Test resolving absolute path."""
        pm = PathManager(base_path=str(tmp_path))
        abs_path = str(tmp_path / "absolute.txt")

        resolved = pm.resolve_path(abs_path)

        assert resolved == tmp_path / "absolute.txt"

    def test_should_raise_error_on_empty_path(self):
        """Test error on empty path string."""
        pm = PathManager()

        with pytest.raises(PathError):
            pm.resolve_path("")

    def test_should_raise_error_on_none_path(self):
        """Test error on None path."""
        pm = PathManager()

        with pytest.raises(PathError):
            pm.resolve_path(None)

    def test_should_normalize_path_with_dots(self, tmp_path):
        """Test path normalization with .. and .."""
        pm = PathManager(base_path=str(tmp_path))
        subdir = tmp_path / "subdir"
        subdir.mkdir()

        resolved = pm.resolve_path("subdir/../file.txt")

        assert resolved == tmp_path / "file.txt"


class TestValidateReadable:
    """Test readable path validation."""

    def test_should_validate_existing_file(self, tmp_path):
        """Test validating existing file."""
        test_file = tmp_path / "test.txt"
        test_file.write_text("test")
        pm = PathManager()

        pm.validate_readable(test_file)

    def test_should_validate_existing_directory(self, tmp_path):
        """Test validating existing directory."""
        pm = PathManager()

        pm.validate_readable(tmp_path)

    def test_should_raise_error_on_nonexistent_path(self):
        """Test error on nonexistent path."""
        pm = PathManager()

        with pytest.raises(PathError):
            pm.validate_readable(pm.resolve_path("/nonexistent/path"))

    def test_should_raise_error_on_nonexistent_symlink(self, tmp_path):
        """Test error on broken symlink."""
        pm = PathManager()
        broken_symlink = tmp_path / "broken_link"
        # Create symlink to non-existent file
        broken_symlink.symlink_to("/nonexistent/target")

        with pytest.raises(PathError):
            pm.validate_readable(broken_symlink)


class TestValidateInputDir:
    """Test input directory validation."""

    def test_should_validate_and_resolve_input_dir(self, tmp_path):
        """Test validating input directory."""
        input_dir = tmp_path / "input"
        input_dir.mkdir()
        pm = PathManager(base_path=str(tmp_path))

        result = pm.validate_input_dir("input")

        assert result == input_dir

    def test_should_raise_error_on_missing_input_dir(self, tmp_path):
        """Test error on missing input directory."""
        pm = PathManager(base_path=str(tmp_path))

        with pytest.raises(PathError):
            pm.validate_input_dir("nonexistent")

    def test_should_raise_error_if_input_is_file(self, tmp_path):
        """Test error when input path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        pm = PathManager(base_path=str(tmp_path))

        with pytest.raises(PathError):
            pm.validate_input_dir("file.txt")


class TestValidateOutputDir:
    """Test output directory validation and creation."""

    def test_should_validate_and_create_output_dir(self, tmp_path):
        """Test creating output directory."""
        output_dir = "output"
        pm = PathManager(base_path=str(tmp_path))

        result = pm.validate_output_dir(output_dir, create=True)

        assert (tmp_path / output_dir).exists()
        assert result == tmp_path / output_dir

    def test_should_not_create_if_create_false(self, tmp_path):
        """Test that output dir not created when create=False."""
        pm = PathManager(base_path=str(tmp_path))

        result = pm.validate_output_dir("nonexistent", create=False)

        assert not (tmp_path / "nonexistent").exists()

    def test_should_raise_error_on_file_instead_of_dir(self, tmp_path):
        """Test error when output path is a file."""
        file_path = tmp_path / "file.txt"
        file_path.write_text("test")
        pm = PathManager(base_path=str(tmp_path))

        with pytest.raises(PathError):
            pm.validate_output_dir("file.txt", create=False)

    def test_should_create_nested_directories(self, tmp_path):
        """Test creating nested directory structure."""
        pm = PathManager(base_path=str(tmp_path))

        result = pm.validate_output_dir("level1/level2/level3", create=True)

        assert (tmp_path / "level1" / "level2" / "level3").exists()


class TestGetScreenshotFiles:
    """Test screenshot file discovery."""

    def test_should_find_jpg_files(self, tmp_path):
        """Test finding JPG files."""
        (tmp_path / "screenshot1.jpg").write_text("jpg1")
        (tmp_path / "screenshot2.jpg").write_text("jpg2")
        (tmp_path / "image.png").write_text("png")

        pm = PathManager()
        files = pm.get_screenshot_files(tmp_path, pattern="*.jpg")

        assert len(files) == 2
        assert all(f.suffix == ".jpg" for f in files)

    def test_should_return_sorted_files(self, tmp_path):
        """Test files returned in sorted order."""
        (tmp_path / "z_screenshot.jpg").write_text("")
        (tmp_path / "a_screenshot.jpg").write_text("")
        (tmp_path / "m_screenshot.jpg").write_text("")

        pm = PathManager()
        files = pm.get_screenshot_files(tmp_path, pattern="*.jpg")

        assert files[0].name == "a_screenshot.jpg"
        assert files[-1].name == "z_screenshot.jpg"

    def test_should_return_empty_list_on_no_matches(self, tmp_path):
        """Test empty list when no files match pattern."""
        (tmp_path / "image.png").write_text("")

        pm = PathManager()
        files = pm.get_screenshot_files(tmp_path, pattern="*.jpg")

        assert len(files) == 0

    def test_should_raise_error_on_nonexistent_directory(self):
        """Test error on nonexistent directory."""
        pm = PathManager()

        with pytest.raises(PathError):
            pm.get_screenshot_files(pm.resolve_path("/nonexistent"), pattern="*.jpg")


class TestCreateOutputStructure:
    """Test output directory structure creation."""

    def test_should_create_complete_structure(self, tmp_path):
        """Test creating complete output structure."""
        pm = PathManager(base_path=str(tmp_path))

        structure = pm.create_output_structure(str(tmp_path), tablet_size="7inch")

        assert "base" in structure
        assert "screenshots" in structure
        assert "logs" in structure
        assert structure["screenshots"].exists()

    def test_should_create_structure_for_10inch_tablet(self, tmp_path):
        """Test structure naming for 10-inch tablet."""
        pm = PathManager(base_path=str(tmp_path))

        structure = pm.create_output_structure(str(tmp_path), tablet_size="10inch")

        assert "tablet_10inch_screenshots" in str(structure["screenshots"])

    def test_should_create_structure_for_7inch_tablet(self, tmp_path):
        """Test structure naming for 7-inch tablet."""
        pm = PathManager(base_path=str(tmp_path))

        structure = pm.create_output_structure(str(tmp_path), tablet_size="7inch")

        assert "tablet_7inch_screenshots" in str(structure["screenshots"])
