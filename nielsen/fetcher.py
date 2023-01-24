"""Fetchers are used to query remote sources for metadata about a given Media object."""

from abc import abstractmethod
from typing import Any
from typing import Optional
from typing import Protocol
import logging
import requests

import nielsen.media

from nielsen.config import config

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


class Fetcher(Protocol):
    """Used to fetch metadata from an external source rather than infering it from the
    file name."""

    @abstractmethod
    def fetch(self, media: nielsen.media.Media) -> dict[str, Any]:
        """Fetch and update metadata using information from the given `Media` object."""


class TVMaze:
    """Fetch metadata for TV shows using the TVMaze API."""

    SERVICE: str = "https://api.tvmaze.com"
    IDS: str = "tvmaze/ids"

    def __init__(self):
        pass

    def fetch(self, media: nielsen.media.TV) -> dict[str, Any]:
        """Fetch metadata from TVMaze. Update and return the provided dictionary."""
        ...

    def get_series_id(
        self, media: nielsen.media.TV, interactive: bool = False
    ) -> Optional[int]:
        """Return the TVMaze ID for the series. Will check for a local config file first
        and search TVMaze if a local match isn't found. Optionally, prompt the user to
        select the correct series interactively if multiple results are found."""

        if config.has_section(self.IDS) and config.has_option(self.IDS, media.series):
            lookup = self.get_series_id_local
        elif interactive:
            lookup = self.get_series_id_search
        else:
            lookup = self.get_series_id_singlesearch

        return lookup(media)

    def get_series_id_local(self, media: nielsen.media.TV) -> Optional[int]:
        """Get the series ID from the configuration."""

        return config.getint(self.IDS, media.series)

    def get_series_id_search(self, media: nielsen.media.TV) -> Optional[int]:
        """Get the series ID from the TVMaze `search` endpoint, which can return
        multiple results. If multiple results are returned, prompt the user to pick one."""

        # TODO: The nature of the picker should be left up to the frontend
        # implementation, but a console prompt is sufficient for now since the console
        # frontend will be the first (and maybe only) implementation.
        request: str = f"{self.SERVICE}/search/shows/?q={media.series}"
        resp: requests.Response = requests.get(request)

        logging.debug(
            "Media: %r\nRequest: %r\nResponse: %s", media, request, resp.json()
        )

        # If only one result, just return its ID
        if len(resp.json()) == 1:
            return resp.json()[0]["show"]["id"]

        print(f"Search results for: {media.series}")
        for option, result in enumerate(resp.json()):
            name: str = result["show"]["name"]
            id: int = result["show"]["id"]
            premiered: int = result["show"]["premiered"]
            print(f"{option}. {name} (ID: {id}, Premiered: {premiered})")

        # TODO: Handle invalid selections.
        selection: int = int(input("Select series: "))

        return resp.json()[selection]["show"]["id"]

    def get_series_id_singlesearch(self, media: nielsen.media.TV) -> Optional[int]:
        """Get the series ID from the TVMaze `singlesearch` endpoint, which returns a
        single result that it considers the best match."""

        request: str = f"{self.SERVICE}/singlesearch/shows/?q={media.series}"
        resp: requests.Response = requests.get(request)

        logging.debug(
            "Media: %r\nRequest: %r\nResponse: %s", media, request, resp.json()
        )

        return resp.json()["id"]

    def get_episode_title(self, media):
        """Return the episode title for the given media object."""

    def select_series(self, media):
        """Interactively select the correct series from a list of search results."""
