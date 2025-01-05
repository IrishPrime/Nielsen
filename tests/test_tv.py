"""Test the nielsen.media.TV class."""

import logging
import pathlib
from configparser import ConfigParser
from typing import Any, Callable, Pattern, TypedDict

import pytest
from pytest_mock import MockerFixture, MockType

import nielsen.config
import nielsen.media


class EpisodeMetadata(TypedDict):
    """A simple way to define the structure of episode metadata used in the majority of
    tests."""

    series: str
    season: int
    episode: int
    title: str


# Not quite a fixture, but a list of of tuples containing a filename and a dictionary of
# the metadata that should be inferred by a successful call to the
# nielsen.media.TV.infer method. This can be passed to pytest parametrized test
# functions to avoid building huge lists in the decorator.
EPISODES: list[tuple[str, EpisodeMetadata]] = [
    (
        # Very nicely formatted
        "The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi",
        {
            "series": "The Glades",
            "season": 2,
            "episode": 1,
            "title": "Family Matters",
        },
    ),
    (
        # Needs title casing
        "the.glades.s02e01.family.matters.hdtv.xvid-fqm.avi",
        {
            "series": "The Glades",
            "season": 2,
            "episode": 1,
            "title": "Family Matters",
        },
    ),
    (
        # Missing title
        "The.Glades.S02E01.HDTV.XviD-FQM.avi",
        {
            "series": "The Glades",
            "season": 2,
            "episode": 1,
            "title": "",
        },
    ),
    (
        # Already processed by nielsen
        "The Glades -02.01- Family Matters.avi",
        {
            "series": "The Glades",
            "season": 2,
            "episode": 1,
            "title": "Family Matters",
        },
    ),
    (
        # Another common post-processing format
        "The Glades -201- Family Matters.avi",
        {
            "series": "The Glades",
            "season": 2,
            "episode": 1,
            "title": "Family Matters",
        },
    ),
    (
        # Four digit season/episode code, fewer hyphens
        "Firefly 0101 - Serenity.mkv",
        {
            "series": "Firefly",
            "season": 1,
            "episode": 1,
            "title": "Serenity",
        },
    ),
    (
        # Has most necessary information, but formatted strangely
        "Supernatural.S10E15.mp4",
        {
            "series": "Supernatural",
            "season": 10,
            "episode": 15,
            "title": "",
        },
    ),
    (
        # Same as above, but with an extra dot between season and episode
        "Pushing.Daisies.S02.E03.mp4",
        {
            "series": "Pushing Daisies",
            "season": 2,
            "episode": 3,
            "title": "",
        },
    ),
    (
        # Nicely formatted, but with an apostrophe in the title
        "Person.of.Interest.S0310.The.Devil's.Share.HDTV.avi",
        {
            "series": "Person of Interest",
            "season": 3,
            "episode": 10,
            "title": "The Devil's Share",
        },
    ),
    (
        # Ensure title casing with the apostrophe works well
        "person.of.interest.s03e10.the.devil's.share.hdtv.avi",
        {
            "series": "Person of Interest",
            "season": 3,
            "episode": 10,
            "title": "The Devil's Share",
        },
    ),
    (
        # Testing WEB-RiP tag and series filtering to drop the year
        "Castle.(2009).S07E18.At.Close.Range.720p.WEB-RiP.mp4",
        {
            "series": "Castle",
            "season": 7,
            "episode": 18,
            "title": "At Close Range",
        },
    ),
    (
        # Same as above, but with title casing
        "Castle.(2009).S01E01.Flowers.for.Your.Grave.720p.WEB-RiP.mp4",
        {
            "series": "Castle",
            "season": 1,
            "episode": 1,
            "title": "Flowers For Your Grave",
        },
    ),
    (
        # Four digit season and episode combination
        "supernatural.1117.red.meat.hdtv-lol[ettv].mp4",
        {
            "series": "Supernatural",
            "season": 11,
            "episode": 17,
            "title": "Red Meat",
        },
    ),
    (
        # Specifying file within a directory
        "supernatural.1117.hdtv-lol[ettv]/supernatural.1117.red.meat.hdtv-lol[ettv].mp4",
        {
            "series": "Supernatural",
            "season": 11,
            "episode": 17,
            "title": "Red Meat",
        },
    ),
    (
        # Four digit year with parenthesis followed by three digit season and episode combination
        "the.flash.(2014).217.flash.back.hdtv-lol[ettv].mp4",
        {
            "series": "The Flash",
            "season": 2,
            "episode": 17,
            "title": "Flash Back",
        },
    ),
    (
        # Four digit year with season and episode markers
        "The.Flash.2014.S02E17.Flash.Back.HDTV.x264-LOL[ettv].mp4",
        {
            "series": "The Flash",
            "season": 2,
            "episode": 17,
            "title": "Flash Back",
        },
    ),
    (
        # Four digit year followed by three digit season and episode combination
        "The.Flash.2014.217.Flash.Back.HDTV.x264-LOL[ettv].mp4",
        {
            "series": "The Flash",
            "season": 2,
            "episode": 17,
            "title": "Flash Back",
        },
    ),
    (
        # Tag removal
        "Game.of.Thrones.S06E07.The.Broken.Man.1080p.HDTV.6CH.ShAaNiG.mkv",
        {
            "series": "Game of Thrones",
            "season": 6,
            "episode": 7,
            "title": "The Broken Man",
        },
    ),
    (
        # File in a subdirectory and tag removal
        "Game.of.Thrones.S07E01.720p.HDTV.x264-AVS[rarbg]/Game.of.Thrones.S07E01.Dragonstone.720p.HDTV.x264-AVS.mkv",
        {
            "series": "Game of Thrones",
            "season": 7,
            "episode": 1,
            "title": "Dragonstone",
        },
    ),
    (
        # Single episode with what looks like a second episode marker in the title
        "Sample.Show.S01E01.E19.Protocol.720p.HDTV.X264-DIMENSION.mkv",
        {
            "series": "Sample Show",
            "season": 1,
            "episode": 1,
            "title": "E19 Protocol",
        },
    ),
    (
        # Unusual filename for last ditch effort pattern
        "Limitless S01E11 This Is Your Brian on Drugs (1080p x265 Joy).mkv",
        {
            "series": "Limitless",
            "season": 1,
            "episode": 11,
            "title": "This Is Your Brian On Drugs",
        },
    ),
    (
        # Filename with lots of numbers
        "What.If.2021.S02E08.What.if.the.Avengers.Assembled.in.1602.1080p.DSNP.WEB-DL.DDP5.1.Atmos.H.264-FLUX.mkv",
        {
            "series": "What If",
            "season": 2,
            "episode": 8,
            "title": "What If The Avengers Assembled In 1602",
        },
    ),
]


