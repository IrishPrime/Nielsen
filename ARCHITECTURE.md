# Technical Overview

## `nielsen.media`
### `nielsen.media.Media`

`Media` objects represent a file to be managed and its metadata. While the base
`Media` class can be instantiated, it's not especially useful on its own,
serving primarily as a workable starting point from which subtypes should be
derived.

The base `Media` class defines the following attributes and methods:

1. `path`: A `pathlib.Path` which represents the actual location of the file on
   disk. Passing a `str` will attempt to coerce to a `pathlib.Path`. A pathlike
   value that points to a non-file will raise a `TypeError`.
1. `patterns`: A list of compiled regular expression `Pattern`s that are
   considered when attempting to infer metadata information about the object
   based on the filename (`path`). The values are processed in order, with more
   robust `Pattern`s being matched first and then falling through to less
   robust `Pattern`s in an attempt to get some useful information, even if not
   much is available.
1. `library`: A `pathlib.Path` representing the root of the library for the
   `Media` type from the configuration.
1. `orgdir`: A `pathlib.Path` representing the sub-directory of the `library`
   into which a `Media` object will be moved by the `organize` method. This is
   not implemented in the base class, so all subclasses must implement it in
   order to be able to organize files of that type.
1. `metadata`: A property which returns all metadata as a dictionary, intended
   for ease of inspection and discovery. This is not implemented in the base
   class, but should be implemented by subclasses.
1. `infer`: A method which attempts to infer metadata about the file (e.g. from
   its filename) and updates the appropriate metadata attributes with this
   information.
1. `organize`: A method which attempts to move the file to a new location (the
   `orgdir`), updates the `path` attribute on success and returns this new
   value.
1. `section`: A `str` which represents the section name of the `ConfigParser`
   from which settings for this `Media` object are retrieved.

The metadata keys are not defined as part of this base class because all types
of media have different relevant pieces of metadata. For example, TV shows
don't have an album name, movies don't have an episode number, music doesn't
have a season, etc. As such, each subtype is free to define its own metadata,
but that metadata should exposed as instance attributes.

## `nielsen.fetcher`

### `nielsen.fetcher.Fetcher`

The `Fetcher` Protocol is used to fetch metadata from sources which aren't
intrinsic to the `Media` object (e.g. making an external API request to TVMaze,
IMDB, etc.).

Other classes must implement their own `fetch` method to conform to this
protocol. The Protocol accepts the generic `MT` class, which is bound to
`nielsen.media.Media`.

```python
MT = TypeVar("MT", bound=nielsen.media.Media)

class Fetcher(Protocol):
    def fetch(self, media: MT) -> None:
        ...
```

See [`nielsen.fetcher.TVMaze`](./nielsen/fetcher.py) for a sample class that
implements the protocol.

## `nielsen.processor`

### `nielsen.processor.Processor`

`Processor` objects are inteded to provide a convenient way to exercise all
functionality provided by the rest of the application without all front-ends
being forced to provide their own implementations.

Instances of the class are created with a type reference to a `Media` subclass
and a `Fetcher` instance. Instances are callable with a `pathlib.Path` object
as an argument.

The `Processor` instance uses the `Media` type reference to determine which
type of `Media` subclass to create from the given `Path`, calls `Media.infer()`
to infer whatever information it can from the filename, and uses the `Fetcher`
instance to fetch additional metadata. Finally, the `Processor` will call the
`Media.rename()` and `Media.organize()` methods to make use of this metadata
and place the files where they belong.

### `nielsen.processor.MediaType`

An `Enum` for all supported `Media` types. This is used to provide choices when
implementing front-ends.

### `nielsen.processor.ProcessorFactory`

The `ProcessorFactory` accepts a type reference to a `Media` subclass and a
`Fetcher` and returns a `Processor` instance.

The `nielsen.processor` module also provides a `PROCESSOR_FACTORIES` dictionary
containing instances of useful `ProcessorFactory` presets.

This factory pattern allows for any combination of a `Media` subclass and
`Fetcher` instance to be combined into a `Processor`.

### `nielsen.processor.PROCESSOR_FACTORIES`

A dictionary with `MediaType` keys and `ProcessorFactory` values. Use one of
the `MediaType`s to get the appropriate `ProcessorFactory`. This serves as a
collection of standard combinations of `Media` subclasses and `Fetcher`s (e.g.
`nielsen.media.TV` and `nielsen.fetcher.TVMaze`).
