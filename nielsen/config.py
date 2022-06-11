"""Interact with configuration files and objects."""

from configparser import ConfigParser
from typing import Optional
import pathlib

config: ConfigParser = ConfigParser()


def load_config(path: Optional[pathlib.Path] = None) -> ConfigParser:
    """Load a configuration from a file. If no file path is provided, default
    configuration file locations are used. Returns a ConfigParser object."""

    if not path:
        config.read(
            [
                "/etc/nielsen/config.ini",
                pathlib.Path("~/.nielsen/config.ini").expanduser(),
            ]
        )
    else:
        config.read(path)

    return config


def write_config(path: pathlib.Path) -> None:
    """Write the global configuration object to the given `path`."""


# vim: et ts=4 sts=4 sw=4
