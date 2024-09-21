#!/usr/bin/env python3

"""Unit tests for the Nielsen library."""

import logging
import pathlib
import pickle
import re
import unittest
import unittest.util
from configparser import ConfigParser
from unittest import mock
from typing import Any, Pattern

import requests

import nielsen.config
import nielsen.fetcher
import nielsen.media
import nielsen.processor

unittest.util._MAX_LENGTH = 2048

logger: logging.Logger = logging.getLogger("nielsen")
logger.setLevel(logging.NOTSET)


class TestConfig(unittest.TestCase):
    """Test the nielsen.config module."""

    def setUp(self):
        """Clear the config to avoid execution order complications."""

        self.CONFIG_FILE: pathlib.Path = pathlib.Path("fixtures/config.ini")
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
            "simulate": "False",
            "fetch": "True",
            "transform": "True",
            "interactive": "True",
            "library": str(pathlib.Path.home()),
            "logfile": "~/.local/log/nielsen/nielsen.log",
            "loglevel": "WARNING",
            "mode": "644",
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

        files: list[str] = nielsen.config.load_config(self.CONFIG_FILE)
        self.assertListEqual(files, ["fixtures/config.ini"])

        self.assertTrue(
            nielsen.config.config.has_section("unit tests"),
            "The config must have the section from the config file fixture.",
        )
        self.assertEqual(nielsen.config.config.get("unit tests", "foo"), "bar")

    def test_load_config_missing_file(self):
        """Specify a missing configuration file to load."""

        file: pathlib.Path = pathlib.Path("fixtures/missing.ini")
        with self.assertLogs("nielsen.config", logging.ERROR) as cm:
            nielsen.config.load_config(file)
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

    @mock.patch("nielsen.config.load_config")
    @mock.patch("nielsen.config.write_config")
    def test_update_config(
        self, mock_write_config: mock.Mock, mock_load_config: mock.Mock
    ):
        """Call load_config and write_config with the correct arguments."""

        nielsen.config.update_config(self.CONFIG_FILE)
        mock_load_config.assert_called_with(self.CONFIG_FILE)
        mock_write_config.assert_called_with(self.CONFIG_FILE)


class TestMedia(unittest.TestCase):
    """Test the nielsen.media.Media base class."""

    def setUp(self):
        """Prepare reference objects for tests."""

        self.config: ConfigParser = nielsen.config.config
        nielsen.config.load_config(pathlib.Path("fixtures/config.ini"))

        self.good_path: nielsen.media.Media = nielsen.media.Media(
            pathlib.Path("fixtures/media.file")
        )
        self.missing_file: nielsen.media.Media = nielsen.media.Media(
            pathlib.Path("fixtures/media/missing.file")
        )
        self.non_file_path: nielsen.media.Media = nielsen.media.Media(
            pathlib.Path("/dev/null")
        )
        self.medias: list[nielsen.media.Media] = [
            self.good_path,
            self.missing_file,
            self.non_file_path,
        ]

    def tearDown(self):
        """Clean up after each test."""

        self.config.clear()

    def test_init(self):
        """Test construction of new Media objects."""

        invalid_paths: list[Any] = [None, False, 0, ""]
        for item in invalid_paths:
            with self.subTest(
                "Falsey path values should convert to None", item=item
            ), self.assertRaises(TypeError):
                invalid_path: nielsen.media.Media = nielsen.media.Media(item)

        self.assertEqual(
            self.good_path.section, "media", "Section attribute based on type."
        )
        # The library attribute must be a path, but the default value isn't especially
        # important for generic Media objects.
        self.assertIsInstance(
            self.good_path.library, pathlib.Path, "Library attribute must be a Path."
        )
        self.assertTrue(
            self.good_path.library.is_absolute(), "Library should be an absolute path."
        )

    def test_infer_no_patterns(self):
        """Cannot infer information about an object with no patterns to match."""

        with self.assertLogs("nielsen.media", logging.ERROR) as cm:
            self.good_path.infer()
            self.assertTrue(
                cm.records[0].msg.startswith("NO_PATTERNS"),
                "Log an error when inferring without patterns",
            )

    def test_match_no_match(self):
        """Return an empty metadata dictionary and log a NO_MATCH message."""

        # Add a pattern just to ensure that the match reaches it and fails to match.
        self.good_path.patterns = [re.compile("USELESS_PATTERN")]

        with self.assertLogs("nielsen.media", logging.INFO) as cm:
            self.assertDictEqual(
                {}, self.good_path._match(), "Return an empty dictionary."
            )
            self.assertTrue(
                cm.records[0].msg.startswith("NO_MATCH"), "Log a NO_MATCH message"
            )

    def test_get_metadata(self):
        """Method not implemented for base Media class."""

        with self.assertRaises(NotImplementedError):
            self.good_path.metadata

    def test_set_metadata(self):
        """Method not implemented for base Media class."""

        with self.assertRaises(NotImplementedError):
            self.good_path.metadata = {}

    def test_get_section(self):
        """The section property should return a value based on the type."""

        for media in self.medias:
            with self.subTest(media=media):
                self.assertEqual(
                    media.section,
                    "media",
                    "The section should match the type name, but lowercase",
                )

    def test_set_section(self):
        """Set the section property."""

        self.assertEqual(
            self.non_file_path.section, "media", "The section should match the type"
        )
        # Set a new section so the change can be verified
        existing_section: str = "unit tests"
        self.non_file_path.section = existing_section
        self.assertEqual(
            self.non_file_path.section,
            existing_section,
            "The section should match the existing section assigned to it",
        )

        new_section: str = "new section"
        self.assertFalse(
            self.config.has_section(new_section), "New section should not yet exist"
        )
        self.non_file_path.section = new_section
        self.assertEqual(
            self.non_file_path.section,
            new_section,
            "The section should match the newly created section assigned to it",
        )
        self.assertTrue(
            self.config.has_section(new_section),
            "The new section should be added to the config",
        )

    def test_get_path(self):
        """Get the path property of the Media object."""

        for media in self.medias:
            with self.subTest(media=media):
                self.assertIsInstance(
                    media.path, pathlib.Path, "Must be a Path object."
                )

    def test_set_path(self):
        """Set the path property of a Media object."""

        temp_str: str = "fixtures/media.file"
        temp_path: pathlib.Path = pathlib.Path(temp_str)
        temp_path.touch(mode=644, exist_ok=True)

        for value in [temp_str, temp_path]:
            with self.subTest(
                "Assigning a string or Path should result in the same Path",
                item=value,
            ):
                media: nielsen.media.Media = nielsen.media.Media(value)
                self.assertIsInstance(media.path, pathlib.Path)
                self.assertTrue(media.path.samefile(temp_path))
                self.assertTrue(media.path.is_file())

        with self.assertRaises(
            TypeError, msg="Cannot set path to non-PathLike object."
        ):
            media.path = None  # type: ignore

    def test_get_library(self):
        """Get the library property from the appropriate config section."""

        # Calling resolve on the Path we compare to also ensures the library property is
        # always an absolute path.
        self.assertEqual(
            self.good_path.library,
            self.config.getpath("media", "library").resolve(),  # type: ignore
            "Should match option from tv section of config.",
        )
        self.assertEqual(
            self.good_path.library,
            pathlib.Path("fixtures/media/").resolve(),
            "Should match known type-specific value.",
        )

    def test_set_library(self):
        """Set the library property."""

        temp_str: str = "fixtures/media/"
        temp_path: pathlib.Path = pathlib.Path(temp_str)

        for value in [temp_str, temp_path]:
            with self.subTest(
                "Assigning a string or Path should result in the same Path",
                item=value,
            ):
                self.non_file_path.library = value
                self.assertIsInstance(self.non_file_path.library, pathlib.Path)
                self.assertTrue(self.non_file_path.library.samefile(temp_path))
                self.assertTrue(self.non_file_path.library.is_dir())

        invalid_paths: list[Any] = [None, False, 0, "/dev/null"]
        for item in invalid_paths:
            with self.subTest(
                "The library must be a PathLike object representing a directory.",
                item=item,
            ), self.assertRaises(TypeError):
                self.non_file_path.library = item

    def test_get_patterns(self):
        """Media base objects have no patterns."""

        for media in self.medias:
            with self.subTest(
                "List of patterns must be empty for Media type", item=media
            ):
                self.assertListEqual([], media.patterns)

    def test_get_orgdir(self):
        """Media base objects have no orgdir property."""

        with self.assertRaises(NotImplementedError):
            for media in self.medias:
                media.orgdir

    def test_organize_invalid_path(self):
        """Media with no path or a non-file path cannot be organized."""

        with self.assertRaises(TypeError):
            self.non_file_path.organize()

    def test_organize_library_permission_error(self):
        """Library directory does not exist and cannot be created."""

        with self.assertRaises(
            PermissionError, msg="Cannot create directory for library"
        ), mock.patch("pathlib.Path.is_file") as mock_is_file, mock.patch(
            "pathlib.Path.is_dir"
        ) as mock_is_dir, mock.patch("pathlib.Path.mkdir") as mock_mkdir:
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
        ) as mock_is_dir, mock.patch("pathlib.Path.mkdir") as mock_mkdir:
            mock_is_file.return_value = True
            mock_is_dir.return_value = False
            mock_mkdir.side_effect = NotADirectoryError()
            self.good_path.organize()

    def test_organize_pass_guards(self):
        """Pass the guard clauses, but fail because Media has no orgdir."""

        with mock.patch("pathlib.Path.is_file") as mock_is_file, mock.patch(
            "shutil.move"
        ) as mock_move:
            # Mock the existence of the file on disk to avoid creating and removing
            # files on every test.
            mock_is_file.return_value = True
            # shutil.move moves a file and returns the destination path passed as an
            # argument. Mock it by just returning the input argument.
            mock_move.side_effect = lambda x: x

            self.assertIsInstance(self.good_path.path, pathlib.Path)

            with self.assertRaises(NotImplementedError):
                self.good_path.organize()

    def test_rename(self):
        """Raise an exception when renaming base Media objects."""

        with self.assertRaises(FileNotFoundError):
            self.missing_file.rename()

    def test_str(self) -> None:
        """String representation should just be a file path."""

        self.assertEqual(
            str(self.good_path), str(pathlib.Path("fixtures/media.file").resolve())
        )


