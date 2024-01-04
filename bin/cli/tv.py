#!/usr/bin/env python3
"""Subcommands for managing TV shows with Nielsen."""

import logging
from pathlib import Path

import nielsen.config
import nielsen.media
from nielsen.config import config as cfg

import typer
from rich.pretty import pprint


logger: logging.Logger = logging.getLogger(__name__)
nielsen.config.load_config()

app: typer.Typer = typer.Typer(name="TV")


@app.command()
def rename(
    files: list[Path] = typer.Argument(
        ...,
        exists=True,
        file_okay=True,
        dir_okay=False,
        writable=True,
        readable=True,
        resolve_path=True,
        help="File(s) to rename",
    ),
    simulate: bool = typer.Option(
        False, help="Show file renames without performing them"
    ),
) -> None:
    """Rename the given files."""

    for file in files:
        media: nielsen.media.TV = nielsen.media.TV(file)
        if simulate:
            media.infer()
            pprint(f"{media.path} → {media!r}")


if __name__ == "__main__":
    app()
