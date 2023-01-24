"""Class defintitions for Media types.

`Media` objects represent a file to be managed and its metadata. The `Media` class
itself is a base class from which subtypes should be derived. It provides an interface
and some template methods for its subtypes, but is generally not very useful on its own.

`Media.library`: A `pathlib.Path` that represents the root location a `Media` object
should be moved to when `Media.organize()` is called.

`Media.path`: A `pathlib.Path` that represents the actual location of the file on disk.
This value is optional, and falsey values should set it to `None`.

`Media.infer()`: A method that attempts to infer metadata about the file (e.g. from its
filename) and updates the appropriate metadata attributes with this information.

`Media.organize()`: A method that attempts to move the file to a new location, updates the
`path` attribute on success, and returns this new value.

`Media.metadata`: A property that returns all metadata as a dictionary, intended for
ease of inspection and discovery.
"""

import logging
import pathlib
import re
from dataclasses import dataclass, field
from typing import Any, Optional, Pattern

from nielsen.config import config

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass(slots=True)
class Media:
    """Media objects represent a file to be managed and its metadata."""

    path: Optional[pathlib.Path] = None
    patterns: list[Pattern] = field(
        default_factory=list,
        init=False,
        repr=False,
        hash=False,
        compare=False,
        metadata=None,
    )
    _section: str = field(
        init=False,
        repr=False,
        hash=False,
        compare=False,
        metadata=None,
    )
    _library: pathlib.Path = field(
        init=False,
        repr=False,
        hash=False,
        compare=False,
        metadata=None,
    )
    _metadata: dict[str, Any] = field(
        default_factory=dict,
        init=False,
        repr=True,
        hash=True,
        compare=True,
        metadata=None,
    )

    def __post_init__(self):
        """Modify instance after initialization."""

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

        # Load filename patterns for the type.
        self.load_patterns()

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

    def load_patterns(self) -> None:
        """Load filename patterns for the instance type into the patterns property."""

        self._load_patterns()
        logger.debug("Loaded %s patterns.", self.__class__.__name__)

    def _load_patterns(self) -> None:
        """Should only be called directly by the `load_patterns` method."""

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

    def infer(self) -> None:
        """Infer information about the object's metadata based on its filename. Does
        some basic error checking and then sets the various metadata fields using the
        `metadata.setter` method which each subclass must implement to handle value
        transformations and/or formatting."""

        if not self.path:
            logger.error("NO_PATH: No path from which to infer.")
            logger.debug(repr(self))
            return

        if not self.patterns:
            logger.error("NO_PATTERNS: No patterns defined to match against.")
            logger.debug(repr(self))
            return

        metadata: dict[str, Any] = self._match()
        self.metadata = metadata

    def _match(self) -> dict[str, Any]:
        """Return the results of `Match.groupdict()` if the filename matched any of the
        patterns. Should only be called by `infer()`."""

        # Assert values here which have already been checked by Media.infer to avoid
        # type errors from the linter.
        assert self.path

        for pattern in self.patterns:
            match = pattern.fullmatch(self.path.name)
            if match:
                return match.groupdict()

        logger.info("NO_MATCH: %s did not match any filename patterns.", self.path.name)
        return {}

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
                    "CANNOT_ORGANIZE: Library directory does not exist and could not be created: %s",
                    self.library,
                )
                raise

        logger.info("Move %s to %s.", self.path.name, self.library)
        # TODO: Don't rename files without metadata
        self.path = self.path.rename(self.library / self.path.name).resolve()
        logger.debug("New path: %s", self.path)

        return self.path

    @property
    def metadata(self) -> dict[str, Any]:
        """Return the metadata property, a dictionary of information relevant to the
        Media type."""

        return self._get_metadata()

    def _get_metadata(self):
        """Override in subclasses."""

        raise NotImplementedError

    @metadata.setter
    def metadata(self, value: dict[str, Any]) -> None:
        """Set the metadata property. Must be a dictionary, but subclasses should
        implement their own transformations (if any) by implementing the set_metadata
        method."""

        self._set_metadata(value)

    def _set_metadata(self, metadata: dict[str, Any]) -> bool:
        """Override in subclasses."""

        raise NotImplementedError

    def transform(self, field: str) -> str:
        """Transform a field's value based on the corresponding config section. For
        example, passing `field=series` for a `TV` object will look for an option in the
        `tv/series/transform` section of the config matching `self.series`. If found,
        `self.series` will be replaced with the option value. If not found, nothing
        changes."""

        section: str = f"{self.section}/{field}/transform"
        option: str = getattr(self, field)

        # Create the corresponding transform sub-section if it doesn't exist.
        if not config.has_section(section):
            logger.warning("NO_TRANSFORM_SECTION: %s", section)
            return option

        if not config.has_option(section, option):
            logger.warning("NO_TRANSFORM_OPTION: %s", option)
            return option

        transformed: str = config.get(section, option)
        logger.info("TRANSFORM: %s to %s", option, transformed)
        return transformed


