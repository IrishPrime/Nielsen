#!/usr/bin/env python3
"""Subcommands for managing TV shows with Nielsen."""

import logging
from pathlib import Path
from typing import Any, Callable, Optional

import typer
from requests import Response
from rich.pretty import pprint
from typing_extensions import Annotated

import nielsen.config
import nielsen.fetcher
import nielsen.media
from nielsen.config import config as config

logger: logging.Logger = logging.getLogger(__name__)
config_files: list[str] = nielsen.config.load_config()

app: typer.Typer = typer.Typer(name="TV")


@app.command(no_args_is_help=True)
def fetch(
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
    raw: Annotated[
        bool,
        typer.Option(is_flag=True, help="Print the JSON formatted API response"),
    ] = False,
) -> None:
    """Fetch information about a TV show. The more information provided to the command,
    the more specific the returned results."""

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
        # Create a TV instance with a dummy path and attach metadata to it for the
        # Fetcher to work with
        response: Response = fetcher.episodebynumber(series_id, season, episode)
        data: dict[str, Any] = response.json()

        if raw:
            pprint(data)
        else:
            fetcher.pretty_episode(data)

    elif series_id and season:
        season_id: int = fetcher.get_season_id(series_id, season)
        response: Response = fetcher.seasons_episodes(season_id)
        data: dict[str, Any] = response.json()

        if raw:
            pprint(data)
        else:
            fetcher.pretty_season(data)

    elif series_id:
        response: Response = fetcher.shows(series_id)
        data: dict[str, Any] = response.json()

        if raw:
            pprint(data)
        else:
            fetcher.pretty_series(data)

    else:
        logger.critical("Could not fetch any information.")
        raise typer.Exit(4)

    if response.ok:
        nielsen.config.update_config(Path(config_files[-1]))

@app.command(no_args_is_help=True)
def apply() -> None:

if __name__ == "__main__":
    app()
