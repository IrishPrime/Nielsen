"""Test the nielsen.media.Media base class."""

import pathlib
import re
from typing import Any

import pytest
from pytest_mock import MockType

import nielsen.config
import nielsen.media


@pytest.fixture
def good_path() -> nielsen.media.Media:
    """Return a Media object with a valid file path."""

    return nielsen.media.Media(pathlib.Path("fixtures/media.file"))


@pytest.fixture
def missing_file() -> nielsen.media.Media:
    """Return a Media object with no file at the specified path."""

    return nielsen.media.Media(pathlib.Path("fixtures/media/missing.file"))


@pytest.fixture
def non_file_path() -> nielsen.media.Media:
    """Return a Media object with a non-file path."""

    return nielsen.media.Media(pathlib.Path("/dev/null"))


@pytest.fixture
def medias(good_path, missing_file, non_file_path) -> list[nielsen.media.Media]:
    return [
        good_path,
        missing_file,
        non_file_path,
    ]


def test_init(good_path) -> None:
    """Test construction of new Media objects."""

    invalid_paths: list[Any] = [None, False, 0, ""]
    for item in invalid_paths:
        with pytest.raises(TypeError):
            nielsen.media.Media(item)

    assert good_path.section == "media", "Section attribute based on type."

    # The library attribute must be a path, but the default value isn't especially
    # important for generic Media objects.
    assert isinstance(
        good_path.library, pathlib.Path
    ), "Library attribute must be a Path."

    assert good_path.library.is_absolute(), "Library should be an absolute path."


def test_infer_no_patterns(caplog, good_path) -> None:
    """Cannot infer information about an object with no patterns to match."""

    good_path.infer()
    assert "NO_PATTERNS" in caplog.text, "Log an error when inferring without patterns"


def test_match_no_match(good_path) -> None:
    """Return an empty metadata dictionary and log a NO_MATCH message."""

    # Add a pattern just to ensure that the match reaches it and fails to match.
    good_path.patterns = [re.compile(r"USELESS_PATTERN")]

    assert good_path._match() == {}, "Return an empty dictionary."


def test_get_library(good_path) -> None:
    """Get the library property from the appropriate config section."""

    # Calling resolve on the Path we compare to also ensures the library property is
    # always an absolute path.
    assert (
        good_path.library == nielsen.config.config.getpath("media", "library").resolve()  # type: ignore
    ), "Should match option from tv section of config."
    assert (
        good_path.library == pathlib.Path("fixtures/media/").resolve()
    ), "Should match known type-specific value."


def test_get_metadata(good_path) -> None:
    """Method not implemented for base Media class."""

    with pytest.raises(NotImplementedError):
        good_path.metadata


def test_get_orgdir(medias) -> None:
    """Media base objects have no orgdir property."""

    for media in medias:
        with pytest.raises(NotImplementedError):
            media.orgdir


def test_get_path(medias) -> None:
    """Get the path property of the Media object."""

    for media in medias:
        assert isinstance(media.path, pathlib.Path), "Must be a Path object."


def test_get_patterns(medias) -> None:
    """Media base objects have no patterns."""

    for media in medias:
        assert media.patterns == [], "List of patterns must be empty for Media type"


def test_get_section(medias) -> None:
    """The section property should return a value based on the type."""

    for media in medias:
        assert (
            media.section == "media"
        ), "The section should match the type name, but lowercase"


def test_organize_invalid_path(non_file_path) -> None:
    """Media with no path or a non-file path cannot be organized."""

    with pytest.raises(TypeError):
        non_file_path.organize()


def test_organize_library_not_a_directory_error(good_path, mocker) -> None:
    """Library path does not point to a directory."""

    mock_is_file: MockType = mocker.patch("pathlib.Path.is_file")
    mock_is_dir: MockType = mocker.patch("pathlib.Path.is_dir")
    mock_mkdir: MockType = mocker.patch("pathlib.Path.mkdir")

    mock_is_file.return_value = True
    mock_is_dir.return_value = False
    mock_mkdir.side_effect = NotADirectoryError()

    with pytest.raises(NotADirectoryError):
        good_path.organize()


