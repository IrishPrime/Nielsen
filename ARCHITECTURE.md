# Technical Overview

## Abstractions

### Media

`Media` objects represent a file to be managed and its metadata. The `Media`
class itself is an abstract base class from which subtypes should be derived.

1. `path`: A `pathlib.Path` which represents the actual location of the file on
   disk. This value is optional, and falsey values should set it to `None`.
2. `infer`: A method which attempts to infer metadata about the file (e.g. from
   its filename) and updates the appropriate metadata attributes with this
   information.
3. `organize`: A method which attempts to move the file to a new location,
   updates the `path` attribute on success, and returning this new value.
4. `metadata`: A property which returns all metadata as a dictionary, intended
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
