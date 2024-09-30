import pathlib
from configparser import ConfigParser
from typing import Any, Generator

import pytest

import nielsen.config


@pytest.fixture(autouse=True)
def config() -> Generator[ConfigParser, Any, Any]:
    """Fixture to load Nielsen configuration for tests."""

    nielsen.config.load_config(pathlib.Path("./fixtures/config.ini"))
    yield nielsen.config.config
    # Clear all options between uses
    nielsen.config.config.clear()


@pytest.fixture
def missing_file() -> pathlib.Path:
    return pathlib.Path("fixtures/media/missing.file")