@dataclass(order=True, slots=True)
class TV(Media):
    """A Media subclass for TV shows."""

    series: str = ""
    season: int = 0
    episode: int = 0
    title: str = ""

    def _load_patterns(self) -> None:
        """Load filename patterns for the instance type into the patterns property."""

        self.patterns = [
            # The.Flash.2014.217.Flash.Back.HDTV.x264-LOL[ettv].mp4
            re.compile(
                r"(?P<series>.+)\.+(?P<year>\d{4})\.(?P<season>\d{1,2})(?P<episode>\d{2})\.*(?P<title>.*)?\.+(?P<extension>\w+)$",
                re.IGNORECASE,
            ),
            # The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi
            re.compile(
                r"(?P<series>.+)\.+S(?P<season>\d{2})\.?E(?P<episode>\d{2})\.*(?P<title>.*)?\.+(?P<extension>\w+)$",
                re.IGNORECASE,
            ),
            # the.glades.201.family.matters.hdtv.xvid-fqm.avi
            re.compile(
                r"(?P<series>.+)\.+S?(?P<season>\d{1,})\.?E?(?P<episode>\d{2,})\.*(?P<title>.*)?\.+(?P<extension>\w+)$",
                re.IGNORECASE,
            ),
            # The Glades -02.01- Family Matters.avi
            re.compile(
                r"(?P<series>.+)\s+-(?P<season>\d{2})\.(?P<episode>\d{2})-\s*(?P<title>.*)\.(?P<extension>.+)$"
            ),
            # The Glades -201- Family Matters.avi
            re.compile(
                r"(?P<series>.+[^\s-])[\s-]+(?P<season>\d{1,2})(?P<episode>\d{2,})[\s-]+(?P<title>.*)\.(?P<extension>.+)$"
            ),
            # Last ditch effort to get essential information
            re.compile(
                r"(?P<series>.+)S(?P<season>\d{1,2})E(?P<episode>\d{2,}).*\.(?P<extension>.+)$"
            ),
        ]

    def _get_metadata(self) -> dict[str, Any]:
        """Return a dictionary of metadata relevant to the TV type."""

        return {
            "series": self.series,
            "season": self.season,
            "episode": self.episode,
            "title": self.title,
        }

    def _set_metadata(self, metadata: dict[str, Any]) -> None:
        """Transform values from the given metadata dictionary and use it to set the
        object's fields."""

        self.series = metadata["series"].replace(".", " ").strip()
        self.series = self.transform("series")
        self.season = int(metadata["season"])
        self.episode = int(metadata["episode"])
        self.title = metadata["title"].replace(".", " ").strip()

    def __str__(self) -> str:
        """Return a friendly, human-readable version of the file metadata, fit for
        renaming or display purposes."""

        return f"{self.series or 'Unknown'} -{self.season:02d}.{self.episode:02d}- {self.title or 'Unknown'}"

    def __repr__(self) -> str:
        """Return a string with enough information to recreate the object."""

        return f"<{self.__class__.__name__}({self.path=}, {self.series=}, {self.season=}, {self.episode=}, {self.title=})>"


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
