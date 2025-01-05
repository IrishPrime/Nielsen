#!/usr/bin/env python3
"""Command-line frontend for Nielsen."""

import logging
from pathlib import Path
from typing_extensions import Annotated

from nielsen.config import config
import nielsen.config
import nielsen.fetcher
import nielsen.media
import nielsen.processor

import nielsen.bin.cli.config
import nielsen.bin.cli.tv

import typer

config_files: list[str] = nielsen.config.load_config()
logger: logging.Logger = logging.getLogger("nielsen")

logging.basicConfig(
    format="[%(asctime)s][%(levelname)s][%(module)s][%(funcName)s:%(lineno)d]: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
    level=config.get("nielsen", "loglevel", fallback=logging.INFO),
)


app: typer.Typer = typer.Typer(no_args_is_help=True)

app.add_typer(
    nielsen.bin.cli.config.app,
    name="config",
    help="Subcommands for the Nielsen configuration",
    no_args_is_help=True,
)
app.add_typer(
    nielsen.bin.cli.tv.app,
    name="tv",
    help="Subcommands for interacting with TV shows",
    no_args_is_help=True,
)


@app.command()
def infer(
    files: Annotated[list[str], typer.Argument(help="File(s) to process")],
    fetch: Annotated[
        bool,
        typer.Option(help="Fetch metadata from remote sources for file(s)"),
    ] = config.getboolean("nielsen", "fetch"),
    media_type: Annotated[
        nielsen.processor.MediaType,
        typer.Option(help="Media Type used to process files"),
    ] = nielsen.processor.MediaType.TV,
) -> None:
    """Infer metadata about the given file and print it. Does not modify the file."""

    config.set("nielsen", "fetch", str(fetch))

    processor_factory: nielsen.processor.ProcessorFactory | None = (
        nielsen.processor.PROCESSOR_FACTORIES.get(media_type)
    )

    if processor_factory is None:
        logger.critical(
            "Media Processor could not be created for type: %s.", media_type
        )
        raise typer.Exit(code=1)

    processor: nielsen.processor.Processor = processor_factory()

    for file in files:
        media: nielsen.media.Media = processor.media_type(Path(file))
        media.infer()
        processor.fetcher.fetch(media)
        print(media)


@app.command()
def process(
    files: Annotated[list[str], typer.Argument(help="File(s) to process")],
    fetch: Annotated[
        bool,
        typer.Option(help="Fetch metadata from remote sources for file(s)"),
    ] = config.getboolean("nielsen", "fetch"),
    organize: Annotated[
        bool,
        typer.Option(help="Move file(s) to library, but do not otherwise rename them"),
    ] = config.getboolean("nielsen", "organize"),
    rename: Annotated[
        bool, typer.Option(help="Rename file(s), but do not otherwise move them")
    ] = config.getboolean("nielsen", "rename"),
    simulate: Annotated[
        bool,
        typer.Option(help="Show file operations without performing them"),
    ] = config.getboolean("nielsen", "simulate"),
    media_type: Annotated[
        nielsen.processor.MediaType,
        typer.Option(help="Media Type used to process files"),
    ] = nielsen.processor.MediaType.TV,
) -> None:
    """Process the given files. Use the Media Type to determine how files should be
    processed (i.e. which Media subclass and Fetcher to use)."""

    processor_factory: nielsen.processor.ProcessorFactory | None = (
        nielsen.processor.PROCESSOR_FACTORIES.get(media_type)
    )

    if processor_factory is None:
        logger.critical(
            "Media Processor could not be created for type: %s.", media_type
        )
        raise typer.Exit(code=1)

    processor: nielsen.processor.Processor = processor_factory()

    if not config.has_section(media_type.value):
        config.add_section(media_type.value)

    config.set(media_type.value, "fetch", str(fetch))
    config.set(media_type.value, "organize", str(organize))
    config.set(media_type.value, "rename", str(rename))
    config.set("nielsen", "simulate", str(simulate))

    for file in files:
        processor.process(Path(file))

    # Due to the order in which configuration files are loaded, the most "personal"
    # version will be at the end of the list.
    if config_files:
        nielsen.config.update_config(Path(config_files[-1]))


def main() -> None:
    """Rename and organize media files."""

    app()


if __name__ == "__main__":
    typer.run(main)
