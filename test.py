#!/usr/bin/env python3
"""Unit tests for the Nielsen library."""

import logging
import pathlib
import unittest
import unittest.util
from configparser import ConfigParser
from unittest import mock
from typing import Any

import nielsen.config
import nielsen.media

unittest.util._MAX_LENGTH = 2000

logger: logging.Logger = logging.getLogger("nielsen")
# logger.addHandler(logging.StreamHandler())
logger.setLevel(logging.DEBUG)


class TestConfig(unittest.TestCase):
    """Test the nielsen.config module."""

    def setUp(self):
        """Clear the config to avoid execution order complications."""

        self.config: ConfigParser = nielsen.config.config
        self.config.clear()

    def tearDown(self):
        """Clear the config to avoid execution order complications."""

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
            "library": str(pathlib.Path.home()),
            "logfile": "~/.local/log/nielsen/nielsen.log",
            "loglevel": "WARNING",
            "mode": "664",
            "organize": "True",
            "rename": "True",
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


class TestMedia(unittest.TestCase):
    """Test the nielsen.media.Media base class."""

    def setUp(self):
        """Prepare reference objects for tests."""

        self.config: ConfigParser = nielsen.config.config
        nielsen.config.load_config(pathlib.Path("fixtures/config.ini"))

        self.no_path: nielsen.media.Media = nielsen.media.Media()
        self.non_file_path: nielsen.media.Media = nielsen.media.TV(
            pathlib.Path("/dev/null")
        )
        self.good_path: nielsen.media.Media = nielsen.media.Media(
            pathlib.Path("fixtures/media.file")
        )

    def tearDown(self):
        """Clean up after each test."""

        self.config.clear()

    def test_init(self):
        """Test construction of new Media objects."""

        self.assertIsNone(self.no_path.path, "No path attribute set by default.")
        self.assertEqual(
            self.no_path.section, "media", "Section attribute based on type."
        )
        # The library attribute must be a path, but the default value isn't especially
        # important for generic Media objects.
        self.assertIsInstance(
            self.no_path.library, pathlib.Path, "Library attribute must be a Path."
        )
        self.assertTrue(
            self.no_path.library.is_absolute(), "Library should be an absolute path."
        )

    def test_infer(self):
        """Cannot use infer on the base Media class."""

        with self.assertRaises(NotImplementedError):
            self.good_path.infer()

    def test_get_section(self):
        """The section property should return a value based on the type."""

        self.assertEqual(
            self.no_path.section, "media", "The section should match the type name"
        )

    def test_set_section(self):
        """Set the section property."""

        existing_section: str = "unit tests"
        self.no_path.section = existing_section
        self.assertEqual(
            self.no_path.section,
            existing_section,
            "The section should match the existing section assigned to it",
        )

        new_section: str = "new section"
        self.no_path.section = new_section
        self.assertEqual(
            self.no_path.section,
            new_section,
            "The section should match the newly created section assigned to it",
        )
        self.assertTrue(
            self.config.has_section(new_section),
            "The new section should be added to the config",
        )

    def test_get_library(self):
        """Get the library property from the appropriate config section."""

        # Calling resolve on the Path we compare to also ensures the library property is
        # always an absolute path.
        self.assertEqual(
            self.no_path.library,
            self.config.getpath("media", "library").resolve(),  # type: ignore
            "Should match option from tv section of config.",
        )
        self.assertEqual(
            self.no_path.library,
            pathlib.Path("fixtures/media/").resolve(),
            "Should match known type-specific value.",
        )

    def test_set_library(self):
        """Set the library property."""

        temp_str: str = "/tmp/nielsen/media/"
        temp_path: pathlib.Path = pathlib.Path(temp_str)

        for value in [temp_str, temp_path]:
            with self.subTest(
                value=value,
                msg="Assigning a string or Path should result in the same Path",
            ):
                self.no_path.library = value
                self.assertEqual(self.no_path.library, temp_path)

        with self.assertRaises(
            TypeError, msg="Cannot set library to non-Path-like object."
        ):
            self.no_path.library = None  # type: ignore

    def test_organize_invalid_path(self):
        """Media with no path or a non-file path cannot be organized."""

        for media in [self.no_path, self.non_file_path]:
            with self.subTest(media=media), self.assertRaises(TypeError):
                media.organize()

    def test_organize_library_permission_error(self):
        """Library directory does not exist and cannot be created."""

        with self.assertRaises(
            PermissionError, msg="Cannot create directory for library"
        ), mock.patch("pathlib.Path.is_file") as mock_is_file, mock.patch(
            "pathlib.Path.is_dir"
        ) as mock_is_dir, mock.patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_is_file.return_value = True
            mock_is_dir.return_value = False
            mock_mkdir.side_effect = PermissionError()
            self.good_path.organize()

    def test_organize_library_not_a_directory_error(self):
        """Library path does not point to a directory."""

        with self.assertRaises(
            NotADirectoryError, msg="Library is not a directory"
        ), mock.patch("pathlib.Path.is_file") as mock_is_file, mock.patch(
            "pathlib.Path.is_dir"
        ) as mock_is_dir, mock.patch(
            "pathlib.Path.mkdir"
        ) as mock_mkdir:
            mock_is_file.return_value = True
            mock_is_dir.return_value = False
            mock_mkdir.side_effect = NotADirectoryError()
            self.good_path.organize()

    def test_organize_happy_path(self):
        """Organize file, set and return new path."""

        with mock.patch("pathlib.Path.is_file") as mock_is_file, mock.patch(
            "pathlib.Path.rename"
        ) as mock_rename:
            # Mock the existence of the file on disk to avoid creating and removing
            # files on every test.
            mock_is_file.return_value = True
            # Path.rename moves a file and returns the destination path passed as an
            # argument. Mock it by just returning the input argument.
            mock_rename.side_effect = lambda x: x

            library: pathlib.Path = pathlib.Path("fixtures/media/")
            self.good_path.library = library
            self.assertIsInstance(self.good_path.path, pathlib.Path)
            self.assertEqual(
                self.good_path.organize(),
                (library / self.good_path.path.name).resolve(),  # type: ignore
            )


