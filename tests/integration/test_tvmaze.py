"""Live integration tests against the real TVMaze API.

These tests are gated behind the `integration` pytest marker and skipped
by default. Run them with::

    uv run pytest -m integration

Each test makes real HTTP requests to https://api.tvmaze.com, so they
require network access and may be rate-limited or affected by API schema
changes upstream.
"""

import pathlib

import pytest

import nielsen.fetcher
import nielsen.media

pytestmark = pytest.mark.integration


@pytest.fixture
def fetcher() -> nielsen.fetcher.TVMaze:
    return nielsen.fetcher.TVMaze()


PATTERNS: list[tuple[str, dict[str, str | int]]] = [
    # Very nicely formatted
    (
        "The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi",
        {"series": "The Glades", "season": 2, "episode": 1, "title": "Family Matters"},
    ),
    # Needs title casing
    (
        "the.glades.s02e01.family.matters.hdtv.xvid-fqm.avi",
        {"series": "The Glades", "season": 2, "episode": 1, "title": "Family Matters"},
    ),
    # Missing title — TVMaze fills it in
    (
        "The.Glades.S02E01.HDTV.XviD-FQM.avi",
        {"series": "The Glades", "season": 2, "episode": 1, "title": "Family Matters"},
    ),
    # Already processed by nielsen
    (
        "The Glades -02.01- Family Matters.avi",
        {"series": "The Glades", "season": 2, "episode": 1, "title": "Family Matters"},
    ),
    # Another common post-processing format
    (
        "The Glades -201- Family Matters.avi",
        {"series": "The Glades", "season": 2, "episode": 1, "title": "Family Matters"},
    ),
    # Four digit season/episode code, fewer hyphens
    (
        "Firefly 0101 - The Train Job.mkv",
        {"series": "Firefly", "season": 1, "episode": 1, "title": "The Train Job"},
    ),
    # Has most necessary information, but formatted strangely
    (
        "Supernatural.S10E15.mp4",
        {
            "series": "Supernatural",
            "season": 10,
            "episode": 15,
            "title": "The Things They Carried",
        },
    ),
    # Same as above, but with an extra dot between season and episode
    (
        "Pushing.Daisies.S02.E03.mp4",
        {
            "series": "Pushing Daisies",
            "season": 2,
            "episode": 3,
            "title": "Bad Habits",
        },
    ),
    # Nicely formatted, but with an apostrophe in the title
    (
        "Person.of.Interest.S03E10.The.Devil's.Share.HDTV.avi",
        {
            "series": "Person of Interest",
            "season": 3,
            "episode": 10,
            "title": "The Devil's Share",
        },
    ),
    # Title casing this will yield slightly incorrect results
    (
        "person.of.interest.s03e10.the.devil's.share.hdtv.avi",
        {
            "series": "Person of Interest",
            "season": 3,
            "episode": 10,
            "title": "The Devil's Share",
        },
    ),
    # Testing WEB-RiP tag and series filtering
    (
        "Castle.(2009).S07E18.720p.WEB-RiP.mp4",
        {"series": "Castle", "season": 7, "episode": 18, "title": "At Close Range"},
    ),
    # Same as above, but with all fields
    (
        "Castle.(2009).S01E01.Flowers.for.Your.Grave.720p.WEB-RiP.mp4",
        {
            "series": "Castle",
            "season": 1,
            "episode": 1,
            "title": "Flowers for Your Grave",
        },
    ),
    # Four digit season and episode combination
    (
        "supernatural.1117.red.meat.hdtv-lol[ettv].mp4",
        {
            "series": "Supernatural",
            "season": 11,
            "episode": 17,
            "title": "Red Meat",
        },
    ),
    # Specifying file within a directory
    (
        "supernatural.1117.hdtv-lol[ettv]/supernatural.1117.red.meat.hdtv-lol[ettv].mp4",
        {
            "series": "Supernatural",
            "season": 11,
            "episode": 17,
            "title": "Red Meat",
        },
    ),
    # Four digit year followed by three digit season and episode combination
    (
        "the.flash.(2014).217.flash.back.hdtv-lol[ettv].mp4",
        {
            "series": "The Flash",
            "season": 2,
            "episode": 17,
            "title": "Flash Back",
        },
    ),
    # Four digit year with season and episode markers
    (
        "The.Flash.2014.S02E17.Flash.Back.HDTV.x264-LOL[ettv].mp4",
        {
            "series": "The Flash",
            "season": 2,
            "episode": 17,
            "title": "Flash Back",
        },
    ),
    # Four digit year followed by three digit season and episode combination
    (
        "The.Flash.2014.217.Flash.Back.HDTV.x264-LOL[ettv].mp4",
        {
            "series": "The Flash",
            "season": 2,
            "episode": 17,
            "title": "Flash Back",
        },
    ),
    # Tag removal
    (
        "Game.of.Thrones.S06E07.1080p.HDTV.6CH.ShAaNiG.mkv",
        {
            "series": "Game of Thrones",
            "season": 6,
            "episode": 7,
            "title": "The Broken Man",
        },
    ),
    # File in a subdirectory
    (
        "Game.of.Thrones.S07E01.720p.HDTV.x264-AVS[rarbg]/Game.of.Thrones.S07E01.720p.HDTV.x264-AVS.mkv",
        {
            "series": "Game of Thrones",
            "season": 7,
            "episode": 1,
            "title": "Dragonstone",
        },
    ),
    # Multi-episode file
    (
        "Bones.S04E01E02.720p.HDTV.X264-DIMENSION.mkv",
        {
            "series": "Bones",
            "season": 4,
            "episode": 1,
            "title": "Yanks in the U.K., Part 1",
        },
    ),
    # Unusual filename for last ditch effort pattern
    (
        "Limitless S01E11 This Is Your Brian on Drugs (1080p x265 Joy).mkv",
        {
            "series": "Limitless",
            "season": 1,
            "episode": 11,
            "title": "This is Your Brian on Drugs",
        },
    ),
]


@pytest.mark.parametrize("filename, expected", PATTERNS)
def test_all_patterns(
    fetcher: nielsen.fetcher.TVMaze,
    filename: str,
    expected: dict[str, str | int],
) -> None:
    """Each filename should infer and fetch into the expected metadata."""

    tv: nielsen.media.TV = nielsen.media.TV(pathlib.Path(filename))
    tv.infer()
    fetcher.fetch(tv)
    assert tv.metadata == expected


FETCH_FAILURES: list[str] = [
    # Single episode with what looks like a second episode marker in the title
    "Sample.Show.S01E01.E19.Protocol.720p.HDTV.X264-DIMENSION.mkv",
    # Insufficient metadata to look anything up
    "Something.Close.12.mp4",
]


@pytest.mark.parametrize("filename", FETCH_FAILURES)
def test_fetch_failures(fetcher: nielsen.fetcher.TVMaze, filename: str) -> None:
    """Filenames that should raise ValueError during fetch."""

    tv: nielsen.media.TV = nielsen.media.TV(pathlib.Path(filename))
    tv.infer()
    with pytest.raises(ValueError):
        fetcher.fetch(tv)
