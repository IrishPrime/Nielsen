"""Test the nielsen.config module."""

import pathlib

import pytest
from pytest_mock import MockType

import nielsen.config


@pytest.fixture
def config_file() -> pathlib.Path:
    """Return a Path object representing the location of the configuration file to be
    used with tests."""

    return pathlib.Path("fixtures/config.ini")


def test_load_config_no_arg_no_files(mocker):
    """Load only the default options."""

    # Mock the default files to avoid polluting the test with user configurations.
    mocker.patch("nielsen.config.CONFIG_FILE_LOCATIONS", new=[])
    assert nielsen.config.load_config() == [], "No files should be loaded."

    for option, value in nielsen.config.config.defaults().items():
        assert (
            nielsen.config.config.get("nielsen", option) == value
        ), "Arbitrary section should return all default values."


def test_load_config_specific_file(config_file):
    """Load config from a specific file."""

    files: list[str] = nielsen.config.load_config(config_file)
    assert files == ["fixtures/config.ini"]

    assert nielsen.config.config.has_section(
        "unit tests"
    ), "The config must have the section from the config file fixture."

    assert nielsen.config.config.get("unit tests", "foo") == "bar"


def test_load_config_missing_file(caplog):
    """Specify a missing configuration file to load."""

    file: pathlib.Path = pathlib.Path("fixtures/missing.ini")
    nielsen.config.load_config(file)
    assert f"Failed to load configuration from: {file}" in caplog.text


def test_write_config(mocker):
    """Write the config to a file."""

    # This function just calls the ConfigParser.write() method, so there's not much
    # for us to test. Ensure our function writes data to the specified file.
    file: pathlib.Path = pathlib.Path("fixtures/write-test.ini")
    mock_open: MockType = mocker.patch("builtins.open")
    mock_write: MockType = mocker.patch("configparser.ConfigParser.write")

    nielsen.config.write_config(file)
    mock_open.assert_called_with(file, mode="w")
    mock_write.assert_called_with(mock_open().__enter__())


def test_update_config(config_file, mocker):
    """Call load_config and write_config with the correct arguments."""

    mock_load_config: MockType = mocker.patch("nielsen.config.load_config")
    mock_write_config: MockType = mocker.patch("nielsen.config.write_config")
    nielsen.config.update_config(config_file)
    mock_load_config.assert_called_with(config_file)
    mock_write_config.assert_called_with(config_file)
