#!/usr/bin/env python3
"""Subcommands for managing TV shows with Nielsen."""

import logging
from pathlib import Path
from typing import Any, Optional

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
        Optional[str], typer.Option(help="Show name to search for")
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
        response: Response = fetcher.episodebynumber(series_id, season, episode)
        data: Any = response.json()

        if raw:
            pprint(data)
        else:
            typer.echo(fetcher.pretty_episode(data))

    elif series_id and season:
        season_id: int = fetcher.get_season_id(series_id, season)
        response = fetcher.seasons_episodes(season_id)
        data = response.json()

        if raw:
            pprint(data)
        else:
            typer.echo(fetcher.pretty_season(data))

    elif series_id:
        response = fetcher.shows(series_id)
        data = response.json()

        if raw:
            pprint(data)
        else:
            typer.echo(fetcher.pretty_series(data))

    else:
        logger.critical("Could not fetch any information.")
        raise typer.Exit(4)

    if response.ok:
        nielsen.config.update_config(Path(config_files[-1]))


@app.command()
def apply(
    files: Annotated[list[str], typer.Argument(help="File(s) to process")],
    series: Annotated[Optional[str], typer.Option(help="Show name")],
    season: Annotated[
        int,
        typer.Option(help="Season number (to get additional details)"),
    ],
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
    simulate: Annotated[
        bool,
        typer.Option(help="Show file operations without performing them"),
    ] = config.getboolean("nielsen", "simulate"),
) -> None:
    """Apply episode information to the provided file(s)."""

    if not series:
        typer.echo("--series is required.")
        raise typer.Exit(1)

    if episode and not season:
        typer.echo("Cannot fetch episode information without a season.")
        raise typer.Exit(2)

    config.set("nielsen", "simulate", str(simulate))

    fetcher: nielsen.fetcher.TVMaze = nielsen.fetcher.TVMaze()

    series_id = fetcher.get_series_id(series, interactive)

    if series_id and season and episode:
        if len(files) != 1:
            typer.echo("Must specify exactly one file to apply this data to.")
            raise typer.Exit(3)

        # Create a TV instance and attach metadata to it for the Fetcher to work with
        media: nielsen.media.TV = nielsen.media.TV(
            Path(files.pop()), series=series, season=season, episode=episode
        )
        fetcher.fetch(media)
        media.rename()

        return

    season_id: int = fetcher.get_season_id(series_id, season)
    response: Response = fetcher.seasons_episodes(season_id)
    episodes: list[dict[str, Any]] = response.json()

    for e, f in zip(episodes, files):
        media = nielsen.media.TV(Path(f), series=series, season=season)
        typer.echo(
            f"Apply information from {series} Season {season} Episode {e['number']} to {media.path}"
        )
        media.episode = e.get("number", 0)
        media.title = e.get("name", "")
        media.rename()


if __name__ == "__main__":
    app()