class TestTV(unittest.TestCase):
    """Test the TV class."""

    def setUp(self):
        """Prepare reference objects for tests."""

        self.config: ConfigParser = nielsen.config.config
        nielsen.config.load_config(pathlib.Path("fixtures/config.ini"))
        self.missing_file: pathlib.Path = pathlib.Path("fixtures/media/missing.file")

        self.tv_good_filename: nielsen.media.Media = nielsen.media.TV(
            pathlib.Path("Ted Lasso -01.03- Trent Crimm: The Independent.mkv")
        )
        self.tv_good_metadata: nielsen.media.Media = nielsen.media.TV(
            pathlib.Path("tv.mkv"),
            series="Ted Lasso",
            season=1,
            episode=3,
            title="Trent Crimm: The Independent",
        )
        self.tv_good_metadata_missing_file: nielsen.media.Media = nielsen.media.TV(
            self.missing_file,
            series="Ted Lasso",
            season=1,
            episode=3,
            title="Trent Crimm: The Independent",
        )
        self.tv_all_data: nielsen.media.Media = nielsen.media.TV(
            pathlib.Path("Ted Lasso -01.03- Trent Crimm: The Independent.mkv"),
            series="Ted Lasso",
            season=1,
            episode=3,
            title="Trent Crimm: The Independent",
        )

        self.tvs: list[nielsen.media.Media] = [
            self.tv_good_filename,
            self.tv_good_metadata,
            self.tv_good_metadata_missing_file,
            self.tv_all_data,
        ]

    def tearDown(self):
        """Clean up after each test."""

        self.config.clear()

    def test_init(self):
        """Type conversion from the base class should happen in the subclass, as well."""

        valid_paths: list[nielsen.media.Media] = [
            self.tv_good_filename,
            self.tv_good_metadata,
            self.tv_all_data,
        ]
        for item in valid_paths:
            with self.subTest("Paths and strings should become paths", item=item):
                self.assertIsInstance(item.path, pathlib.Path)

    def test_get_metadata(self):
        """Return a dictionary with all the relevant fields."""

        self.assertDictEqual(
            {
                "series": "Ted Lasso",
                "season": 1,
                "episode": 3,
                "title": "Trent Crimm: The Independent",
            },
            self.tv_good_metadata.metadata,
        )

    def test_set_metadata(self):
        """Set the metadata dictionary."""

        metadata: dict[str, Any] = {
            "series": "Ted Lasso",
            "season": 1,
            "episode": 3,
            "title": "Trent Crimm: The Independent",
        }
        self.tv_good_filename.metadata = metadata

        self.assertDictEqual(metadata, self.tv_good_filename.metadata)

    def test_get_patterns(self):
        """TV objects should have a list of patterns."""

        for tv in self.tvs:
            with self.subTest(tv=tv):
                self.assertIsInstance(tv.patterns, list)
                for pattern in tv.patterns:
                    with self.subTest(pattern=pattern):
                        self.assertIsInstance(pattern, Pattern)

    def test_get_section(self):
        """The section property should return a value based on the type."""

        self.assertEqual(
            self.tv_all_data.section,
            "tv",
            "The section should match the type name, but lowercase",
        )

    def test_get_orgdir(self):
        """The orgdir should be the library, series name, then season."""

        self.assertEqual(
            pathlib.Path("fixtures/tv/Ted Lasso/Season 01/").resolve(),
            self.tv_all_data.orgdir,
        )

    def test_infer_basic(self):
        """A descriptive filename should populate the metadata."""

        self.assertNotEqual(
            self.tv_good_filename,
            self.tv_all_data,
            "Objects should differ before infer is called",
        )
        self.tv_good_filename.infer()
        self.assertEqual(
            self.tv_good_filename,
            self.tv_all_data,
            "Objects should be identical after infer is called",
        )

    def test_infer_all_patterns(self):
        """Test every pattern and difficult edge cases."""

        media: dict[str, dict[str, str | int]] = {
            # Not quite formatted correctly for TV
            "Something.Close.12.mp4": {
                "series": "",
                "season": 0,
                "episode": 0,
                "title": "",
            },
            # Very nicely formatted
            "The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi": {
                "series": "The Glades",
                "season": 2,
                "episode": 1,
                "title": "Family Matters",
            },
            # Needs title casing
            "the.glades.s02e01.family.matters.hdtv.xvid-fqm.avi": {
                "series": "The Glades",
                "season": 2,
                "episode": 1,
                "title": "Family Matters",
            },
            # Missing title
            "The.Glades.S02E01.HDTV.XviD-FQM.avi": {
                "series": "The Glades",
                "season": 2,
                "episode": 1,
                "title": "",
            },
            # Already processed by nielsen
            "The Glades -02.01- Family Matters.avi": {
                "series": "The Glades",
                "season": 2,
                "episode": 1,
                "title": "Family Matters",
            },
            # Another common post-processing format
            "The Glades -201- Family Matters.avi": {
                "series": "The Glades",
                "season": 2,
                "episode": 1,
                "title": "Family Matters",
            },
            # Four digit season/episode code, fewer hyphens
            "Firefly 0101 - Serenity.mkv": {
                "series": "Firefly",
                "season": 1,
                "episode": 1,
                "title": "Serenity",
            },
            # Has most necessary information, but formatted strangely
            "Supernatural.S10E15.mp4": {
                "series": "Supernatural",
                "season": 10,
                "episode": 15,
                "title": "",
            },
            # Same as above, but with an extra dot between season and episode
            "Pushing.Daisies.S02.E03.mp4": {
                "series": "Pushing Daisies",
                "season": 2,
                "episode": 3,
                "title": "",
            },
            # Nicely formatted, but with an apostrophe in the title
            "Person.of.Interest.S0310.The.Devil's.Share.HDTV.avi": {
                "series": "Person of Interest",
                "season": 3,
                "episode": 10,
                "title": "The Devil's Share",
            },
            # Ensure title casing with the apostrophe works well
            "person.of.interest.s03e10.the.devil's.share.hdtv.avi": {
                "series": "Person of Interest",
                "season": 3,
                "episode": 10,
                "title": "The Devil's Share",
            },
            # Testing WEB-RiP tag and series filtering
            "Castle.(2009).S07E18.At.Close.Range.720p.WEB-RiP.mp4": {
                "series": "Castle",
                "season": 7,
                "episode": 18,
                "title": "At Close Range",
            },
            # Same as above, but with all fields
            "Castle.(2009).S01E01.Flowers.for.Your.Grave.720p.WEB-RiP.mp4": {
                "series": "Castle",
                "season": 1,
                "episode": 1,
                "title": "Flowers For Your Grave",
            },
            # Four digit season and episode combination
            "supernatural.1117.red.meat.hdtv-lol[ettv].mp4": {
                "series": "Supernatural",
                "season": 11,
                "episode": 17,
                "title": "Red Meat",
            },
            # Specifying file within a directory
            "supernatural.1117.hdtv-lol[ettv]/supernatural.1117.red.meat.hdtv-lol[ettv].mp4": {
                "series": "Supernatural",
                "season": 11,
                "episode": 17,
                "title": "Red Meat",
            },
            # Four digit year followed by three digit season and episode combination
            "the.flash.(2014).217.flash.back.hdtv-lol[ettv].mp4": {
                "series": "The Flash",
                "season": 2,
                "episode": 17,
                "title": "Flash Back",
            },
            # Four digit year with season and episode markers
            "The.Flash.2014.S02E17.Flash.Back.HDTV.x264-LOL[ettv].mp4": {
                "series": "The Flash",
                "season": 2,
                "episode": 17,
                "title": "Flash Back",
            },
            # Four digit year followed by three digit season and episode combination
            "The.Flash.2014.217.Flash.Back.HDTV.x264-LOL[ettv].mp4": {
                "series": "The Flash",
                "season": 2,
                "episode": 17,
                "title": "Flash Back",
            },
            # Tag removal
            "Game.of.Thrones.S06E07.The.Broken.Man.1080p.HDTV.6CH.ShAaNiG.mkv": {
                "series": "Game of Thrones",
                "season": 6,
                "episode": 7,
                "title": "The Broken Man",
            },
            # File in a subdirectory
            "Game.of.Thrones.S07E01.720p.HDTV.x264-AVS[rarbg]/Game.of.Thrones.S07E01.Dragonstone.720p.HDTV.x264-AVS.mkv": {
                "series": "Game of Thrones",
                "season": 7,
                "episode": 1,
                "title": "Dragonstone",
            },
            # Single episode with what looks like a second episode marker in the title
            "Sample.Show.S01E01.E19.Protocol.720p.HDTV.X264-DIMENSION.mkv": {
                "series": "Sample Show",
                "season": 1,
                "episode": 1,
                "title": "E19 Protocol",
            },
            # Unusual filename for last ditch effort pattern
            "Limitless S01E11 This Is Your Brian on Drugs (1080p x265 Joy).mkv": {
                "series": "Limitless",
                "season": 1,
                "episode": 11,
                "title": "This Is Your Brian On Drugs",
            },
            "What.If.2021.S02E08.What.if.the.Avengers.Assembled.in.1602.1080p.DSNP.WEB-DL.DDP5.1.Atmos.H.264-FLUX.mkv": {
                "series": "What If",
                "season": 2,
                "episode": 8,
                "title": "What If The Avengers Assembled In 1602",
            },
        }

        for filename, metadata in media.items():
            tv: nielsen.media.TV = nielsen.media.TV(pathlib.Path(filename))
            with self.subTest(
                "Inferred metadata mismatch", tv=tv, metadata=metadata
            ), mock.patch("pathlib.Path.exists") as mock_exists:
                mock_exists.return_value = True
                tv.infer()
                self.assertDictEqual(tv.metadata, metadata)

    def test_ordering(self):
        """Items should be sorted by season, then episode number."""

        self.assertLess(
            nielsen.media.TV(self.missing_file, season=1, episode=1),
            nielsen.media.TV(self.missing_file, season=1, episode=2),
            "Same season, different episode numbers",
        )

        self.assertLess(
            nielsen.media.TV(self.missing_file, season=1, episode=1),
            nielsen.media.TV(self.missing_file, season=2, episode=1),
            "Different seasons, same episode number",
        )

        self.assertLess(
            nielsen.media.TV(self.missing_file, season=1, episode=10),
            nielsen.media.TV(self.missing_file, season=2, episode=2),
            "Different seasons and episode numbers",
        )

        self.assertEqual(
            nielsen.media.TV(self.missing_file, season=1, episode=2),
            nielsen.media.TV(self.missing_file, season=1, episode=2),
            "Same season and episode number",
        )

    def test_rename_file_not_found(self):
        """Rename a TV object with no path or an invalid path."""

        tvs: list[nielsen.media.Media] = [
            self.tv_good_metadata_missing_file,
            self.tv_good_metadata,
        ]

        for tv in tvs:
            with self.subTest("TV with a bad path", tv=tv):
                with self.assertRaises(
                    FileNotFoundError, msg="Missing files cannot be renamed."
                ):
                    self.tv_good_metadata_missing_file.rename()

    @mock.patch("pathlib.Path.samefile")
    @mock.patch("pathlib.Path.exists")
    def test_rename_file_exists(self, mock_exists, mock_same):
        """Rename a TV object where the destination already exists."""

        mock_exists.return_value = True
        mock_same.return_value = False
        with self.assertLogs("nielsen", logging.INFO) as cm:
            self.tv_good_metadata.rename()
            self.assertIn("FILE_CONFLICT", cm.records[1].getMessage())

        mock_same.return_value = True
        with self.assertLogs("nielsen", logging.INFO) as cm:
            self.tv_good_metadata.rename()
            self.assertIn("File already named correctly.", cm.records[1].getMessage())

    def test_rename(self):
        """Rename a file without moving it to a different directory."""

        # Ensure we have a fixed point for the intended destination.
        dest: pathlib.Path = pathlib.Path(
            "Ted Lasso -01.03- Trent Crimm: The Independent.mkv"
        ).resolve()
        # Ensure the destination file does not exist before running other tests.
        dest.unlink(missing_ok=True)
        self.assertFalse(dest.exists())

        # Create the base file
        self.assertIsInstance(self.tv_good_metadata.path, pathlib.Path)
        self.tv_good_metadata.path.unlink(missing_ok=True)
        self.tv_good_metadata.path.touch(exist_ok=False)

        # Rename the base file
        self.assertTrue(
            dest.samefile(self.tv_good_metadata.rename()),
            "Paths should match.",
        )

        assert self.tv_all_data.path
        self.assertTrue(self.tv_all_data.path.exists())
        self.tv_all_data.path.unlink()

    @mock.patch("nielsen.media.chown")
    @mock.patch("nielsen.media.move")
    @mock.patch("pathlib.Path.chmod")
    @mock.patch("pathlib.Path.is_file")
    def test_organize_success(self, mock_is_file, mock_chmod, mock_move, mock_chown):
        """Organize file, set and return new path."""

        # Mock the existence of the file on disk to avoid creating and removing
        # files on every test.
        mock_is_file.return_value = True

        # shutil.move moves a file and returns the destination path passed as an
        # argument. Mock it by just returning the input argument.
        mock_move.side_effect = lambda _, org: org

        self.assertIsInstance(self.tv_all_data.path, pathlib.Path)
        self.assertEqual(
            self.tv_all_data.organize(),
            pathlib.Path(
                "fixtures/tv/Ted Lasso/Season 01/Ted Lasso -01.03- Trent Crimm: The Independent.mkv"
            ).resolve(),
        )

        # The pathlib.Path.chmod and shutil.chown functions can be assumed to work properly,
        # we just need to assert that they were called with the correct values.
        mock_chmod.assert_called_with(0o644)
        mock_chown.assert_called_with(
            self.tv_all_data.path, "nielsen_user", "nielsen_group"
        )

    def test_transform(self):
        """Transform series names based on values from the tv/series/transform config section."""

        # Marvel's Agents of S.H.I.E.L.D. has many variants in the way the series name
        # might be listed. Which variant you prefer is a matter of personal preference
        # and can be configured, but once configured they should all resolve to the same
        # user-preferred variant.
        variants: list[str] = [
            "Marvel's Agents of S.H.I.E.L.D.",
            "Marvel's Agents of S H I E L D ",
            "Marvel's Agents of SHIELD",
            "Agents of S.H.I.E.L.D.",
            "Agents of S H I E L D ",
            "Agents of SHIELD",
        ]

        self.config.clear()
        self.config.add_section("tv/transform/series")
        for variant in variants:
            with self.subTest(variant=variant):
                self.config.set("tv/transform/series", variant, "Agents of SHIELD")
                shield: nielsen.media.Media = nielsen.media.TV(
                    self.missing_file, series=variant, season=1, episode=1
                )
                self.assertEqual(
                    "Agents of SHIELD",
                    shield.transform("series"),
                    "Series name should be transformed to match",
                )

    def test_transform_no_section(self):
        """Log a warning and return the input if no config section found."""

        self.config.clear()

        with self.assertLogs("nielsen", logging.WARNING) as cm:
            self.tv_all_data.transform("series")
            self.assertIn("NO_TRANSFORM_SECTION", cm.records[0].getMessage())

    def test_transform_no_option(self):
        """Log a warning and return the input if no config option found."""

        self.config.clear()
        self.config.add_section("tv/transform/series")
        with self.assertLogs("nielsen", logging.WARNING) as cm:
            self.tv_all_data.transform("series")
            self.assertIn("NO_TRANSFORM_OPTION", cm.records[0].getMessage())

    def test_repr(self):
        """Object representation should contain enough information to recreate an object."""

        path: pathlib.Path = pathlib.Path(
            "Ted Lasso -01.03- Trent Crimm: The Independent.mkv"
        ).resolve()
        series: str = "Ted Lasso"
        season: int = 1
        episode: int = 3
        title: str = "Trent Crimm: The Independent"
        expected: str = f"<TV(self.{path=}, self.{series=}, self.{season=}, self.{episode=}, self.{title=})>"

        self.assertEqual(expected, repr(self.tv_all_data))

    def test_str(self):
        """The string representation should provide a useful display name."""

        string: str = "Ted Lasso -01.03- Trent Crimm: The Independent"

        self.assertEqual(
            string,
            str(self.tv_all_data),
            "TV object with all data",
        )
        self.assertEqual(
            string,
            str(self.tv_good_metadata),
            "TV object with all metadata",
        )
        self.assertEqual(
            string,
            str(self.tv_good_metadata_missing_file),
            "TV object with all metadata",
        )
        self.assertEqual(
            "Unknown -00.00- Unknown",
            str(self.tv_good_filename),
            "TV object with no metadata, but good filename",
        )


