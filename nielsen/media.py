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


# vim: et ts=4 sts=4 sw=4
