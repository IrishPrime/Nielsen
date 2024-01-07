#!/usr/bin/env python3
"""Subcommands for managing TV shows with Nielsen."""

import logging
from pathlib import Path
from typing_extensions import Annotated

import nielsen.config
import nielsen.fetcher
import nielsen.media
from nielsen.config import config as config

import typer
from rich.pretty import pprint


logger: logging.Logger = logging.getLogger(__name__)
nielsen.config.load_config()

app: typer.Typer = typer.Typer(name="TV")


@app.command()
def series(
    interactive: Annotated[bool, typer.Option()],
    series: Annotated[list[str], typer.Argument(help="Show title to search for")],
) -> None:
    """Search for a TV series by title."""

    flattened: str = " ".join(series)
    media: nielsen.media.TV = nielsen.media.TV(Path("/dev/null"), series=flattened)
    fetcher: nielsen.fetcher.TVMaze = nielsen.fetcher.TVMaze()

    fetcher.get_series_id_search(media)


if __name__ == "__main__":
    app()
