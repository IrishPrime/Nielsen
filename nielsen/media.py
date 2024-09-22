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

`Media.organize()`: A method that attempts to move the file to a new location, updates
the `path` attribute on success, and returns this new value.

`Media.metadata`: A property that returns all metadata as a dictionary, intended for
ease of inspection and discovery.
"""

import logging
import pathlib
import re
from dataclasses import dataclass, field
from shutil import chown, move
from string import capwords
from typing import Any, Pattern

from nielsen.config import config

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


@dataclass(slots=True)
class Media:
    """Media objects represent a file to be managed and its metadata."""

    patterns: list[Pattern] = field(
        default_factory=list,
        init=False,
        repr=False,
        hash=False,
        compare=False,
        metadata=None,
    )
    _path: pathlib.Path = field(
        hash=True,
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

        # Set the path again to run it through the property setter
        self.path = self.path

        # By default, instances of a subclass should use the section of the config
        # corresponding to their type name.
        self.section = self.__class__.__name__.lower()

        # Similarly, the library should be pulled from the section of the config
        # corresponding to the type name.
        self.library = config.getpath(self.section, "library").resolve()  # type: ignore

        # Load filename patterns for the type.
        self.load_patterns()

    @property
    def path(self) -> pathlib.Path:
        """Return a Path object representing the Media file on disk."""

        return self._path

    @path.setter
    def path(self, value: pathlib.Path | str) -> None:
        """Set the path property. Attempt to coerce the value to a Path if not
        provided as such."""

        try:
            if not isinstance(value, pathlib.Path):
                value = pathlib.Path(value)

                # TODO Do not allow non-files
                if not value.is_file():
                    raise TypeError(repr(value))
        except TypeError:
            logger.exception("Media.path must be a file: %s", repr(value))
            raise

        self._path = value.resolve()

    @property
    def library(self) -> pathlib.Path:
        """Return a Path object representing the root of the library for the Media type
        from the config."""

        return self._library

    @library.setter
    def library(self, value: pathlib.Path | str) -> None:
        """Set the library property. Attempt to coerce the value to a Path if not
        provided as such."""

        try:
            if not isinstance(value, pathlib.Path):
                value = pathlib.Path(value)

            if not value.is_dir():
                raise TypeError(repr(value))
        except TypeError:
            logger.exception("Media.library must be a directory: %s", repr(value))
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

    @property
    def orgdir(self) -> pathlib.Path:
        """Return the orgdir property."""

        raise NotImplementedError

    def infer(self) -> None:
        """Infer information about the object's metadata based on its filename. Does
        some basic error checking and then sets the various metadata fields using the
        `metadata.setter` method which each subclass must implement to handle value
        transformations and/or formatting."""

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
        """Move the file to the appropriate media library on disk, set file ownership
        and mode."""

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

        # Ensure the orgdir exists and move the file there.
        logger.info("Move %s → %s/.", self.path.name, self.orgdir)
        if not config.getboolean("nielsen", "simulate"):
            self.orgdir.mkdir(exist_ok=True, parents=True)
            self.path = pathlib.Path(
                move(self.path, self.orgdir / self.path.name)
            ).resolve()
            logger.debug("New path: %s", self.path)

        self.path.chmod(int(config.get(self.section, "mode"), 8))

        # If chown gets a None value for user or group, it won't modify the existing
        # values. Use None as a fallback to leave things alone unless the user has
        # explicitly set a different value in their configuration.
        user: str | None = config.get(self.section, "owner", fallback=None)
        group: str | None = config.get(self.section, "group", fallback=None)

        if user or group:
            chown(self.path, user, group)  # type: ignore

        return self.path

    @property
    def metadata(self) -> dict[str, Any]:
        """Return the metadata property, a dictionary of information relevant to the
        Media type."""

        raise NotImplementedError

    @metadata.setter
    def metadata(self, metadata: dict[str, Any]) -> None:
        """Set the metadata property. Must be a dictionary, but subclasses should
        implement their own transformations (if any) by implementing this setter
        method."""

        raise NotImplementedError

    # This implementation may not be especially useful for base Media objects, but it
    # provides a sensible default implementation other classes are free to use,
    # extend, or override.
    def rename(self) -> pathlib.Path:
        """Rename the file associated with this Media object to match its `str`
        representation, but do not change its parent directory. Return the new location
        as a Path object."""

        if not self.path or not self.path.exists():
            raise FileNotFoundError(self.path)

        simulate: bool = config.getboolean("nielsen", "simulate")
        dest: pathlib.Path = self.path.with_stem(f"{self!s}")
        logger.info("Renaming %s → %s. Simulate: %s", self.path, dest, simulate)

        # TODO: Raise an exception file destination conflicts
        # TODO: Handle exception on the client side
        if dest.exists():
            if self.path.samefile(dest):
                logger.info("File already named correctly.")
            else:
                logger.warning("FILE_CONFLICT: %s already exists.", dest)

            return self.path

        if not simulate:
            self.path = self.path.rename(dest)

        return self.path

    def transform(self, field: str) -> str:
        """Transform a field's value based on the corresponding config section. For
        example, passing `field=series` for a `TV` object will look for an option in the
        `tv/transform/series` section of the config matching `self.series`. If found,
        `self.series` will be replaced with the option value. If not found, nothing
        changes."""

        section: str = f"{self.section}/transform/{field}"
        option: str = getattr(self, field)

        # Create the corresponding transform sub-section if it doesn't exist.
        if not config.has_section(section):
            logger.warning("NO_TRANSFORM_SECTION: %s", section)
            return option

        if not config.has_option(section, option):
            logger.warning("NO_TRANSFORM_OPTION: %s", option)
            return option

        transformed: str = config.get(section, option)
        logger.info("TRANSFORM: %s → %s", option, transformed)

        return transformed

    def __str__(self) -> str:
        """Return a friendly, human-readable version of the file path, fit for
        renaming or display purposes."""

        return f"{self.path.resolve()!s}"


@dataclass(order=True, slots=True)
class TV(Media):
    """A Media subclass for TV shows."""

    series: str = ""
    series_id: int = 0
    season: int = 0
    episode: int = 0
    title: str = ""

    def _load_patterns(self) -> None:
        """Load filename patterns for the instance type into the patterns property."""

        self.patterns = [
            # The.Glades.S02E01.Family.Matters.HDTV.XviD-FQM.avi
            re.compile(
                r"(?P<series>.+?)\.+(?P<year>\d{4}|\(\d{4}\))?\.*S(?P<season>\d{2})\.?E(?P<episode>\d{2})\.*(?P<title>.*)?\.+(?P<extension>\w+)$",
                re.IGNORECASE,
            ),
            # The.Flash.2014.217.Flash.Back.HDTV.x264-LOL[ettv].mp4
            re.compile(
                r"(?P<series>.+?)\.+(?P<year>\d{4}|\(\d{4}\))?\.(?P<season>\d{1,2})(?P<episode>\d{2})\.*(?P<title>.*)?\.+(?P<extension>\w+)$",
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
                r"(?P<series>.+)S(?P<season>\d{1,2})E(?P<episode>\d{2,})(?P<title>.*)\.(?P<extension>.+)$"
            ),
        ]

    @property
    def metadata(self) -> dict[str, Any]:
        """Return a dictionary of metadata relevant to the TV type."""

        return {
            "series": self.series,
            "season": self.season,
            "episode": self.episode,
            "title": self.title,
        }

    @metadata.setter
    def metadata(self, metadata: dict[str, Any]) -> None:
        """Transform values from the given metadata dictionary and use it to set the
        object's fields."""

        self.series = metadata.get("series", "").replace(".", " ").strip().title()
        self.series = self.transform("series")
        self.season = int(metadata.get("season", 0))
        self.episode = int(metadata.get("episode", 0))
        self.title = metadata.get("title", "").replace(".", " ").strip()

        tags: re.Pattern = re.compile(
            r"\(?(1080p|720p|HDTV|WEB|PROPER|REPACK|RERIP)\)?.*", re.IGNORECASE
        )
        # Use string.capwords() rather than str.title() to properly handle letters after apostrophes.
        self.title = capwords(re.sub(tags, "", self.title).strip())

    @property
    def orgdir(self) -> pathlib.Path:
        """Return the orgdir property."""

        return pathlib.Path(self.library / f"{self.series}/Season {self.season:02d}/")

    def __str__(self) -> str:
        """Return a friendly, human-readable version of the file metadata, fit for
        renaming or display purposes."""

        return f"{self.series or 'Unknown'} -{self.season:02d}.{self.episode:02d}- {self.title or 'Unknown'}"

    def __repr__(self) -> str:
        """Return a string with enough information to recreate the object."""

        return f"<{self.__class__.__name__}({self.path=}, {self.series=}, {self.season=}, {self.episode=}, {self.title=})>"


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab textwidth=88