@pytest.fixture
def tv_good_filename() -> nielsen.media.TV:
    return nielsen.media.TV(
        pathlib.Path("fixtures/tv/Ted Lasso -01.03- Trent Crimm: The Independent.mkv")
    )


@pytest.fixture
def tv_good_metadata() -> nielsen.media.TV:
    return nielsen.media.TV(
        pathlib.Path("fixtures/tv/tv.mkv"),
        series="Ted Lasso",
        season=1,
        episode=3,
        title="Trent Crimm: The Independent",
    )


@pytest.fixture
def tv_good_metadata_missing_file(missing_file) -> nielsen.media.TV:
    return nielsen.media.TV(
        missing_file,
        series="Ted Lasso",
        season=1,
        episode=3,
        title="Trent Crimm: The Independent",
    )


@pytest.fixture
def tv_all_data() -> nielsen.media.Media:
    return nielsen.media.TV(
        pathlib.Path("fixtures/tv/Ted Lasso -01.03- Trent Crimm: The Independent.mkv"),
        series="Ted Lasso",
        season=1,
        episode=3,
        title="Trent Crimm: The Independent",
    )


@pytest.fixture
def tv_no_metadata(mocker) -> Callable[[str], nielsen.media.TV]:
    """Return a mock TV object using the given filename as a Path but setting no
    metadata. Unlike a real TV object, the provided filename need not exist, nor be a
    regular file - those checks are disabled when creating this object."""

    def __tv_factory(filename: str) -> nielsen.media.TV:
        return nielsen.media.TV(pathlib.Path(filename))

    mock_exists: MockType = mocker.patch("pathlib.Path.exists")
    mock_exists.return_value = True
    mock_is_file: MockType = mocker.patch("pathlib.Path.is_file")
    mock_is_file.return_value = True

    return __tv_factory


