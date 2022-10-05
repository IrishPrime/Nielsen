#!/usr/bin/env python3
"""Unit tests for the Nielsen library."""

import logging
import pathlib
import unittest
from configparser import ConfigParser
from unittest import mock

import nielsen.config

logger: logging.Logger = logging.getLogger("nielsen")
logger.addHandler(logging.NullHandler())
logger.setLevel(logging.DEBUG)


class TestConfig(unittest.TestCase):
    """Test the nielsen.config module."""

    def setUp(self):
        """Empty the config before each test."""

        self.config: ConfigParser = nielsen.config.config
        self.config.clear()

    @mock.patch("nielsen.config.config.read")
    def test_load_config_no_arg_no_files(self, mock_read):
        """Load only the default options."""

        # Mock the default files to avoid polluting the test with user configurations.
        mock_read.return_value = []
        with self.assertLogs("nielsen.config", logging.DEBUG) as cm:
            nielsen.config.load_config()
            self.assertEqual(
                "Loaded configuration from default locations: []", cm.records[0].message
            )

        self.assertListEqual(
            self.config.sections(), [], "The config should have no sections."
        )

        defaults: dict[str, str] = {
            "dryrun": "False",
            "fetch": "True",
            "filter": "True",
            "interactive": "True",
            "logfile": "~/.local/log/nielsen/nielsen.log",
            "loglevel": "WARNING",
            "mediapath": str(pathlib.Path.home()),
            "mode": "664",
            "organize": "True",
        }

        self.config.add_section("test section")
        for option, value in defaults.items():
            with self.subTest(option=option, value=value):
                self.assertEqual(
                    self.config.get("test section", option),
                    value,
                    "Arbitrary section should return all default values.",
                )

    def test_load_config_specific_file(self):
        """Load config from a specific file."""

        with self.assertLogs("nielsen.config", logging.DEBUG) as cm:
            config = nielsen.config.load_config(pathlib.Path("fixtures/config.ini"))
            self.assertEqual(
                "Loaded configuration from: ['fixtures/config.ini']",
                cm.records[0].message,
            )

        self.assertTrue(
            config.has_section("unit tests"),
            "The config must have the section from the config file fixture.",
        )
        self.assertEqual(config.get("unit tests", "foo"), "bar")

    def test_load_config_missing_file(self):
        """Specify a missing configuration file to load."""

        file: pathlib.Path = pathlib.Path("fixtures/missing.ini")
        with self.assertLogs("nielsen.config", logging.ERROR) as cm:
            self.config = nielsen.config.load_config(file)
            self.assertEqual(
                f"Failed to load configuration from: {file}",
                cm.records[0].message,
            )

    def test_write_config(self):
        """Write the config to a file."""

        # This function just calls the ConfigParser.write() method, so there's not much
        # for us to test. Ensure our function writes data to the specified file.
        file: pathlib.Path = pathlib.Path("fixtures/write-test.ini")
        file.unlink(missing_ok=True)  # Start with a clean slate
        self.assertFalse(file.exists(), f"{file} must not exist before writing.")
        nielsen.config.write_config(file)
        self.assertTrue(file.is_file(), f"{file} must exist as a file after writing.")
        self.assertGreater(
            file.stat().st_size, 100, f"{file} must have some data in it."
        )


if __name__ == "__main__":
    unittest.main()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