class TestTVMaze(unittest.TestCase):
    """Tests for the TVMaze Fetcher."""

    def setUp(self):
        """Prepare reference objects for tests."""

        self.config: ConfigParser = nielsen.config.config
        nielsen.config.load_config(pathlib.Path("fixtures/config.ini"))
        self.missing_path: pathlib.Path = pathlib.Path("fixtures/media/missing.file")

        self.fetcher: nielsen.fetcher.TVMaze = nielsen.fetcher.TVMaze()
        self.ted_lasso: nielsen.media.TV = nielsen.media.TV(
            self.missing_path,
            series="Ted Lasso",
        )
        self.ted_lasso_id: int = 44458
        self.agents_of_shield: nielsen.media.TV = nielsen.media.TV(
            pathlib.Path("fixtures/media/missing.file"),
            series="Agents of SHIELD",
        )
        self.agents_of_shield_id: int = 31

    def tearDown(self):
        """Clean up after each test."""

        self.config.clear()

    def test_get_series_id_local(self):
        """Get series ID from local config file."""

        # Use a Mock to assert the right function was called by get_series_id.
        self.fetcher.get_series_id_local = mock.MagicMock(
            side_effect=self.fetcher.get_series_id_local
        )

        self.assertEqual(
            self.fetcher.get_series_id(self.ted_lasso.series),
            self.ted_lasso_id,
            "Should get ID from config file",
        )
        self.fetcher.get_series_id_local.assert_called()

    @mock.patch("requests.get")
    def test_get_series_id_remote_single(self, mock_get: mock.Mock):
        """Get series ID from TVMaze API with single result."""

        # Clear the config to ensure the series isn't found locally
        self.config.clear()

        # Load test fixture with actual API results
        resp_ok: requests.Response = pickle.loads(
            pathlib.Path(
                "fixtures/tv/singlesearch/shows-q-ted+lasso.pickle"
            ).read_bytes()
        )

        # Use a Mock to assert the right function was called by get_series_id.
        self.fetcher.get_series_id_singlesearch = mock.MagicMock(
            side_effect=self.fetcher.get_series_id_singlesearch
        )

        mock_get.return_value = resp_ok
        self.assertEqual(
            self.fetcher.get_series_id(self.ted_lasso.series),
            self.ted_lasso_id,
            "Should get ID from TVMaze response",
        )
        self.fetcher.get_series_id_singlesearch.assert_called_once()

        # Ensure a bad response returns a 0 for the Series ID
        resp_not_ok: requests.Response = requests.Response()
        resp_not_ok: requests.Response = pickle.loads(
            pathlib.Path(
                "fixtures/tv/singlesearch/shows-q-useless+search+string.pickle"
            ).read_bytes()
        )
        self.fetcher.get_series_id_singlesearch.reset_mock()
        mock_get.return_value = resp_not_ok
        self.assertEqual(
            self.fetcher.get_series_id_singlesearch(self.ted_lasso.series),
            0,
            "Should return 0 on a 'not ok' TVMaze response",
        )
        self.fetcher.get_series_id_singlesearch.assert_called_once()

    @mock.patch("builtins.input")
    @mock.patch("requests.get")
    def test_get_series_id_remote_multiple(
        self, mock_get: mock.Mock, mock_input: mock.Mock
    ):
        """Get series ID from TVMaze API with multiple results."""

        mock_input.return_value = "1"
        fixtures: list[dict[str, Any]] = [
            {
                "id": self.agents_of_shield_id,
                "media": self.agents_of_shield,
                "pickle": "fixtures/tv/search/shows-q-agents+of+shield.pickle",
            },
            {
                "id": self.ted_lasso_id,
                "media": self.ted_lasso,
                "pickle": "fixtures/tv/search/shows-q-ted+lasso.pickle",
            },
            {
                "id": 0,
                "media": nielsen.media.TV(
                    self.missing_path, series="Useless Search String"
                ),
                "pickle": "fixtures/tv/search/shows-q-useless+search+string.pickle",
            },
        ]

        for fixture in fixtures:
            # Clear the config to ensure the series isn't found locally.
            self.config.clear()

            with self.subTest(fixture=fixture):
                # Use a Mock to assert the right function was called by get_series_id.
                self.fetcher.get_series_id_search = mock.MagicMock(
                    side_effect=self.fetcher.get_series_id_search
                )

                # Load test fixture with actual API results.
                resp: requests.models.Response = pickle.loads(
                    pathlib.Path(fixture["pickle"]).read_bytes()
                )

                mock_get.return_value = resp

                self.assertEqual(
                    self.fetcher.get_series_id(
                        series=fixture["media"].series, interactive=True
                    ),
                    fixture["id"],
                    "Should get ID from TVMaze response",
                )

                self.fetcher.get_series_id_search.assert_called_with(
                    fixture["media"].series
                )

    @mock.patch("requests.get")
    def test_get_episode_title(self, mock_get):
        """Get the episode title for a given series, season, and episode number."""

        self.ted_lasso.season = 1
        self.ted_lasso.episode = 3
        title: str = "Trent Crimm: The Independent"

        mock_get.return_value = pickle.loads(
            pathlib.Path(
                "fixtures/tv/shows/44458/episodebynumber-season-1-number-3.pickle"
            ).read_bytes()
        )

        self.assertEqual(self.fetcher.get_episode_title(self.ted_lasso), title)

    @mock.patch("nielsen.fetcher.TVMaze.get_series_id")
    def test_get_episode_title_errors(self, mock_series_id):
        """Raise errors when insufficient information to search for episode titles."""

        mock_series_id.return_value = None

        empty: nielsen.media.TV = nielsen.media.TV(self.missing_path)
        with self.assertRaises(ValueError):
            self.fetcher.get_episode_title(empty)

        mock_series_id.return_value = 42
        with self.assertRaises(ValueError):
            self.fetcher.get_episode_title(empty)

        empty.season = 1
        with self.assertRaises(ValueError):
            self.fetcher.get_episode_title(empty)

    def test_set_series_id(self):
        """Create a mapping between a series name and a TVMaze series ID."""

        series: str = "Foo: The Series"
        id: int = 42

        # Clear the config to ensure things work properly even when there is no section
        # for TVMaze IDs.
        self.config.clear()

        self.assertFalse(
            self.config.has_option(self.fetcher.IDS, series),
            "The option should not exist before setting.",
        )

        self.fetcher.set_series_id(series, id)
        self.assertTrue(
            self.config.has_option(self.fetcher.IDS, series),
            "The section and option should both exist after setting.",
        )

    def test_fetch(self):
        """Fetch and update metadata using information from the given `Media` object."""

        self.assertEqual(self.ted_lasso.title, "", "Title should be empty.")

        self.ted_lasso.season = 1
        self.ted_lasso.episode = 3
        self.fetcher.fetch(self.ted_lasso)

        self.assertEqual(
            self.ted_lasso.title,
            "Trent Crimm: The Independent",
            "Title should be correctly set after fetching.",
        )

    @mock.patch("nielsen.fetcher.TVMaze.get_series_id")
    def test_fetch_no_series_id(self, mock_series_id):
        """Fetch and update metadata using information from the given `Media` object."""

        mock_series_id.return_value = 0

        with self.assertRaises(ValueError):
            self.fetcher.fetch(self.ted_lasso)

    @mock.patch("requests.get")
    def test_get_season_id(self, mock_get):
        """Verify the GET request and response handling."""

        mock_get.return_value = pickle.loads(
            pathlib.Path(
                f"fixtures/tv/shows/{self.ted_lasso_id}/seasons-.pickle"
            ).read_bytes()
        )
        season_id: int = self.fetcher.get_season_id(self.ted_lasso_id, 2)
        mock_get.assert_called_with(
            f"{self.fetcher.SERVICE}/shows/{self.ted_lasso_id}/seasons"
        )

        assert season_id == 112939  # Ted Lasso Season 2 ID

    @mock.patch("requests.get")
    def test_get_season_id_no_match(self, mock_get):
        """Verify the GET request and response handling."""

        mock_get.return_value.json.return_value = {}
        season_id: int = self.fetcher.get_season_id(self.ted_lasso_id, 0)

        assert season_id == 0

    @mock.patch("requests.get")
    def test_episodebynumber(self, mock_get):
        """Verify the GET request and response handling."""

        mock_get.return_value = pickle.loads(
            pathlib.Path(
                f"fixtures/tv/shows/{self.ted_lasso_id}/episodebynumber-season-1-number-3.pickle"
            ).read_bytes()
        )

        self.fetcher.episodebynumber("Ted Lasso", 1, 3)
        mock_get.assert_called_with(
            f"{self.fetcher.SERVICE}/shows/{self.ted_lasso_id}/episodebynumber?season=1&number=3"
        )

    def test_episodebynumber_no_series_id(self):
        """Raise a ValueError if the series ID is invalid."""

        with self.assertRaises(ValueError):
            self.fetcher.episodebynumber(0, 0, 0)

    @mock.patch("requests.get")
    def test_seasons_episodes(self, mock_get):
        """Verify the GET request and response handling."""

        season_id: int = 112939  # Ted Lasso Season 2 ID

        mock_get.return_value = pickle.loads(
            pathlib.Path(
                f"fixtures/tv/seasons/{season_id}/episodes-.pickle"
            ).read_bytes()
        )

        self.fetcher.seasons_episodes(season_id)
        mock_get.assert_called_with(
            f"{self.fetcher.SERVICE}/seasons/{season_id}/episodes"
        )

    @mock.patch("requests.get")
    def test_shows(self, mock_get):
        """Verify the GET request and response handling."""

        self.fetcher.shows(self.ted_lasso_id)
        mock_get.assert_called_with(f"{self.fetcher.SERVICE}/shows/{self.ted_lasso_id}")

    def test_pick_series_network(self):
        pass

    def test_pick_series_streaming(self):
        pass

    @mock.patch("builtins.input")
    def test_pick_series_minimal(self, mock_input):
        """Pick a series with minimal information. Unlikely to happen, but should
        account for incomplete information returned from TVMaze."""

        # Mock a search result with incomplete data
        minimal_result: dict[str, Any] = {
            "show": {
                "name": "Unit Test",
                "id": 12345,
                "premiered": "2024-08-30",
            }
        }

        # Select the only result
        mock_input.return_value = 1

        self.assertDictEqual(
            self.fetcher.pick_series("Unit Test", [minimal_result]), minimal_result
        )

    @mock.patch("builtins.input")
    def test_pick_series_default(self, mock_input):
        """Pick a series with unparseable information."""

        unparseable_result: dict[str, Any] = {
            "Invalid": "Form",
        }

        # Select the only result
        mock_input.return_value = 1

        self.assertDictEqual(
            self.fetcher.pick_series("Invalid Results", [unparseable_result]),
            unparseable_result,
        )

    def test_pretty_series(self):
        """Return a nicely formatted series for the picker."""

        # Sample return from the /shows/:id endpoint
        # https://api.tvmaze.com/shows/44458
        data: dict[Any, Any] = {
            "id": 44458,
            "url": "https://www.tvmaze.com/shows/44458/ted-lasso",
            "name": "Ted Lasso",
            "type": "Scripted",
            "language": "English",
            "genres": ["Drama", "Comedy", "Sports"],
            "status": "Running",
            "runtime": None,
            "averageRuntime": 42,
            "premiered": "2020-08-14",
            "ended": None,
            "officialSite": "https://tv.apple.com/show/ted-lasso/umc.cmc.vtoh0mn0xn7t3c643xqonfzy",
            "schedule": {"time": "", "days": ["Wednesday"]},
            "rating": {"average": 8.1},
            "weight": 99,
            "network": None,
            "webChannel": {
                "id": 310,
                "name": "Apple TV+",
                "country": None,
                "officialSite": "https://tv.apple.com/",
            },
            "dvdCountry": None,
            "externals": {"tvrage": None, "thetvdb": 383203, "imdb": "tt10986410"},
            "image": {
                "medium": "https://static.tvmaze.com/uploads/images/medium_portrait/457/1142533.jpg",
                "original": "https://static.tvmaze.com/uploads/images/original_untouched/457/1142533.jpg",
            },
            "summary": "<p><b>Ted Lasso </b>centers on an idealistic — and clueless — all-American football coach hired to manage an English football club — despite having no soccer coaching experience at all.</p>",
            "updated": 1724535610,
            "_links": {
                "self": {"href": "https://api.tvmaze.com/shows/44458"},
                "previousepisode": {
                    "href": "https://api.tvmaze.com/episodes/2490079",
                    "name": "So Long, Farewell",
                },
            },
        }

        self.assertEqual(
            nielsen.fetcher.TVMaze.pretty_series(data),
            (
                "Ted Lasso - ID: 44458 - https://www.tvmaze.com/shows/44458/ted-lasso\n"
                "Premiered: 2020-08-14 - Status: Running\n"
                "Ted Lasso centers on an idealistic — and clueless — all-American football coach hired to manage an English football club — despite having no soccer coaching experience at all."
            ),
        )

    def test_pretty_season(self):
        """Return a nicely formatted season for the picker."""

        # Sample output from the /seasons/:id/episodes endpoint
        # https://api.tvmaze.com/seasons/112939/episodes
        data: list[dict[Any, Any]] = [
            {
                "id": 2075166,
                "url": "https://www.tvmaze.com/episodes/2075166/ted-lasso-2x01-goodbye-earl",
                "name": "Goodbye Earl",
                "season": 2,
                "number": 1,
                "type": "regular",
                "airdate": "2021-07-23",
                "airtime": "",
                "airstamp": "2021-07-23T12:00:00+00:00",
                "runtime": 34,
                "rating": {"average": 7.8},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/341/852868.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/341/852868.jpg",
                },
                "summary": "<p>AFC Richmond brings in a sports psychologist to help the team overcome their unprecedented seven game tie-streak.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2075166"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2132225,
                "url": "https://www.tvmaze.com/episodes/2132225/ted-lasso-2x02-lavender",
                "name": "Lavender",
                "season": 2,
                "number": 2,
                "type": "regular",
                "airdate": "2021-07-30",
                "airtime": "",
                "airstamp": "2021-07-30T12:00:00+00:00",
                "runtime": 33,
                "rating": {"average": 7.9},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/341/852869.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/341/852869.jpg",
                },
                "summary": "<p>Ted is surprised by the reappearance of a familiar face. Roy tries out a new gig.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2132225"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2138281,
                "url": "https://www.tvmaze.com/episodes/2138281/ted-lasso-2x03-do-the-right-est-thing",
                "name": "Do the Right-est Thing",
                "season": 2,
                "number": 3,
                "type": "regular",
                "airdate": "2021-08-06",
                "airtime": "",
                "airstamp": "2021-08-06T12:00:00+00:00",
                "runtime": 36,
                "rating": {"average": 8},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/344/862256.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/344/862256.jpg",
                },
                "summary": "<p>Rebecca has a special visitor shadow her at work. A player's return is not welcomed by the team.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2138281"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2142664,
                "url": "https://www.tvmaze.com/episodes/2142664/ted-lasso-2x04-carol-of-the-bells",
                "name": "Carol of the Bells",
                "season": 2,
                "number": 4,
                "type": "regular",
                "airdate": "2021-08-13",
                "airtime": "",
                "airstamp": "2021-08-13T12:00:00+00:00",
                "runtime": 30,
                "rating": {"average": 8.5},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/346/866045.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/346/866045.jpg",
                },
                "summary": "<p>It's Christmas in Richmond. Rebecca enlists Ted for a secret mission, Roy and Keeley search for a miracle, and the Higginses open up their home.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2142664"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2147114,
                "url": "https://www.tvmaze.com/episodes/2147114/ted-lasso-2x05-rainbow",
                "name": "Rainbow",
                "season": 2,
                "number": 5,
                "type": "regular",
                "airdate": "2021-08-20",
                "airtime": "",
                "airstamp": "2021-08-20T12:00:00+00:00",
                "runtime": 38,
                "rating": {"average": 8.3},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/348/871312.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/348/871312.jpg",
                },
                "summary": "<p>Nate learns how to be assertive from Keeley and Rebecca. Ted asks Roy for a favor.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2147114"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2151080,
                "url": "https://www.tvmaze.com/episodes/2151080/ted-lasso-2x06-the-signal",
                "name": "The Signal",
                "season": 2,
                "number": 6,
                "type": "regular",
                "airdate": "2021-08-27",
                "airtime": "",
                "airstamp": "2021-08-27T12:00:00+00:00",
                "runtime": 35,
                "rating": {"average": 8},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/350/875535.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/350/875535.jpg",
                },
                "summary": "<p>Ted is fired up that the new team dynamic seems to be working. But will they have a chance in the semifinal?</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2151080"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2156168,
                "url": "https://www.tvmaze.com/episodes/2156168/ted-lasso-2x07-headspace",
                "name": "Headspace",
                "season": 2,
                "number": 7,
                "type": "regular",
                "airdate": "2021-09-03",
                "airtime": "",
                "airstamp": "2021-09-03T12:00:00+00:00",
                "runtime": 35,
                "rating": {"average": 7.6},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/352/880559.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/352/880559.jpg",
                },
                "summary": "<p>With things turning around for Richmond, it's time for everyone to work on their issues—like Ted's discomfort, Nate's confidence, and Roy's attention.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2156168"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2161174,
                "url": "https://www.tvmaze.com/episodes/2161174/ted-lasso-2x08-man-city",
                "name": "Man City",
                "season": 2,
                "number": 8,
                "type": "regular",
                "airdate": "2021-09-10",
                "airtime": "",
                "airstamp": "2021-09-10T12:00:00+00:00",
                "runtime": 45,
                "rating": {"average": 8.1},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/353/884734.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/353/884734.jpg",
                },
                "summary": "<p>Ted and Dr. Sharon realize they might have to meet each other halfway. Tensions are high as the team prepares for the semifinal.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2161174"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2166305,
                "url": "https://www.tvmaze.com/episodes/2166305/ted-lasso-2x09-beard-after-hours",
                "name": "Beard After Hours",
                "season": 2,
                "number": 9,
                "type": "regular",
                "airdate": "2021-09-17",
                "airtime": "",
                "airstamp": "2021-09-17T12:00:00+00:00",
                "runtime": 43,
                "rating": {"average": 6.9},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/356/890404.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/356/890404.jpg",
                },
                "summary": "<p>After the semifinal, Beard sets out on an all-night odyssey through London in an effort to collect his thoughts.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2166305"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2172163,
                "url": "https://www.tvmaze.com/episodes/2172163/ted-lasso-2x10-no-weddings-and-a-funeral",
                "name": "No Weddings and a Funeral",
                "season": 2,
                "number": 10,
                "type": "regular",
                "airdate": "2021-09-24",
                "airtime": "",
                "airstamp": "2021-09-24T12:00:00+00:00",
                "runtime": 46,
                "rating": {"average": 7.6},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/357/894799.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/357/894799.jpg",
                },
                "summary": "<p>Rebecca is stunned by a sudden loss. The team rallies to show their support, but Ted finds himself grappling with a piece of his past.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2172163"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2172941,
                "url": "https://www.tvmaze.com/episodes/2172941/ted-lasso-2x11-midnight-train-to-royston",
                "name": "Midnight Train to Royston",
                "season": 2,
                "number": 11,
                "type": "regular",
                "airdate": "2021-10-01",
                "airtime": "",
                "airstamp": "2021-10-01T12:00:00+00:00",
                "runtime": 42,
                "rating": {"average": 7.8},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/360/900284.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/360/900284.jpg",
                },
                "summary": "<p>A billionaire football enthusiast from Ghana makes Sam an unbelievable offer. Ted plans something special for Dr. Sharon's last day with the team.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2172941"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
            {
                "id": 2172942,
                "url": "https://www.tvmaze.com/episodes/2172942/ted-lasso-2x12-inverting-the-pyramid-of-success",
                "name": "Inverting the Pyramid of Success",
                "season": 2,
                "number": 12,
                "type": "regular",
                "airdate": "2021-10-08",
                "airtime": "",
                "airstamp": "2021-10-08T12:00:00+00:00",
                "runtime": 49,
                "rating": {"average": 8},
                "image": {
                    "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/362/905367.jpg",
                    "original": "https://static.tvmaze.com/uploads/images/original_untouched/362/905367.jpg",
                },
                "summary": "<p>Richmond gets their final chance to win promotion as Ted deals with the fallout of Trent Crimm's painfully honest exposé.</p>",
                "_links": {
                    "self": {"href": "https://api.tvmaze.com/episodes/2172942"},
                    "show": {
                        "href": "https://api.tvmaze.com/shows/44458",
                        "name": "Ted Lasso",
                    },
                },
            },
        ]

        self.assertEqual(
            nielsen.fetcher.TVMaze.pretty_season(data),
            (
                "2x1 - Goodbye Earl\n"
                "https://www.tvmaze.com/episodes/2075166/ted-lasso-2x01-goodbye-earl\n"
                "AFC Richmond brings in a sports psychologist to help the team overcome their unprecedented seven game tie-streak.\n\n"
                "2x2 - Lavender\n"
                "https://www.tvmaze.com/episodes/2132225/ted-lasso-2x02-lavender\n"
                "Ted is surprised by the reappearance of a familiar face. Roy tries out a new gig.\n\n"
                "2x3 - Do the Right-est Thing\n"
                "https://www.tvmaze.com/episodes/2138281/ted-lasso-2x03-do-the-right-est-thing\n"
                "Rebecca has a special visitor shadow her at work. A player's return is not welcomed by the team.\n\n"
                "2x4 - Carol of the Bells\n"
                "https://www.tvmaze.com/episodes/2142664/ted-lasso-2x04-carol-of-the-bells\n"
                "It's Christmas in Richmond. Rebecca enlists Ted for a secret mission, Roy and Keeley search for a miracle, and the Higginses open up their home.\n\n"
                "2x5 - Rainbow\n"
                "https://www.tvmaze.com/episodes/2147114/ted-lasso-2x05-rainbow\n"
                "Nate learns how to be assertive from Keeley and Rebecca. Ted asks Roy for a favor.\n\n"
                "2x6 - The Signal\n"
                "https://www.tvmaze.com/episodes/2151080/ted-lasso-2x06-the-signal\n"
                "Ted is fired up that the new team dynamic seems to be working. But will they have a chance in the semifinal?\n\n"
                "2x7 - Headspace\n"
                "https://www.tvmaze.com/episodes/2156168/ted-lasso-2x07-headspace\n"
                "With things turning around for Richmond, it's time for everyone to work on their issues—like Ted's discomfort, Nate's confidence, and Roy's attention.\n\n"
                "2x8 - Man City\n"
                "https://www.tvmaze.com/episodes/2161174/ted-lasso-2x08-man-city\n"
                "Ted and Dr. Sharon realize they might have to meet each other halfway. Tensions are high as the team prepares for the semifinal.\n\n"
                "2x9 - Beard After Hours\n"
                "https://www.tvmaze.com/episodes/2166305/ted-lasso-2x09-beard-after-hours\n"
                "After the semifinal, Beard sets out on an all-night odyssey through London in an effort to collect his thoughts.\n\n"
                "2x10 - No Weddings and a Funeral\n"
                "https://www.tvmaze.com/episodes/2172163/ted-lasso-2x10-no-weddings-and-a-funeral\n"
                "Rebecca is stunned by a sudden loss. The team rallies to show their support, but Ted finds himself grappling with a piece of his past.\n\n"
                "2x11 - Midnight Train to Royston\n"
                "https://www.tvmaze.com/episodes/2172941/ted-lasso-2x11-midnight-train-to-royston\n"
                "A billionaire football enthusiast from Ghana makes Sam an unbelievable offer. Ted plans something special for Dr. Sharon's last day with the team.\n\n"
                "2x12 - Inverting the Pyramid of Success\n"
                "https://www.tvmaze.com/episodes/2172942/ted-lasso-2x12-inverting-the-pyramid-of-success\n"
                "Richmond gets their final chance to win promotion as Ted deals with the fallout of Trent Crimm's painfully honest exposé."
            ),
        )

    def test_pretty_episode(self):
        """Return a nicely formatted episode for the picker."""

        # Sample output from the /shows/:id/episodebynumber?season=:season&number=:number endpoint
        # https://api.tvmaze.com/shows/44458/episodebynumber?season=3&number=4
        data: dict[str, Any] = {
            "id": 2490069,
            "url": "https://www.tvmaze.com/episodes/2490069/ted-lasso-3x04-big-week",
            "name": "Big Week",
            "season": 3,
            "number": 4,
            "type": "regular",
            "airdate": "2023-04-05",
            "airtime": "",
            "airstamp": "2023-04-05T12:00:00+00:00",
            "runtime": 49,
            "rating": {"average": 7.4},
            "image": {
                "medium": "https://static.tvmaze.com/uploads/images/medium_landscape/454/1135656.jpg",
                "original": "https://static.tvmaze.com/uploads/images/original_untouched/454/1135656.jpg",
            },
            "summary": "\u003cp\u003eEveryone's feeling the pressure as Richmond gear up to play West Ham. Ted is reunited with an old friend.\u003c/p\u003e",
            "_links": {
                "self": {"href": "https://api.tvmaze.com/episodes/2490069"},
                "show": {
                    "href": "https://api.tvmaze.com/shows/44458",
                    "name": "Ted Lasso",
                },
            },
        }

        self.assertEqual(
            nielsen.fetcher.TVMaze.pretty_episode(data),
            (
                "3x4 - Big Week\n"
                "https://www.tvmaze.com/episodes/2490069/ted-lasso-3x04-big-week\n"
                "Everyone's feeling the pressure as Richmond gear up to play West Ham. Ted is reunited with an old friend."
            ),
        )


