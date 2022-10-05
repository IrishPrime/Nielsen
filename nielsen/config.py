"""Interact with configuration files and objects."""

import logging
import pathlib
from configparser import ConfigParser
from typing import Optional

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

config: ConfigParser = ConfigParser()


def load_config(path: Optional[pathlib.Path] = None) -> ConfigParser:
    """Load a configuration from a file. If no file path is provided, default
    configuration file locations are used. Returns a ConfigParser object."""

    # Set some default options
    config.set(config.default_section, "dryrun", "False")
    config.set(config.default_section, "fetch", "True")
    config.set(config.default_section, "filter", "True")
    config.set(config.default_section, "interactive", "True")
    config.set(config.default_section, "logfile", "~/.local/log/nielsen/nielsen.log")
    config.set(config.default_section, "loglevel", "WARNING")
    config.set(config.default_section, "mediapath", str(pathlib.Path.home()))
    config.set(config.default_section, "mode", "664")
    config.set(config.default_section, "organize", "True")

    if not path:
        files: list[str] = config.read(
            [
                "/etc/nielsen/config.ini",
                pathlib.Path("~/.config/nielsen/config.ini").expanduser(),
                pathlib.Path("~/.nielsen/config.ini").expanduser(),
            ]
        )
        logger.debug("Loaded configuration from default locations: %s", files)
    else:
        files: list[str] = config.read(str(path))
        if files:
            logger.debug("Loaded configuration from: %s", files)
        else:
            logger.error("Failed to load configuration from: %s", path)

    return config


def write_config(path: pathlib.Path) -> None:
    """Write the global configuration object to the given `path`."""

    with open(path, "w") as fp:
        config.write(fp)


# vim: et ts=4 sts=4 sw=4
