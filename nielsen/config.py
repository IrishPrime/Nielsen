"""Interact with configuration files and objects."""

import logging
import pathlib
from configparser import ConfigParser
from typing import Optional

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

config: ConfigParser = ConfigParser(converters={"path": pathlib.Path})
# Set default options
config["DEFAULT"] = {
    # Dry Run - Outputs results without actually modifying files
    "dryrun": "False",
    # Fetch - Whether to query remote sources for information
    "fetch": "True",
    # Filter - Whether to refer to the <type>/filter section when organizing Media
    "filter": "True",
    # Interactive - Whether to prompt the user to make decisions while processing
    "interactive": "True",
    # Library - The directory under which Media should be organized
    "library": str(pathlib.Path.home()),
    # LogFile - The file to which log messages should be written
    "logfile": "~/.local/log/nielsen/nielsen.log",
    # LogLevel - The minimum log-level to display
    "loglevel": "WARNING",
    # Mode - The file mode (permissions) to set on Media files during processing
    "mode": "664",
    # Organize - Whether to move Media to its library directory
    "organize": "True",
    # Rename - Whether to rename individual Media files
    "rename": "True",
}


def load_config(path: Optional[pathlib.Path] = None) -> ConfigParser:
    """Load a configuration from a file. If no file path is provided, default
    configuration file locations are used. Returns a ConfigParser object."""

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

    with open(path, mode="w") as file:
        config.write(file)


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
