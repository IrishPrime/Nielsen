import pathlib
import pickle
from configparser import ConfigParser
from typing import Any

import pytest
from pytest_mock import MockerFixture, MockType
from requests.models import Response

import nielsen.config
import nielsen.fetcher
import nielsen.media


@pytest.fixture
def fetcher() -> nielsen.fetcher.TVMaze:
    """Return a TVMaze fetcher."""

    return nielsen.fetcher.TVMaze()


@pytest.fixture
def ted_lasso_series_id() -> int:
    """Return the TVMaze ID for Ted Lasso to have a consistently available show ID."""

    return 44458


@pytest.fixture
def ted_lasso_season2_id() -> int:
    """Return the TVMaze ID for Ted Lasso season 2 to have a consistently available
    season ID."""

    return 112939


@pytest.fixture
def mock_get(mocker: MockerFixture) -> MockType:
    """Return a mocked version of requests.get."""

    return mocker.patch("requests.get")


@pytest.fixture
def mock_input(mocker: MockerFixture) -> MockType:
    """Return a mocked version of builtins.input."""

    return mocker.patch("builtins.input")


@pytest.fixture
def mock_tv(mocker: MockerFixture) -> MockType:
    """Return a MagicMock specced for a nielsen.media.TV instance."""

    return mocker.MagicMock(spec=nielsen.media.TV)


def test_get_series_id_local(
    fetcher: nielsen.fetcher.TVMaze, ted_lasso_series_id: int, mocker: MockerFixture
) -> None:
    """Get series ID from local config file."""

    # Use a Spy to assert the right function was called by get_series_id.
    id_local = mocker.spy(nielsen.fetcher.TVMaze, "get_series_id_local")

    assert (
        fetcher.get_series_id("Ted Lasso") == ted_lasso_series_id
    ), "Should get ID from config file"

    id_local.assert_called_with(fetcher, "Ted Lasso")


def test_get_series_id_remote_single(
    config: ConfigParser,
    fetcher: nielsen.fetcher.TVMaze,
    ted_lasso_series_id: int,
    mock_get: MockType,
    mocker: MockerFixture,
) -> None:
    """Get series ID from TVMaze API with single result."""

    # Clear the config to ensure the series isn't found locally
    config.clear()

    # Use a Spy to assert the right function was called by get_series_id.
    id_singlesearch = mocker.spy(nielsen.fetcher.TVMaze, "get_series_id_singlesearch")

    # Load test fixture with actual API results
    resp_ok: Response = pickle.loads(
        pathlib.Path("fixtures/tv/singlesearch/shows-q-ted+lasso.pickle").read_bytes()
    )

    mock_get.return_value = resp_ok
    assert (
        fetcher.get_series_id("Ted Lasso") == ted_lasso_series_id
    ), "Should get ID from TVMaze response"

    id_singlesearch.assert_called_once_with(fetcher, "Ted Lasso")
    id_singlesearch.reset_mock()

    # Ensure a bad response returns a 0 for the Series ID
    resp_not_ok: Response = pickle.loads(
        pathlib.Path(
            "fixtures/tv/singlesearch/shows-q-useless+search+string.pickle"
        ).read_bytes()
    )
    mock_get.return_value = resp_not_ok

    assert (
        fetcher.get_series_id_singlesearch("Ted Lasso") == 0
    ), "Should return 0 on a 'not ok' TVMaze response"
    id_singlesearch.assert_called_once_with(fetcher, "Ted Lasso")


@pytest.mark.parametrize(
    "series_name, series_id, data_name",
    [
        pytest.param(
            "Agents of SHIELD",
            31,
            "fixtures/tv/search/shows-q-agents+of+shield.pickle",
            id="Agents of SHIELD",
        ),
        pytest.param(
            "Ted Lasso",
            44458,
            "fixtures/tv/search/shows-q-ted+lasso.pickle",
            id="Ted Lasso",
        ),
        pytest.param(
            "Useless Search String",
            0,
            "fixtures/tv/search/shows-q-useless+search+string.pickle",
            id="Useless Search String",
        ),
    ],
)
def test_get_series_id_remote_multiple(
    series_name: str,
    series_id: int,
    data_name: str,
    config: ConfigParser,
    fetcher: nielsen.fetcher.TVMaze,
    mock_tv: MockType,
    mock_get: MockType,
    mock_input: MockType,
    mocker: MockerFixture,
) -> None:
    """Get series ID from TVMaze API with multiple results. This test ensures that the
    correct method for getting the series ID was called."""

    # Clear the config to ensure the series isn't found locally.
    config.clear()

    # Use a Spy to assert the right function was called by get_series_id.
    id_search = mocker.spy(nielsen.fetcher.TVMaze, "get_series_id_search")

    # Setup the TV instance
    mock_tv.series = series_name

    # Mock the Response with actual API results.
    resp: Response = pickle.loads(pathlib.Path(data_name).read_bytes())
    mock_get.return_value = resp

    # Always choose the first result
    mock_input.return_value = "1"

    assert (
        fetcher.get_series_id(series=mock_tv.series, interactive=True) == series_id
    ), "Should get ID from TVMaze response"

    id_search.assert_called_with(fetcher, mock_tv.series)


