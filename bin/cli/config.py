#!/usr/bin/env python3
"""Subcommands for interacting with Nielsen's configuration."""

import logging

import nielsen.config
from nielsen.config import config as cfg

import typer
from rich.pretty import pprint

logger: logging.Logger = logging.getLogger(__name__)
nielsen.config.load_config()

app: typer.Typer = typer.Typer()


@app.command()
def dump() -> None:
    """Dump the current configuration."""

    typer.echo("Configuration")
    typer.echo(cfg.default_section)
    pprint(cfg.defaults(), expand_all=True)

    for section in cfg.sections():
        typer.echo(section)
        pprint(cfg.items(section))


if __name__ == "__main__":
    app()
