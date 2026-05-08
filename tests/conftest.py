import pathlib
from configparser import ConfigParser
from typing import Any, Generator

import pytest

import nielsen.config


@pytest.fixture
def media_library(tmp_path: pathlib.Path) -> pathlib.Path:
    """Real directory under tmp_path used as the [media] library."""

    d = tmp_path / "media"
    d.mkdir()
    return d


@pytest.fixture
def tv_library(tmp_path: pathlib.Path) -> pathlib.Path:
    """Real directory under tmp_path used as the [tv] library."""

    d = tmp_path / "tv"
    d.mkdir()
    return d


@pytest.fixture
def media_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Real, empty file under tmp_path that tests can use as a Media path."""

    f = tmp_path / "media.file"
    f.touch()
    return f


@pytest.fixture(autouse=True)
def config(
    tmp_path: pathlib.Path,
    media_library: pathlib.Path,
    tv_library: pathlib.Path,
) -> Generator[ConfigParser, Any, Any]:
    """Load Nielsen configuration backed by tmp_path-rooted libraries."""

    # Build the test config from the canonical fixture, but redirect every
    # `library` path to a tmp_path-rooted directory so tests never read or
    # write real on-disk fixtures.
    parser: ConfigParser = ConfigParser()
    parser.read(pathlib.Path("fixtures/config.ini"))
    for section in ("nielsen", "media", "tv"):
        if not parser.has_section(section):
            parser.add_section(section)
    parser["nielsen"]["library"] = str(tmp_path)
    parser["media"]["library"] = str(media_library)
    parser["tv"]["library"] = str(tv_library)

    config_file: pathlib.Path = tmp_path / "config.ini"
    with config_file.open("w") as f:
        parser.write(f)

    nielsen.config.load_config(config_file)
    yield nielsen.config.config
    nielsen.config.config.clear()


@pytest.fixture
def missing_file(tmp_path: pathlib.Path) -> pathlib.Path:
    """Path under tmp_path that is guaranteed not to exist."""

    return tmp_path / "missing" / "file"