@pytest.fixture
def tv_factory(mocker) -> Callable[[str, EpisodeMetadata], nielsen.media.TV]:
    """Return a mock TV object using the given filename as a Path and setting any other
    metadata provided. Unlike a real TV object, the provided filename need not exist,
    nor be a regular file - those checks are disabled when creating this object."""

    def __tv_factory(filename: str, metadata: EpisodeMetadata) -> nielsen.media.TV:
        return nielsen.media.TV(
            pathlib.Path(filename),
            series=metadata.get("series", ""),
            season=metadata.get("season", 0),
            episode=metadata.get("episode", 0),
            title=metadata.get("title", ""),
        )

    mock_exists: MockType = mocker.patch("pathlib.Path.exists")
    mock_exists.return_value = True
    mock_is_file: MockType = mocker.patch("pathlib.Path.is_file")
    mock_is_file.return_value = True

    return __tv_factory


@pytest.mark.parametrize(
    "fixt",
    [
        pytest.param("tv_good_metadata", id="good metadata"),
        pytest.param("tv_good_metadata_missing_file", id="good metadata missing file"),
        pytest.param("tv_all_data", id="all data"),
    ],
)
def test_get_metadata(fixt, request) -> None:
    """Return a dictionary with all the relevant fields."""

    tv: nielsen.media.TV = request.getfixturevalue(fixt)
    assert tv.metadata == {
        "series": "Ted Lasso",
        "season": 1,
        "episode": 3,
        "title": "Trent Crimm: The Independent",
    }


def test_get_orgdir(tv_all_data) -> None:
    """The orgdir should be the library, series name, then season."""

    assert (
        tv_all_data.orgdir == pathlib.Path("fixtures/tv/Ted Lasso/Season 01/").resolve()
    )


@pytest.mark.parametrize(
    "fixt",
    [
        pytest.param("tv_good_filename", id="good filename"),
        pytest.param("tv_good_metadata", id="good metadata"),
        pytest.param("tv_good_metadata_missing_file", id="good metadata missing file"),
        pytest.param("tv_all_data", id="all data"),
    ],
)
def test_get_patterns(fixt, request) -> None:
    """TV objects should have a list of patterns."""

    tv: nielsen.media.TV = request.getfixturevalue(fixt)
    assert isinstance(tv.patterns, list)
    for pattern in tv.patterns:
        assert isinstance(pattern, Pattern)


@pytest.mark.parametrize(
    "fixt",
    [
        pytest.param("tv_good_filename", id="good filename"),
        pytest.param("tv_good_metadata", id="good metadata"),
        pytest.param("tv_good_metadata_missing_file", id="good metadata missing file"),
        pytest.param("tv_all_data", id="all data"),
    ],
)
def test_get_section(fixt, request) -> None:
    """The section property should return a value based on the type."""

    tv: nielsen.media.TV = request.getfixturevalue(fixt)
    assert tv.section == "tv", "The section should match the type name, but lowercase"


@pytest.mark.parametrize("filename, metadata", EPISODES)
def test_infer(filename: str, metadata: EpisodeMetadata, tv_no_metadata) -> None:
    """Test every pattern and difficult edge cases."""

    tv: nielsen.media.TV = tv_no_metadata(filename)
    tv.infer()
    assert tv.metadata == metadata, "Inferred metadata mismatch"


