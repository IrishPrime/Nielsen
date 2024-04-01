# Nielsen

Nielsen helps rename and organize digital media collections.

Consider a filename such as `The.Wheel.of.Time.S01E06.720p.WEB.x265-MiNX.mkv`.
If you'd prefer something more along the lines of `The Wheel of Time -01.06-
The Flame of Tar Valon.mkv`, Nielsen can help.

Nielsen endeavors to automatically handle these types of renaming operations,
as well as move the files into a more hierarchical folder structure that keeps
your media directories tidy.

## Requirements

- Python 3.11 (or newer)
- [Poetry][poetry] (for source installations)

## Install

### PyPI

This package is published on [PyPI][pypi-nielsen] and can be installed from
there with the following command.

```bash
pip install nielsen
```

### Source

This package can also be installed from source by cloning this repository and
using [Poetry][poetry].

```bash
poetry install
```

## Concepts

- [`Media`](./ARCHITECTURE.md#nielsen.media.Media) - Represents a file on disk
  and its metadata. The specific subclass determines how metadata is inferred
  and which `Fetcher` should be used.
- [`Fetcher`](./ARCHITECTURE.md#nielsen.fetcher.Fetcher) - Queries external
  systems/services for metadata about a given `Media` instance.
- [`Processor`](./ARCHITECTURE.md#nielsen.processor.Processor) - A grouping of
  a `MediaType` and `Fetcher`. Given a file, the `Processor` creates the
  appropriate `Media` (based on the `MediaType`) and `Fetcher` to query for
  metadata.

Under the hood, "processing" a file will create a `Media` object from the given
path and `MediaType`, infer metadata based on the filename (e.g. TV series
name, season number, episode number, and episode title).

If the `fetch` option is enabled, then a `Fetcher` will also be created to
query more information (e.g. `Ted.Lasso.S01.E01.mp4` doesn't give us an episode
title, but the `Fetcher` can ask [TVMaze][tvmaze] for it).

`nielsen` can then rename the file (e.g. `Ted Lasso -01.04- For the
Children.mp4`) and move it to your media library (e.g. `~/Videos/TV/Ted
Lasso/Season 01/`).

See the [ARCHITECTURE][architecture] file for more detailed information.

## Usage

The primary use case `nielsen` is intended to handle is that of renaming a file
and moving it into the correct location on disk. This is done with the
`process` subcommand.

All commands (and subcommands) will accept a `--help` flag to provide more
information about usage.

```bash
# Process a given file
nielsen process PATH_TO_FILE