class TestProcessor(unittest.TestCase):
    """Tests for the nielsen.processor module."""

    def setUp(self):
        """Prepare reference objects for tests."""

        self.config: ConfigParser = nielsen.config.config
        nielsen.config.load_config(pathlib.Path("fixtures/config.ini"))

    def test_processor_init(self):
        """Test construction of new Processor objects."""

        processor: nielsen.processor.Processor = nielsen.processor.Processor(
            nielsen.media.Media, nielsen.fetcher.TVMaze()
        )

        assert hasattr(processor, "media_type")
        assert hasattr(processor, "fetcher")
        assert issubclass(processor.media_type, nielsen.media.Media)
        assert isinstance(processor.fetcher, nielsen.fetcher.TVMaze)

    def test_processor_factory_init(self):
        """Test construction of new ProcessorFactory objects."""

        factory: nielsen.processor.ProcessorFactory = (
            nielsen.processor.ProcessorFactory(
                nielsen.media.Media, nielsen.fetcher.TVMaze
            )
        )

        assert hasattr(factory, "media_type")
        assert hasattr(factory, "fetcher")
        assert issubclass(factory.media_type, nielsen.media.Media)
        # factory.fetcher must be a subclass of Fetcher, but not an instance of it
        assert issubclass(factory.fetcher, nielsen.fetcher.TVMaze)
        assert not isinstance(factory.fetcher, nielsen.fetcher.TVMaze)

    def test_processor_factory_call(self):
        """Calling the Factory should return a Processor."""

        factory: nielsen.processor.ProcessorFactory = (
            nielsen.processor.ProcessorFactory(nielsen.media.TV, nielsen.fetcher.TVMaze)
        )

        processor: nielsen.processor.Processor = factory()
        assert isinstance(processor, nielsen.processor.Processor)

    def test_processor_process(self):
        """The process method should call all other high-level Media/Fetcher functions."""

        # This test should be expanded as more Media and Fetcher types are added
        mock_fetcher: mock.Mock = mock.Mock(spec_set=nielsen.fetcher.TVMaze)
        processor: nielsen.processor.Processor = nielsen.processor.Processor(
            nielsen.media.TV, mock_fetcher
        )

        with mock.patch("nielsen.media.Media.rename") as mock_rename, mock.patch(
            "nielsen.media.Media.organize"
        ) as mock_organize:
            media_path: pathlib.Path = pathlib.Path(
                "ted.lasso.s01e01.1080p.web.h264-ggwp"
            )
            # Disable side effects
            mock_fetcher.fetch.side_effect = None
            mock_rename.side_effect = None
            mock_organize.side_effect = None

            # Assert all options are enabled
            assert self.config.getboolean("tv", "fetch")
            assert self.config.getboolean("tv", "rename")
            assert self.config.getboolean("tv", "organize")

            # Process media
            processed: nielsen.media.Media = processor.process(media_path)

            # Assert functions are called
            mock_fetcher.fetch.assert_called_once()
            mock_rename.assert_called_once()
            mock_organize.assert_called_once()

            # Assert returned type of processed Media matches
            assert isinstance(processed, nielsen.media.TV)


class TestMLStripper(unittest.TestCase):
    def test_strip_tags(self):
        """Should strip HTML tags from the given input."""

        summary: str = """\u003cp\u003eJason Sudeikis plays Ted Lasso, a small-time
            college football coach from Kansas hired to coach a professional soccer team
            in England, despite having no experience coaching soccer.\u003c/p\u003e"""

        stripped: str = """Jason Sudeikis plays Ted Lasso, a small-time
            college football coach from Kansas hired to coach a professional soccer team
            in England, despite having no experience coaching soccer."""

        self.assertEqual(nielsen.fetcher.strip_tags(summary), stripped)


if __name__ == "__main__":
    unittest.main()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab textwidth=88