def test_get_episode_title(
    fetcher: nielsen.fetcher.TVMaze,
    mock_get: MockType,
    ted_lasso_series_id: int,
    mocker: MockerFixture,
) -> None:
    """Get the episode title for a given series, season, and episode number."""

    tv: MockType = mocker.MagicMock(spec=nielsen.media.TV)
    tv.series = "Ted Lasso"
    tv.season = 1
    tv.episode = 3
    title: str = "Trent Crimm: The Independent"

    mock_get.return_value = pickle.loads(
        pathlib.Path(
            f"fixtures/tv/shows/{ted_lasso_series_id}/episodebynumber-season-1-number-3.pickle"
        ).read_bytes()
    )

    assert fetcher.get_episode_title(tv) == title


def test_get_episode_title_errors(
    fetcher: nielsen.fetcher.TVMaze, missing_file: pathlib.Path, mocker: MockerFixture
) -> None:
    """Raise errors when insufficient information to search for episode titles."""

    mock_get_series_id: MockType = mocker.patch("nielsen.fetcher.TVMaze.get_series_id")
    mock_get_series_id.return_value = None

    empty: nielsen.media.TV = nielsen.media.TV(missing_file)
    with pytest.raises(ValueError):
        fetcher.get_episode_title(empty)

    mock_get_series_id.return_value = 42
    with pytest.raises(ValueError):
        fetcher.get_episode_title(empty)

    empty.season = 1
    with pytest.raises(ValueError):
        fetcher.get_episode_title(empty)


def test_set_series_id(fetcher: nielsen.fetcher.TVMaze, config: ConfigParser) -> None:
    """Create a mapping between a series name and a TVMaze series ID."""

    series: str = "Foo: The Series"
    id: int = 42

    # Clear the config to ensure things work properly even when there is no section
    # for TVMaze IDs.
    config.clear()

    assert not config.has_option(
        fetcher.IDS, series
    ), "The option should not exist before setting."

    fetcher.set_series_id(series, id)
    assert config.has_option(
        fetcher.IDS, series
    ), "The section and option should both exist after setting."


def test_fetch(
    fetcher: nielsen.fetcher.TVMaze,
    mock_get: MockType,
    mocker: MockerFixture,
    ted_lasso_series_id: int,
) -> None:
    """Fetch and update metadata using information from the given `Media` object."""

    tv: MockType = mocker.MagicMock(spec=nielsen.media.TV)
    tv.title = ""

    tv.series = "Ted Lasso"
    tv.season = 1
    tv.episode = 3

    mock_get.return_value = pickle.loads(
        pathlib.Path(
            f"fixtures/tv/shows/{ted_lasso_series_id}/episodebynumber-season-1-number-3.pickle"
        ).read_bytes()
    )

    assert tv.title == ""
    fetcher.fetch(tv)
    assert (
        tv.title == "Trent Crimm: The Independent"
    ), "Title should be correctly set after fetching."


def test_fetch_no_series_id(
    fetcher: nielsen.fetcher.TVMaze, mocker: MockerFixture
) -> None:
    """Fetch and update metadata using information from the given `Media` object."""

    mock_series_id: MockType = mocker.patch("nielsen.fetcher.TVMaze.get_series_id")
    mock_series_id.return_value = 0
    tv: MockType = mocker.MagicMock(spec=nielsen.media.TV)
    tv.series = ""

    with pytest.raises(ValueError):
        fetcher.fetch(tv)


