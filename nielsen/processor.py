"""A collection of classes used to orchestrate combinations of Media and Fetcher
operations to be used by any frontend application.

Rather than creating individual Media instances of a specific subclass and a Fetcher
instance and manually calling all of their individual methods, Processors provide a
convenience method (process) which creates a Media instance of the desired type and
handles all changes to that Media instance."""

import pathlib
from dataclasses import dataclass
from enum import Enum
from typing import Any

import nielsen.fetcher
import nielsen.media
from nielsen.config import config


class MediaType(str, Enum):
    TV = "tv"


@dataclass
class Processor[M: nielsen.media.Media]:
    """A convenience class to handle all the Media and Fetcher operations required to
    manage an individual file. The `media_type` is a Media class and is used to
    construct instances of the given type. The `fetcher` is an instance of an object
    implementing the `Fetcher` Protocol."""

    media_type: type[M]
    fetcher: nielsen.fetcher.Fetcher[M]

    def process(self, path: pathlib.Path) -> M:
        """Convenience function to process Media for storage in its library, respecting the configuration
        options (so some steps may be skipped).
        1. Infer metadata based on the Media type.
        2. Fetch missing data.
        3. Rename the file.
        4. Move the file to the appropriate directory.
        5. Modify file ownership and mode.
        """

        # Create an instance of the appropriate Media subclass
        media: M = self.media_type(path)

        media.infer()

        if config.getboolean(media.section, "fetch"):
            self.fetcher.fetch(media)

        if config.getboolean(media.section, "rename"):
            media.rename()

        if config.getboolean(media.section, "organize"):
            media.organize()

        return media


@dataclass
class ProcessorFactory[M: nielsen.media.Media]:
    """A Factory class for Processors. Given a Media and Fetcher class, calling an
    instance of this Factory will return a Processor with the given Media class and
    Fetcher instance."""

    media_type: type[M]
    fetcher: type[nielsen.fetcher.Fetcher[M]]

    def __call__(self) -> Processor[M]:
        """Return a Processor for the given types."""

        return Processor(self.media_type, self.fetcher())


PROCESSOR_FACTORIES: dict[MediaType, ProcessorFactory[Any]] = {
    MediaType.TV: ProcessorFactory(nielsen.media.TV, nielsen.fetcher.TVMaze),
}