# See a list of all subcommands
nielsen --help
```

## Configuration

`nielsen` uses an [INI file][wikipedia-ini] for configuration. The module will
look for files in the following locations, and load them in order (overwriting
old values with newer values as they're loaded):

- `/etc/nielsen/config.ini`
- `~/.config/nielsen/config.ini`

The CLI uses these configuration files to determine its default behavior, but
also accepts a few command line flags (e.g. `--[no-]organize`) to modify its
behavior at runtime. Command line arguments will take precedence over the
configuration files.

### Sections and Options

Each section (denoted with square-brackets around the name) may contain
multiple options.

#### `[nielsen]`

Contains options about the behavior of the application itself.

##### `fetch`

Whether or not to create and use a `Fetcher` to obtain additional metadata
about a file. If there is sufficient information in the filename or there is no
network connection, the data fetching process can be skipped altogether.

*Values*: `True` or `False`

*Default*: `True`

##### `interactive`

Whether or not to prompt the user to select their desired result when a
`Fetcher` yields multiple results (e.g. "The Office"). In non-interactive mode,
the first result is used.

*Values*: `True` or `False`

*Default*: `True`

##### `library`

The root directory into which a file should be moved as part of its processing.
Each `Media` type may define its own `library` path.

*Value*: *A directory the user can write to*

*Default*: `$HOME`

##### `logfile`

The location on disk to which `nielsen` log output should be written.

*Value*: *A file the user can write to*

*Default*: `~/.local/log/nielsen/nielsen.log`

##### `loglevel`

The [Python logging level][python-logging] at which to filter log messages.

*Values*: `NOTSET`, `DEBUG`, `INFO`, `WARNING`, `ERROR`, `CRITICAL`

*Default*: `WARNING`

##### `mode`

The [numeric notation][wikipedia-fs-mode] for the file mode (or permissions) a
file should be given during processing.

*Default*: 644

##### `organize`

Whether or not to move files to the media library during processing.

*Values*: `True` or `False`

*Default*: `True`

##### `rename`

Whether or not to rename a file with its new metadata during processing.

*Values*: `True` or `False`

*Default*: `True`

##### `simulate`

Whether or not to actually modify files (e.g. rename and move them), or just
print/log the actions which would otherwise be taken during processing.

*Values*: `True` or `False`

*Default*: `False`

##### `transform`

Whether or not to transform (or modify) the inferred or fetched data during
processing. The exact nature of these transformations are defined by the
`MediaType`.

*Values*: `True` or `False`

*Default*: `True`

#### `[media]`

Contains options to apply to generic `Media` objects. Currently, there's no
real use for this.

#### `[tv]`

Contains options to apply to `TV` objects. It is recommended that you set a
`library` option to keep each media type separated. This value will overwrite
the default `[nielsen]` or `[media]` section options for files processed as
`TV`.

#### `[tv/transform/series]`

This section defines transformations for `TV.series` values. This can be used
to normalize series names so that all files get organized into the same
directory and are named consistently. Consider the series [Marvel's Agents of
S.H.I.E.L.D.][tvmaze-agents-of-shield]. You may have files with various naming
conventions:

1. Agents Of S.H.I.E.L.D.
1. Agents Of SHIELD
1. Agents Of Shield
1. Agents of S.H.I.E.L.D.
1. Agents of SHIELD
1. Agents of Shield
1. Marvel's Agents Of S.H.I.E.L.D.
1. Marvel's Agents Of SHIELD
1. Marvel's Agents Of Shield
1. Marvel's Agents of S.H.I.E.L.D.
1. Marvel's Agents of SHIELD
1. Marvel's Agents of Shield

By default, `nielsen` will see each of these as a different series. Defining a
variant and a preferred name allows `nielsen` to treat them all as a single
series. The variants used to choose a transformation are case insensitive, so
you can fix capital letters/title casing with minimal repetition.

*Values*: `Variant Series Name = Preferred Series Name`

```ini
[tv/transform/series]
Agents of S.H.I.E.L.D. = Marvel's Agents of S.H.I.E.L.D.
Agents of SHIELD = Marvel's Agents of S.H.I.E.L.D.
Marvel's Agents of S.H.I.E.L.D. = Marvel's Agents of S.H.I.E.L.D.
Marvel's Agents of SHIELD = Marvel's Agents of S.H.I.E.L.D.

Its Always Sunny In Philadelphia = It's Always Sunny in Philadelphia
It's Always Sunny In Philadelphia = It's Always Sunny in Philadelphia
```

#### `[tvmaze/ids]`

Fetching an episode title from [TVMaze][tvmaze] requires a series ID, season
number, and episode number. Once a series name to series ID mapping has been
determined, `nielsen` will attempt to save it in this section to avoid having
to do the same lookup again in the future.

*Values*: `Series Name = Series ID`

[architecture]: ARCHITECTURE.md
[poetry]: https://python-poetry.org/
[pypi-nielsen]: https://pypi.org/project/Nielsen/
[python-logging]: https://docs.python.org/3/library/logging.html#logging-levels
[tvmaze-agents-of-shield]: https://www.tvmaze.com/shows/31/marvels-agents-of-shield
[tvmaze]: https://tvmaze.com/
[wikipedia-fs-mode]: https://en.wikipedia.org/wiki/File-system_permissions#Numeric_notation
[wikipedia-ini]: https://en.wikipedia.org/wiki/INI_file