def test_get_season_id(
    fetcher: nielsen.fetcher.TVMaze, mock_get: MockType, ted_lasso_series_id: int
) -> None:
    """Verify the GET request and response handling."""

    mock_get.return_value = pickle.loads(
        pathlib.Path(
            f"fixtures/tv/shows/{ted_lasso_series_id}/seasons-.pickle"
        ).read_bytes()
    )
    season_id: int = fetcher.get_season_id(ted_lasso_series_id, 2)
    mock_get.assert_called_with(
        f"{fetcher.SERVICE}/shows/{ted_lasso_series_id}/seasons"
    )

    assert season_id == 112939  # Ted Lasso Season 2 ID


def test_get_season_id_no_match(
    fetcher: nielsen.fetcher.TVMaze, mock_get: MockType, ted_lasso_series_id: int
) -> None:
    """Verify the GET request and response handling."""

    mock_get.return_value.json.return_value = {}
    season_id: int = fetcher.get_season_id(ted_lasso_series_id, 0)

    assert season_id == 0


def test_episodebynumber(
    fetcher: nielsen.fetcher.TVMaze, mock_get: MockType, ted_lasso_series_id
) -> None:
    """Verify the GET request and response handling."""

    mock_get.return_value = pickle.loads(
        pathlib.Path(
            f"fixtures/tv/shows/{ted_lasso_series_id}/episodebynumber-season-1-number-3.pickle"
        ).read_bytes()
    )

    fetcher.episodebynumber("Ted Lasso", 1, 3)
    mock_get.assert_called_with(
        f"{fetcher.SERVICE}/shows/{ted_lasso_series_id}/episodebynumber?season=1&number=3"
    )


def test_episodebynumber_no_series_id(fetcher: nielsen.fetcher.TVMaze) -> None:
    """Raise a ValueError if the series ID is invalid."""

    with pytest.raises(ValueError):
        fetcher.episodebynumber(0, 0, 0)


def test_seasons_episodes(fetcher: nielsen.fetcher.TVMaze, mock_get: MockType) -> None:
    """Verify the GET request and response handling."""

    season_id: int = 112939  # Ted Lasso Season 2 ID

    mock_get.return_value = pickle.loads(
        pathlib.Path(f"fixtures/tv/seasons/{season_id}/episodes-.pickle").read_bytes()
    )

    fetcher.seasons_episodes(season_id)
    mock_get.assert_called_with(f"{fetcher.SERVICE}/seasons/{season_id}/episodes")


def test_shows(
    fetcher: nielsen.fetcher.TVMaze, ted_lasso_series_id: int, mock_get: MockType
) -> None:
    """Verify the GET request and response handling."""

    fetcher.shows(ted_lasso_series_id)
    mock_get.assert_called_with(f"{fetcher.SERVICE}/shows/{ted_lasso_series_id}")


def test_pick_series_network() -> None:
    pass


def test_pick_series_streaming() -> None:
    pass


def test_pick_series_minimal(
    fetcher: nielsen.fetcher.TVMaze, mocker: MockerFixture
) -> None:
    """Pick a series with minimal information. Unlikely to happen, but should
    account for incomplete information returned from TVMaze."""

    mock_input: MockType = mocker.patch("builtins.input")

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

    assert fetcher.pick_series("Unit Test", [minimal_result]) == minimal_result


def test_pick_series_default(
    fetcher: nielsen.fetcher.TVMaze, mocker: MockerFixture
) -> None:
    """Pick a series with unparseable information."""

    mock_input: MockType = mocker.patch("builtins.input")
    unparseable_result: dict[str, Any] = {
        "Invalid": "Form",
    }

    # Select the only result
    mock_input.return_value = 1

    assert (
        fetcher.pick_series("Invalid Results", [unparseable_result])
        == unparseable_result
    )


def test_pretty_series() -> None:
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

    assert nielsen.fetcher.TVMaze.pretty_series(data) == (
        "Ted Lasso - ID: 44458 - https://www.tvmaze.com/shows/44458/ted-lasso\n"
        "Premiered: 2020-08-14 - Status: Running\n"
        "Ted Lasso centers on an idealistic — and clueless — all-American football coach hired to manage an English football club — despite having no soccer coaching experience at all."
    )


def test_pretty_season() -> None:
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

    assert nielsen.fetcher.TVMaze.pretty_season(data) == (
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
    )


def test_pretty_episode() -> None:
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

    assert nielsen.fetcher.TVMaze.pretty_episode(data) == (
        "3x4 - Big Week\n"
        "https://www.tvmaze.com/episodes/2490069/ted-lasso-3x04-big-week\n"
        "Everyone's feeling the pressure as Richmond gear up to play West Ham. Ted is reunited with an old friend."
    )
