# Technical Overview

## Abstractions

### Media

`Media` objects represent a file to be managed and its metadata. While the base
`Media` class can be instantiated, it's not especially useful on its own,
serving primarily as a workable starting point from which subtypes should be
derived.

The base `Media` class defines the following attributes and methods:

1. `path`: A `pathlib.Path` which represents the actual location of the file on
   disk. This value is optional, and falsey values should set it to `None`.
1. `patterns`: A list of compiled regular expression `Pattern`s that are
   considered when attempting to infer metadata information about the object
   based on the filename (`path`).
1. `infer`: A method which attempts to infer metadata about the file (e.g. from
   its filename) and updates the appropriate metadata attributes with this
   information.
1. `organize`: A method which attempts to move the file to a new location,
   updates the `path` attribute on success, and returning this new value.
1. `metadata`: A property which returns all metadata as a dictionary, intended
   for ease of inspection and discovery.

The metadata keys are not defined as part of this base class because all types
of media have different relevant pieces of metadata. For example, TV shows
don't have an album name, movies don't have an episode number, music doesn't
have a season, etc. As such, each subtype is free to define its own metadata,
but that metadata should exposed as instance attributes.

### MetadataFetcher

`MetadataFetcher` objects are used to fetch metadata from sources which aren't
intrinsic to the `Media` object (e.g. making an external API request to TVMaze,
IMDB, etc.).
