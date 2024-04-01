#!/usr/bin/env python3
"""Subcommands for interacting with Nielsen's configuration."""

import logging

import nielsen.config
from nielsen.config import config as config

import typer
from rich.pretty import pprint

logger: logging.Logger = logging.getLogger(__name__)
nielsen.config.load_config()

app: typer.Typer = typer.Typer()


@app.command()
def dump() -> None:
    """Dump the current configuration."""

    typer.echo("Configuration")
    typer.echo(config.default_section)
    pprint(config.defaults(), expand_all=True)

    for section in config.sections():
        typer.echo(section)
        pprint(config.items(section))


if __name__ == "__main__":
    app()
