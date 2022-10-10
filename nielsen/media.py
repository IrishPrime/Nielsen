"""Class defintitions for all Media types."""

import logging
import pathlib
from dataclasses import dataclass, field
from typing import Any, Optional

from nielsen.config import config

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass(slots=True)
class Media:
    """Media objects represent a file to be managed and its metadata."""

    path: Optional[pathlib.Path] = None
    _section: str = field(
        init=False, repr=False, hash=False, compare=False, metadata=None
    )
    _library: pathlib.Path = field(
        init=False, repr=False, hash=False, compare=False, metadata=None
    )

    def __post_init__(self):
        if isinstance(self.path, pathlib.Path):
            self.path = self.path.resolve()
        else:
            self.path = None

        # By default, instances of a subclass should use the section of the config
        # corresponding to their type name.
        self.section = self.__class__.__name__.lower()

        # Similarly, the library should be pulled from the section of the config
        # corresponding to the type name.
        self.library = config.getpath(self.section, "library").resolve()  # type: ignore

    @property
    def library(self) -> pathlib.Path:
        """Return a Path object representing the root of the library for the Media type
        from the config."""

        return self._library

    @library.setter
    def library(self, value: pathlib.Path) -> None:
        """Set the library property. Attempt to coerce the value to a Path if not
        provided as such."""

        if not isinstance(value, pathlib.Path):
            try:
                value = pathlib.Path(value)
            except TypeError:
                logger.exception("Could not coerce value to Path: %s", repr(value))
                raise

        self._library = value.resolve()

    @property
    def section(self) -> str:
        """Return a string denoting which section of the ConfigParser this Media should
        refer to when looking for its options."""

        return self._section

    @section.setter
    def section(self, value: str) -> None:
        """Set the section in the ConfigParser to refer to for options."""

        if not config.has_section(value):
            config.add_section(value)

        self._section = value

    def infer(self) -> dict[str, Any]:
        """Infer information about the object's metadata based on its filename."""

        raise NotImplementedError

    def organize(self) -> pathlib.Path:
        """Move the file to the appropriate media library on disk."""

        if not isinstance(self.path, pathlib.Path):
            logger.error("Path attribute is not of type Path: %s", self.path)
            raise TypeError(self.path)

        if not self.path.is_file():
            logger.error(
                "Path attribute does not point to a regular file: %s", self.path
            )
            raise TypeError(self.path)

        if not self.library.is_dir():
            try:
                self.library.mkdir(exist_ok=True)
            except (PermissionError, NotADirectoryError):
                logger.exception(
                    "Library directory does not exist and could not be created: %s",
                    self.library,
                )
                raise

        logger.info("Move %s to %s.", self.path.name, self.library)
        self.path = self.path.rename(self.library / self.path.name).resolve()
        logger.debug("New path: %s", self.path)

        return self.path


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

    def __str__(self) -> str:
        """Return a friendly, human-readable version of the file metadata, fit for
        renaming or display purposes."""

        return f"{self.series} -{self.season:02d}.{self.episode:02d}- {self.title}"


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
