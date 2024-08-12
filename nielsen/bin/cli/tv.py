#!/usr/bin/env python3
"""Subcommands for managing TV shows with Nielsen."""

import logging
from pathlib import Path
from typing import Any, Optional
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
def info(
    series: Annotated[
        Optional[str], typer.Option(help="Show title to search for")
    ] = None,
    series_id: Annotated[
        Optional[int], typer.Option(help="The TVMaze series ID")
    ] = None,
    season: Annotated[
        Optional[int],
        typer.Option(help="Season number (to get additional details)"),
    ] = None,
    episode: Annotated[
        Optional[int],
        typer.Option(help="Episode number (to get additional details)"),
    ] = None,
    interactive: Annotated[
        bool,
        typer.Option(
            is_flag=True,
            help="Interactively select from multiple results",
        ),
    ] = True,
) -> None:
    """Search for a TV series by title."""

    if series and series_id:
        typer.echo("The --series and --series-id options are mutually exclusive.")
        raise typer.Exit(1)
    elif not (series or series_id):
        typer.echo("One of --series or --series-id required.")
        raise typer.Exit(2)

    if episode and not season:
        typer.echo("Cannot fetch episode information without a season.")
        raise typer.Exit(3)

    fetcher: nielsen.fetcher.TVMaze = nielsen.fetcher.TVMaze()

    if series:
        series_id = fetcher.get_series_id(series, interactive)

    if series_id and season and episode:
        typer.echo("Get additional information for the episode")

    elif series_id and season:
        typer.echo("Get additional information for the season")

    elif series_id:
        typer.echo(f"{series_id=}")


if __name__ == "__main__":
    app()
