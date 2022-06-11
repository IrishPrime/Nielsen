#!/usr/bin/env python3
"""Unit tests for the Nielsen library."""

import logging
import pathlib
import unittest
from configparser import ConfigParser
from unittest import mock
from typing import Any

import nielsen.config
import nielsen.media

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


class TestTV(unittest.TestCase):
    """Test the TV class."""

    def setUp(self):
        """Prepare references objects for tests."""

        self.wot_good_filename: nielsen.media.Media = nielsen.media.TV(
            "The Wheel of Time -01.08- The Eye of the World.mkv"
        )
        self.wot_good_metadata: nielsen.media.Media = nielsen.media.TV(
            "wot.mkv",
            series="The Wheel of Time",
            season=1,
            episode=8,
            title="The Eye of the World",
        )
        self.wot_all_data: nielsen.media.Media = nielsen.media.TV(
            "The Wheel of Time -01.08- The Eye of the World.mkv",
            series="The Wheel of Time",
            season=1,
            episode=8,
            title="The Eye of the World",
        )

    def test_init(self):
        """Type conversion from the base class should happen in the subclass, as well."""

        falsey: list[Any] = [None, False, 0, ""]
        for item in falsey:
            with self.subTest("Falsey path values should convert to None", item=item):
                tv_none_path: nielsen.media.TV = nielsen.media.TV(item)
                self.assertIsNone(tv_none_path.path)

        valid_paths: list[nielsen.media.Media] = [
            self.wot_good_filename,
            self.wot_good_metadata,
            self.wot_all_data,
        ]
        for item in valid_paths:
            with self.subTest("Paths and strings should become paths", item=item):
                self.assertIsInstance(item.path, pathlib.Path)

    def test_ordering(self):
        """Items should be sorted by season, then episode number."""

        self.assertGreater(
            nielsen.media.TV(None, season=1, episode=2),
            nielsen.media.TV(None, season=1, episode=1),
            "Same season, different episode numbers",
        )

        self.assertGreater(
            nielsen.media.TV("Show -02.01- Title.mkv", season=2, episode=1),
            nielsen.media.TV("Show -01.01- Title.mkv", season=1, episode=1),
            "Different seasons, same episode number",
        )

        self.assertGreater(
            nielsen.media.TV(None, season=2, episode=2),
            nielsen.media.TV(None, season=1, episode=10),
            "Different seasons and episode numbers",
        )

        self.assertLessEqual(
            nielsen.media.TV(None, season=3, episode=4),
            nielsen.media.TV(None, season=3, episode=4),
            "Same season and episode number",
        )

        self.assertGreaterEqual(
            nielsen.media.TV(None, season=4, episode=5),
            nielsen.media.TV(None, season=4, episode=5),
            "Same season and episode number",
        )

        self.assertEqual(
            nielsen.media.TV(None, season=4, episode=5),
            nielsen.media.TV(None, season=4, episode=5),
            "Same season and episode number",
        )

    def test_str(self):
        """The string representation should provide a useful display name."""

        self.assertEqual(
            "The Wheel of Time -01.08- The Eye of the World",
            str(self.wot_all_data),
            "TV object with all data",
        )
        self.assertEqual(
            "The Wheel of Time -01.08- The Eye of the World",
            str(self.wot_good_metadata),
            "TV object with all metadata",
        )

    def test_infer(self):
        """A descriptive filename should populate the metadata."""

        self.assertNotEqual(
            self.wot_good_filename,
            self.wot_all_data,
            "Objects should differ before infer is called",
        )
        self.wot_good_filename.infer()
        self.assertEqual(
            self.wot_good_filename,
            self.wot_all_data,
            "Objects should be identical after infer is called",
        )

    def test_organize(self):
        """Organizing an object should return its new path."""

        self.assertEqual(
            pathlib.Path(f"/tmp/organized/{self.wot_all_data}"),
            self.wot_all_data.organize(),
        )


if __name__ == "__main__":
    unittest.main()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
