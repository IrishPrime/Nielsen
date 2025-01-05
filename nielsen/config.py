"""Interact with configuration files and objects."""

import logging
import pathlib
from configparser import ConfigParser
from typing import Optional

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())

CONFIG_FILE_LOCATIONS: list[str | pathlib.Path] = [
    "/etc/nielsen/config.ini",
    pathlib.Path("~/.config/nielsen/config.ini").expanduser(),
]

# Add a getpath converter.
config: ConfigParser = ConfigParser(
    converters={"path": pathlib.Path}, default_section="nielsen"
)

# Set default options
config[config.default_section] = {
    # Dry Run - Outputs results without actually modifying files
    "simulate": "False",
    # Fetch - Whether to query remote sources for information
    "fetch": "True",
    # Transform - Whether to refer to the <type>/<field>/transform section when organizing Media
    "transform": "True",
    # Interactive - Whether to prompt the user to make decisions while processing
    "interactive": "True",
    # Library - The directory under which Media should be organized
    "library": str(pathlib.Path.home()),
    # LogFile - The file to which log messages should be written
    "logfile": "~/.local/log/nielsen/nielsen.log",
    # LogLevel - The minimum log-level to display
    "loglevel": "WARNING",
    # Mode - The file mode (permissions) to set on Media files during processing
    "mode": "644",
    # Organize - Whether to move Media to its library directory
    "organize": "True",
    # Rename - Whether to rename individual Media files
    "rename": "True",
}


def load_config(path: Optional[pathlib.Path] = None) -> list[str]:
    """Load a configuration from a file into the global configuration object. If no file
    path is provided, default configuration file locations are used. Returns a list of
    files loaded."""

    global config
    files: list[str]

    if not path:
        files = config.read(CONFIG_FILE_LOCATIONS)
        logger.debug("Loaded configuration from default locations: %s", files)
    else:
        files = config.read(str(path))
        if files:
            logger.debug("Loaded configuration from: %s", files)
        else:
            logger.error("Failed to load configuration from: %s", path)

    return files


def write_config(path: pathlib.Path) -> None:
    """Write the global configuration object to the given `path`."""

    global config

    with open(path, mode="w") as file:
        config.write(file)


def update_config(path: pathlib.Path) -> None:
    """Write new data to the config file without changing options already present in the
    config files. By re-reading the config files before writing, runtime options or
    other dynamic changes to the config will be reverted before the file is written."""

    load_config(path.expanduser())
    write_config(path.expanduser())


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
