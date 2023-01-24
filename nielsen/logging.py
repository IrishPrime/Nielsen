"""Logging configuration for use in the various Nielsen modules."""

import logging

logging.basicConfig(
    format="[%(filename)s][%(funcname)s][%(levelname)-8s]%(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
