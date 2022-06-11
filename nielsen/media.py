"""Class defintitions for all Media types."""

from abc import ABC
from abc import abstractmethod
from dataclasses import dataclass
from typing import Optional
import logging
import pathlib


@dataclass(slots=True)
class Media(ABC):
    """Media objects represent a file to be managed and its metadata."""

    path: Optional[pathlib.Path | str]

    def __post_init__(self):
        if not self.path:
            self.path = None
        elif self.path and not isinstance(self.path, pathlib.Path):
            logging.debug("Convert %s to pathlib.Path", self.path)
            self.path = pathlib.Path(self.path)

    @abstractmethod
    def infer(self):
        """Infer information about the object's metadata based on its filename."""

    @abstractmethod
    def organize(self):
        """Move the file to the appropriate media library on disk."""


@dataclass(order=True, slots=True)
class TV(Media):
    """A class just for TV shows."""

    series: str = ""
    season: int = 0
    episode: int = 0
    title: str = ""

    def infer(self):
        self.series = "The Wheel of Time"
        self.season = 1
        self.episode = 8
        self.title = "The Eye of the World"

    def organize(self) -> pathlib.Path:
        """Move the file to the TV media library location."""
        return pathlib.Path(f"/tmp/organized/{self}")

    def __str__(self) -> str:
        """Return a friendly, human-readable version of the file metadata, fit for
        renaming or display purposes."""

        return f"{self.series} -{self.season:02d}.{self.episode:02d}- {self.title}"


# vim: et ts=4 sts=4 sw=4