class TestTV(unittest.TestCase):
    """Test the TV class."""

    def setUp(self):
        """Prepare reference objects for tests."""

        self.config: ConfigParser = nielsen.config.config
        nielsen.config.load_config(pathlib.Path("fixtures/config.ini"))

        self.wot_good_filename: nielsen.media.Media = nielsen.media.TV(
            pathlib.Path("The Wheel of Time -01.08- The Eye of the World.mkv")
        )
        self.wot_good_metadata: nielsen.media.Media = nielsen.media.TV(
            pathlib.Path("wot.mkv"),
            series="The Wheel of Time",
            season=1,
            episode=8,
            title="The Eye of the World",
        )
        self.wot_all_data: nielsen.media.Media = nielsen.media.TV(
            pathlib.Path("The Wheel of Time -01.08- The Eye of the World.mkv"),
            series="The Wheel of Time",
            season=1,
            episode=8,
            title="The Eye of the World",
        )

    def tearDown(self):
        """Clean up after each test."""

        self.config.clear()

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

        self.assertLess(
            nielsen.media.TV(None, season=1, episode=1),
            nielsen.media.TV(None, season=1, episode=2),
            "Same season, different episode numbers",
        )

        self.assertLess(
            nielsen.media.TV(None, season=1, episode=1),
            nielsen.media.TV(None, season=2, episode=1),
            "Different seasons, same episode number",
        )

        self.assertLess(
            nielsen.media.TV(None, season=1, episode=10),
            nielsen.media.TV(None, season=2, episode=2),
            "Different seasons and episode numbers",
        )

        self.assertEqual(
            nielsen.media.TV(None, season=1, episode=2),
            nielsen.media.TV(None, season=1, episode=2),
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

    def test_get_section(self):
        """The section property should return a value based on the type."""

        self.assertEqual(
            self.wot_all_data.section, "tv", "The section should match the type name"
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


if __name__ == "__main__":
    unittest.main()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