def test_organize_library_permission_error(good_path, mocker) -> None:
    """Library directory does not exist and cannot be created."""

    mock_is_file: MockType = mocker.patch("pathlib.Path.is_file")
    mock_is_dir: MockType = mocker.patch("pathlib.Path.is_dir")
    mock_mkdir: MockType = mocker.patch("pathlib.Path.mkdir")

    mock_is_file.return_value = True
    mock_is_dir.return_value = False
    mock_mkdir.side_effect = PermissionError()

    with pytest.raises(PermissionError):
        good_path.organize()


def test_organize_pass_guards(good_path, mocker) -> None:
    """Pass the guard clauses, but fail because Media has no orgdir."""

    mock_is_file: MockType = mocker.patch("pathlib.Path.is_file")
    mock_move: MockType = mocker.patch("shutil.move")

    # Mock the existence of the file on disk to avoid creating and removing
    # files on every test.
    mock_is_file.return_value = True
    # shutil.move moves a file and returns the destination path passed as an
    # argument. Mock it by just returning the input argument.
    mock_move.return_value = lambda x: x

    assert isinstance(good_path.path, pathlib.Path)

    with pytest.raises(NotImplementedError):
        good_path.organize()


def test_rename_file_not_found(good_path, mocker) -> None:
    """Raise an exception when renaming base Media objects."""

    mock_exists: MockType = mocker.patch("pathlib.Path.exists")
    mock_exists.return_value = False

    with pytest.raises(FileNotFoundError):
        good_path.rename()


def test_str(good_path) -> None:
    """String representation should just be a file path."""

    assert str(good_path) == str(good_path.path.resolve())


def test_set_metadata(good_path) -> None:
    """Method not implemented for base Media class."""

    with pytest.raises(NotImplementedError):
        good_path.metadata = {}


def test_set_section(non_file_path) -> None:
    """Set the section property."""

    assert non_file_path.section == "media", "The section should match the type"

    # Set a new section so the change can be verified
    existing_section: str = "unit tests"
    non_file_path.section = existing_section
    assert (
        non_file_path.section == existing_section
    ), "The section should match the existing section assigned to it"

    new_section: str = "new section"
    assert not nielsen.config.config.has_section(
        new_section
    ), "New section should not yet exist"

    non_file_path.section = new_section
    assert (
        non_file_path.section == new_section
    ), "The section should match the newly created section assigned to it"
    assert nielsen.config.config.has_section(
        new_section
    ), "The new section should be added to the config"


@pytest.mark.parametrize(
    "location",
    [
        pytest.param("fixtures/media/", id="string"),
        pytest.param(pathlib.Path("fixtures/media/"), id="path"),
    ],
)
def test_set_library(good_path, location) -> None:
    """Set the library property to valid paths."""

    good_path.library = location
    assert isinstance(good_path.library, pathlib.Path)
    assert good_path.library.is_dir()


@pytest.mark.parametrize(
    "location",
    [
        pytest.param(None, id="none"),
        pytest.param(0, id="zero"),
        pytest.param(False, id="false"),
        pytest.param("/dev/null", id="non-file string"),
        pytest.param(pathlib.Path("/dev/null"), id="non-file path"),
    ],
)
def test_set_library_invalid(good_path, location) -> None:
    """Set the library property to invalid paths."""

    with pytest.raises(TypeError):
        good_path.library = location


@pytest.mark.parametrize(
    "path",
    [
        pytest.param("fixtures/media.file", id="string"),
        pytest.param(pathlib.Path("fixtures/media.file"), id="path"),
    ],
)
def test_set_path(path) -> None:
    """Set the path property of a Media object."""

    media: nielsen.media.Media = nielsen.media.Media(path)
    assert isinstance(media.path, pathlib.Path)
    assert media.path.is_file()

    with pytest.raises(TypeError):
        media.path = None  # type: ignore
