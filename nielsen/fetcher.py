"""Fetchers are used to query remote sources for metadata about a given Media object."""

import logging
import urllib.parse
from typing import Any, Optional, Protocol, TypeVar

import requests

import nielsen.media
from nielsen.config import config

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

# Define a generic Media type so the Fetcher Protocol will recognize Media subclasses
MT = TypeVar("MT", bound=nielsen.media.Media)


class Fetcher(Protocol):
    """Used to fetch metadata from an external source rather than infering it from the
    file name."""

    def fetch(self, media: MT) -> None:
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
            media.series, config.getboolean("DEFAULT", "interactive")
        )
        if series_id:
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
        select the correct series interactively if multiple results are found."""

        if config.has_option(self.IDS, series):
            lookup = self.get_series_id_local
        elif interactive:
            lookup = self.get_series_id_search
        else:
            lookup = self.get_series_id_singlesearch

        series_id: int = lookup(series)
        logger.debug("Series: %s, ID: %s", series, series_id)

        return series_id

    def get_series_id_local(self, series: str) -> int:
        """Get the series ID from the configuration."""

        return config.getint(self.IDS, series, fallback=0)

    def get_series_id_search(self, series: str) -> int:
        """Get the series ID from the TVMaze `search` endpoint, which can return
        multiple results. If multiple results are returned, prompt the user to pick one.
        URL: /search/shows?q=:query.
        """

        request: str = (
            f"{self.SERVICE}/search/shows/?q={urllib.parse.quote_plus(series)}"
        )
        response: requests.Response = requests.get(request)
        rjson: dict[Any, Any] = response.json()

        logging.debug("Series: %s\nRequest: %r\nResponse: %s", series, request, rjson)

        series_id: int = 0
        # If TVMaze returns an empty list, return 0.
        if not rjson:
            return series_id

        # If only one result, add it to the config and return the ID.
        if len(rjson) == 1:
            return rjson[0]["show"]["id"]

        # If multiple results, offer a means of selecting the correct one.
        # TODO: The nature of the picker should be left up to the frontend
        # implementation, but a console prompt is sufficient for now since the console
        # frontend will be the first (and maybe only) implementation.
        print(f"Search results for: {series}")
        for option, result in enumerate(rjson, start=1):
            name: str = result["show"]["name"]
            series_id: int = result["show"]["id"]
            premiered: int = result["show"]["premiered"]

            # All these ifs and try/except blocks look silly, but it's an order of
            # magnitude faster than reducing or using defaultdict
            if result["show"]["network"]:
                try:
                    network: str = result["show"]["network"].get("name", "Unknown")
                except (AttributeError, KeyError, TypeError):
                    network: str = "Unknown"

                try:
                    country: str = result["show"]["network"]["country"].get(
                        "name", "Unknown"
                    )
                except (AttributeError, KeyError, TypeError):
                    country: str = "Unknown"

            elif result["show"]["webChannel"]:
                try:
                    network: str = result["show"]["webChannel"].get("name", "Unknown")
                except (AttributeError, KeyError, TypeError):
                    network: str = "Unknown"

                try:
                    country: str = result["show"]["webChannel"]["country"].get(
                        "name", "Unknown"
                    )
                except (AttributeError, KeyError, TypeError):
                    country: str = "Unknown"

            else:
                network: str = "Unknown"
                country: str = "Unknown"

            print(
                f"{option}. {name} (Premiered: {premiered}, Network: {network}, Country: {country}, ID: {series_id})"
            )
        # TODO: Handle invalid selections.
        selection: int = int(input("Select series: ")) - 1

        # Add selected ID to config and return it.
        series_id = rjson[selection]["show"]["id"]

        return series_id

    def get_series_id_singlesearch(self, series: str) -> int:
        """Get the series ID from the TVMaze `singlesearch` endpoint, which returns a
        single result that it considers the best match.
        URL: /singlesearch/shows?q=:query
        """

        request: str = (
            f"{self.SERVICE}/singlesearch/shows/?q={urllib.parse.quote_plus(series)}"
        )
        response: requests.Response = requests.get(request)
        rjson: dict[Any, Any] = response.json()
        logger.debug("Media: %r\nRequest: %r\nResponse: %s", series, request, rjson)

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

        request: str = f"{self.SERVICE}/shows/{series_id}/episodebynumber?season={media.season}&number={media.episode}"
        response: requests.Response = requests.get(request)
        rjson: dict[Any, Any] = response.json()
        logging.debug("Media: %r\nRequest: %r\nResponse: %s", media, request, rjson)

        if response.ok:
            episode_title = str(rjson.get("name"))

        return episode_title

    def search_series(self, series: str, interactive: bool = True) -> dict[str, Any]:
        """Return a dictionary of information about a series."""

        request: str = (
            f"{self.SERVICE}/search/shows/?q={urllib.parse.quote_plus(series)}"
        )

        response: requests.Response = requests.get(request)
        rjson: dict[Any, Any] = response.json()

        if len(rjson) == 1 or not interactive:
            return rjson[0]["show"]

        for option, result in enumerate(rjson, start=1):
            name: str = result["show"]["name"]
            series_id: int = result["show"]["id"]
            premiered: int = result["show"]["premiered"]

            # All these ifs and try/except blocks look silly, but it's an order of
            # magnitude faster than reducing or using defaultdict
            if result["show"]["network"]:
                try:
                    network: str = result["show"]["network"].get("name", "Unknown")
                except (AttributeError, KeyError, TypeError):
                    network: str = "Unknown"

                try:
                    country: str = result["show"]["network"]["country"].get(
                        "name", "Unknown"
                    )
                except (AttributeError, KeyError, TypeError):
                    country: str = "Unknown"

            elif result["show"]["webChannel"]:
                try:
                    network: str = result["show"]["webChannel"].get("name", "Unknown")
                except (AttributeError, KeyError, TypeError):
                    network: str = "Unknown"

                try:
                    country: str = result["show"]["webChannel"]["country"].get(
                        "name", "Unknown"
                    )
                except (AttributeError, KeyError, TypeError):
                    country: str = "Unknown"

            else:
                network: str = "Unknown"
                country: str = "Unknown"

            print(
                f"{option}. {name} (Premiered: {premiered}, Network: {network}, Country: {country}, ID: {series_id})"
            )

        # TODO: Handle invalid selections.
        selection: int = int(input("Select series: "))

        return rjson[selection - 1]["show"]


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab textwidth=88