def test_ordering(missing_file) -> None:
    """Items should be sorted by season, then episode number."""

    assert nielsen.media.TV(missing_file, season=1, episode=1) < nielsen.media.TV(
        missing_file, season=1, episode=2
    ), "Same season, different episode numbers"

    assert nielsen.media.TV(missing_file, season=1, episode=1) < nielsen.media.TV(
        missing_file, season=2, episode=1
    ), "Different seasons, same episode number"

    assert nielsen.media.TV(missing_file, season=1, episode=10) < nielsen.media.TV(
        missing_file, season=2, episode=2
    ), "Different seasons and episode numbers"

    assert nielsen.media.TV(missing_file, season=1, episode=2) == nielsen.media.TV(
        missing_file, season=1, episode=2
    ), "Same season and episode number"


def test_rename_file_not_found(tv_good_metadata_missing_file) -> None:
    """Rename a TV object with no path or an invalid path."""

    with pytest.raises(FileNotFoundError):
        tv_good_metadata_missing_file.rename()


@pytest.mark.parametrize("simulate", ["true", "false"], ids=["simulate", "no-simulate"])
def test_rename_success(
    simulate: str,
    tv_good_metadata: nielsen.media.TV,
    config: ConfigParser,
) -> None:
    """Successfully rename a file without moving it to a different directory."""

    # Set simulation, which controls whether the file is actually renamed, or the the
    # new path is returned without renaming
    config.set("nielsen", "simulate", simulate)

    # Ensure the source exists and the destination does not
    tv_good_metadata.path.touch(exist_ok=True)
    source: pathlib.Path = tv_good_metadata.path.resolve()
    dest: pathlib.Path = tv_good_metadata.path.with_stem(str(tv_good_metadata))
    dest.unlink(missing_ok=True)
    assert source.exists()
    assert not dest.exists()

    new_path: pathlib.Path = tv_good_metadata.rename()

    if config.getboolean("nielsen", "simulate"):
        assert new_path == source
        assert source.exists()
        assert not dest.exists()
        source.unlink()
    else:
        assert new_path == dest
        assert not source.exists()
        assert dest.exists()
        dest.unlink()


