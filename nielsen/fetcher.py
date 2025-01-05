"""Fetchers are used to query remote sources for metadata about a given Media object."""

import logging
import urllib.parse
from html.parser import HTMLParser
from io import StringIO
from typing import Any, Callable, Optional, Protocol

import requests

import nielsen.media
from nielsen.config import config

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Fetcher(Protocol):
    """Used to fetch metadata from an external source rather than infering it from the
    file name."""

    def fetch(self, media: nielsen.media.Media) -> None:
        """Fetch and update metadata using information from the given `Media` object."""
        ...


class TVMaze:
    """Fetch metadata for TV shows using the TVMaze API."""

    SERVICE: str = "https://api.tvmaze.com"
    IDS: str = "tvmaze/ids"

    def fetch(self, media: nielsen.media.TV) -> None:
        """Fetch metadata from TVMaze, update the metadata of the provided Media object,
        record the series ID in the config."""

        series_id: Optional[int] = self.get_series_id(
            media.series, config.getboolean("nielsen", "interactive")
        )

        if not series_id:
            raise ValueError("No Series ID")

        self.set_series_id(media.series, str(series_id))
        media.title = self.get_episode_title(media)

    def set_series_id(self, series: str, id: int | str) -> None:
        """Create a mapping from a series name to a TVMaze series ID in the config."""
        # TODO: Ensure the config gets written back to disk.

        logger.debug("Set '%s' to TVMaze Series ID %s.", series, id)

        if not config.has_section(self.IDS):
            logger.debug("Adding '%s' section to config.", self.IDS)
            config.add_section(self.IDS)

        config.set(self.IDS, series, str(id))

    def get_series_id(self, series: str, interactive: bool = False) -> int:
        """Return the TVMaze ID for the series. Will check for a local config file first
        and search TVMaze if a local match isn't found. Optionally, prompt the user to
        select the correct series interactively if multiple results are found. Returns 0
        if no series ID can be found."""

        if config.has_option(self.IDS, series):
            lookup = self.get_series_id_local
        elif interactive:
            lookup = self.get_series_id_search
        else:
            lookup = self.get_series_id_singlesearch

        series_id: int = lookup(series)
        logger.debug("Series: %s, ID: %s", series, series_id)

        if series_id and not config.has_option(self.IDS, series):
            self.set_series_id(series, series_id)

        return series_id

    def get_series_id_local(self, series: str) -> int:
        """Get the series ID from the configuration."""

        return config.getint(self.IDS, series, fallback=0)

    def get_series_id_search(
        self,
        series: str,
        picker: Callable[[str, list[dict[Any, Any]]], dict[str, Any]] | None = None,
    ) -> int:
        """Get the series ID from the TVMaze `search` endpoint, which can return
        multiple results. If multiple results are returned, prompt the user to pick one.
        The `picker` defines this behavior.
        """

        response: requests.Response = self.search_shows(series)
        rjson: list[dict[Any, Any]] = response.json()

        series_id: int = 0
        # If TVMaze returns an empty list, return 0.
        if not rjson:
            return series_id

        # If only one result, add it to the config and return the ID.
        if len(rjson) == 1:
            return rjson[0]["show"]["id"]

        # If multiple results, offer a means of selecting the correct one.
        if picker is None:
            picker = self.pick_series

        selection: dict = picker(series, rjson)

        series_id = selection["show"]["id"]

        return series_id

    def get_series_id_singlesearch(self, series: str) -> int:
        """Get the series ID from the TVMaze `singlesearch` endpoint, which returns a
        single result that it considers the best match.
        URL: /singlesearch/shows?q=:query
        """

        response: requests.Response = self.search_shows_single(series)
        rjson: dict[Any, Any] = response.json()

        if response.ok:
            return rjson.get("id", 0)

        return 0

    def get_episode_title(self, media: nielsen.media.TV) -> str:
        """Return the episode title for the given media object from the TVMaze API.
        URL: /shows/:id/episodebynumber?season=:season&number=:number.
        """

        series_id: Optional[int] = self.get_series_id(media.series)
        episode_title: str = ""

        if not series_id:
            raise ValueError("No Series ID")

        if not media.season:
            raise ValueError("No Season")

        if not media.episode:
            raise ValueError("No Episode Number")

        response: requests.Response = self.episodebynumber(
            series_id, media.season, media.episode
        )
        rjson: dict[Any, Any] = response.json()

        if response.ok:
            episode_title = str(rjson.get("name"))

        return episode_title

    def get_season_id(self, series_id: int, season: int) -> int:
        """Return information about a given `season` of a given `series_id`.
        URL: /shows/:id/seasons"""

        response: requests.Response = self.shows_seasons(series_id)
        rjson: dict[Any, Any] = response.json()

        for item in rjson:
            match item:
                case {"number": number} if number == season:
                    return item["id"]

        return 0

    def search_shows(self, series: str) -> requests.Response:
        """Search TVMaze for the given `series` and return the `requests.Response`
        object. URL: /search/shows?q=:query."""

        request: str = (
            f"{self.SERVICE}/search/shows/?q={urllib.parse.quote_plus(series)}"
        )
        logging.debug("Series: %s\nRequest: %r", series, request)
        response: requests.Response = requests.get(request)
        logging.debug(response)

        return response

    def search_shows_single(self, series: str) -> requests.Response:
        """Search TVMaze for the given `series` and return the `requests.Response`
        object containing information about the single best result.
        URL: /singlesearch/shows?q=:query"""

        request: str = (
            f"{self.SERVICE}/singlesearch/shows/?q={urllib.parse.quote_plus(series)}"
        )
        logger.debug("Series: %r\nRequest: %r", series, request)
        response: requests.Response = requests.get(request)
        logger.debug(response)

        return response

    def episodebynumber(
        self, series: int | str, season: int, episode: int
    ) -> requests.Response:
        """URL: /shows/:id/episodebynumber?season=:season&number=:episode"""

        if isinstance(series, int):
            series_id: int = series
        elif isinstance(series, str):
            series_id = self.get_series_id(series)

        if not series_id:
            raise ValueError("No Series ID")

        request: str = f"{self.SERVICE}/shows/{series_id}/episodebynumber?season={season}&number={episode}"
        response: requests.Response = requests.get(request)

        return response

    def seasons_episodes(self, season_id: int) -> requests.Response:
        """URL: /seasons/:id/episodes"""

        request: str = f"{self.SERVICE}/seasons/{season_id}/episodes"
        logger.debug("Request: %s", request)
        response: requests.Response = requests.get(request)

        return response

    def shows(self, series_id: int) -> requests.Response:
        """URL: /shows/:id"""

        request: str = f"{self.SERVICE}/shows/{series_id}"
        logger.debug("Request: %s", request)
        response: requests.Response = requests.get(request)

        return response

    def shows_seasons(self, series_id: int) -> requests.Response:
        """URL: /shows/:id/seasons"""

        request: str = f"{self.SERVICE}/shows/{series_id}/seasons"
        logger.debug("Request: %s", request)
        response: requests.Response = requests.get(request)

        return response

    @staticmethod
    def pick_series(query: str, results: list[dict[Any, Any]]) -> dict[str, Any]:
        """Display a text-based picker to choose a single show from multiple results."""

        print(f"Search results for: {query}")

        for option, result in enumerate(results, start=1):
            match result:
                # Network Television
                case {
                    "show": {
                        "name": name,
                        "id": series_id,
                        "premiered": premiered,
                        "network": {"name": nw_name, "country": nw_country},
                    }
                }:
                    logger.debug("Matched Network")
                    name = name
                    series_id = series_id
                    premiered = premiered
                    network: str = nw_name
                    country: str = (
                        nw_country.get("name", "Unknown") if nw_country else "Unknown"
                    )

                # Streaming Platforms
                case {
                    "show": {
                        "name": name,
                        "id": series_id,
                        "premiered": premiered,
                        "webChannel": {"name": wc_name, "country": wc_country},
                    }
                }:
                    logger.debug("Matched Streaming")
                    name = name
                    series_id = series_id
                    premiered = premiered
                    network = wc_name
                    country = (
                        wc_country.get("name", "Unknown") if wc_country else "Unknown"
                    )

                # Minimal Results
                case {
                    "show": {
                        "name": name,
                        "id": series_id,
                        "premiered": premiered,
                    }
                }:
                    logger.debug("Matched Minimal")
                    name = name
                    series_id = series_id
                    premiered = premiered
                    network = "Unknown"
                    country = "Unknown"

                # This should never happen
                case _:
                    # NOTE: It may be better to simply skip these results.
                    logger.error("Unable to parse search result")
                    logger.debug(result)
                    name = "Unknown"
                    series_id = 0
                    premiered = "Unknown"
                    network = "Unknown"
                    country = "Unknown"

            print(
                f"{option}. {name} (Premiered: {premiered}, Network: {network}, Country: {country}, ID: {series_id})"
            )

        # Start with an invalid selection to start the loop
        selection: int = -1
        while 0 > selection or selection >= len(results):
            selection = int(input("Select series: ")) - 1

        return results[selection]

    @staticmethod
    def pretty_series(data: dict[str, Any]) -> str:
        """Return a nicely formatted string of high-level information about the series
        as a whole, such as the title, TVMaze ID, premiere date, whether it's currently
        airing, and a plot summary.

        This is intended to work with the results of the TVMaze `/shows/:id`
        endpoint."""

        return "\n".join(
            (
                f"{data['name']} - ID: {data['id']} - {data['url']}",
                f"Premiered: {data['premiered']} - Status: {data['status']}",
                f"{strip_tags(data['summary'])}",
            )
        )

    @staticmethod
    def pretty_season(data: list[dict[str, Any]]) -> str:
        """Return a nicely formatted string containing information about every episode
        in a season, including the season and episode numbers, episode title, a link
        to the episode URL on TVMaze, and an episode summary.

        This is intended to work with the results of the TVMaze `/seasons/:id/episodes`
        endpoint."""

        pretty_episodes: list[str] = []

        for episode in data:
            pretty_episodes.append(TVMaze.pretty_episode(episode))

        return "\n\n".join(pretty_episodes)

    @staticmethod
    def pretty_episode(data: dict[str, Any]) -> str:
        """Return a nicely formatted string of episode specific information, including
        the season and episode numbers, episode title, a link to the episode URL on
        TVMaze, and an episode summary.

        This is intended to work with the results of the TVMaze `/seasons/:id/episodes`
        and `/shows/:id/episodebynumber?season=:season&number=:number` endpoints."""

        return "\n".join(
            (
                f"{data['season']}x{data['number']} - {data["name"]}",
                f"{data['url']}",
                f"{strip_tags(data['summary'])}",
            )
        )


class MLStripper(HTMLParser):
    """Markup Language Stripper"""

    def __init__(self):
        super().__init__()
        self.reset()
        self.strict = False
        self.convert_charrefs = True
        self.text = StringIO()

    def handle_data(self, data: str) -> None:
        self.text.write(data)

    def get_data(self) -> str:
        return self.text.getvalue()


def strip_tags(html):
    """Strip HTML tags to make API responses more readable in the terminal."""

    s = MLStripper()
    s.feed(html)
    return s.get_data()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab textwidth=88