def test_rename_file_exists(
    tv_good_metadata: nielsen.media.TV,
    mocker: MockerFixture,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Rename a TV object where the destination already exists."""

    caplog.set_level(logging.INFO)

    mock_exists: MockType = mocker.patch("pathlib.Path.exists")
    mock_exists.return_value = True

    mock_samefile: MockType = mocker.patch("pathlib.Path.samefile")
    mock_samefile.return_value = False

    tv_good_metadata.rename()
    assert "FILE_CONFLICT" in caplog.text

    mock_samefile.return_value = True
    tv_good_metadata.rename()
    assert "File already named correctly." in caplog.text


def test_organize_success(tv_factory, mocker: MockerFixture) -> None:
    """Organize file, set and return new path."""

    # Mock the existence of the file on disk to avoid creating and removing
    # files on every test.
    mock_is_file: MockType = mocker.patch("pathlib.Path.is_file")
    mock_is_file.return_value = True

    mock_chmod: MockType = mocker.patch("pathlib.Path.chmod")
    mock_chown: MockType = mocker.patch("nielsen.media.chown")
    mock_move: MockType = mocker.patch("nielsen.media.move")

    # shutil.move moves a file and returns the destination path passed as an
    # argument. Mock it by just returning the input argument.
    mock_move.side_effect = lambda _, org: org
    filename: str = "fixtures/tv/Ted Lasso -01.03- Trent Crimm: The Independent.mkv"
    destination: str = "fixtures/tv/Ted Lasso/Season 01/Ted Lasso -01.03- Trent Crimm: The Independent.mkv"

    tv: nielsen.media.TV = tv_factory(
        filename,
        {
            "series": "Ted Lasso",
            "season": 1,
            "episode": 3,
            "title": "Trent Crimm: The Independent",
        },
    )

    assert tv.organize() == (pathlib.Path(destination).resolve())

    # The pathlib.Path.chmod and shutil.chown functions can be assumed to work properly,
    # we just need to assert that they were called with the correct values.
    mock_chmod.assert_called_with(0o644)
    mock_chown.assert_called_with(tv.path, "nielsen_user", "nielsen_group")


def test_repr(tv_all_data) -> None:
    """Object representation should contain enough information to recreate an object."""

    path: pathlib.Path = pathlib.Path(
        "fixtures/tv/Ted Lasso -01.03- Trent Crimm: The Independent.mkv"
    ).resolve()
    series: str = "Ted Lasso"
    season: int = 1
    episode: int = 3
    title: str = "Trent Crimm: The Independent"
    expected: str = f"<TV(self.{path=}, self.{series=}, self.{season=}, self.{episode=}, self.{title=})>"

    assert repr(tv_all_data) == expected


def test_set_metadata(tv_no_metadata) -> None:
    """Set the metadata dictionary (with type conversions)."""

    metadata: dict[str, Any] = {
        "series": "Ted Lasso",
        "season": "1",
        "episode": "3",
        "title": "Trent Crimm: The Independent",
    }
    tv_no_metadata.metadata = metadata

    assert tv_no_metadata.metadata == metadata


def test_str(tv_good_metadata: nielsen.media.TV) -> None:
    """The string representation should provide a useful display name."""

    expected: str = "Ted Lasso -01.03- Trent Crimm: The Independent"

    assert (
        str(tv_good_metadata) == expected
    ), "String representation should match display format"


def test_str_no_metadata(tv_no_metadata: Callable[[str], nielsen.media.TV]) -> None:
    """The string representation should indicate a lack of metadata."""

    expected: str = "Unknown -00.00- Unknown"

    assert (
        str(tv_no_metadata("Ted Lasso -01.03- Trent Crimm: The Independent.mkv"))
        == expected
    ), "TV object with no metadata, but good filename"


def test_transform_no_section(
    tv_all_data: nielsen.media.TV,
    config: ConfigParser,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Log a warning and return the input if no config section found."""

    config.clear()

    transformed: str = tv_all_data.transform("series")
    assert "NO_TRANSFORM_SECTION" in caplog.text
    assert tv_all_data.series == transformed


def test_transform_no_option(
    tv_all_data: nielsen.media.TV,
    config: ConfigParser,
    caplog: pytest.LogCaptureFixture,
):
    """Log a warning and return the input if no config option found."""

    config.clear()
    config.add_section("tv/transform/series")
    transformed: str = tv_all_data.transform("series")

    assert "NO_TRANSFORM_OPTION" in caplog.text
    assert tv_all_data.series == transformed


@pytest.mark.parametrize(
    "variant",
    [
        "Marvel's Agents of S.H.I.E.L.D.",
        "Marvel's Agents of S H I E L D ",
        "Marvel's Agents of SHIELD",
        "Agents of S.H.I.E.L.D.",
        "Agents of S H I E L D ",
        "Agents of SHIELD",
    ],
)
def test_transform(
    variant: str,
    tv_factory: Callable[[str, EpisodeMetadata], nielsen.media.TV],
    config: ConfigParser,
    mocker: MockerFixture,
) -> None:
    """Transform series names based on values from the tv/series/transform config section."""

    # Marvel's Agents of S.H.I.E.L.D. has many variants in the way the series name
    # might be listed. Which variant you prefer is a matter of personal preference
    # and can be configured, but once configured they should all resolve to the same
    # user-preferred variant.

    config.clear()
    config.add_section("tv/transform/series")
    expected: str = "Agents of SHIELD"
    config.set("tv/transform/series", variant, expected)

    # Mock is_dir to ensure the library setter succeeds even when we don't know what the
    # filesystem tree actually looks like in automated test environments.
    mock_is_dir: MockType = mocker.patch("pathlib.Path.is_dir")
    mock_is_dir.return_value = True

    shield: nielsen.media.Media = tv_factory(
        "shield.mkv", {"series": variant, "season": 1, "episode": 1, "title": ""}
    )

    assert shield.transform("series") == expected
