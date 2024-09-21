#!/usr/bin/env python3

"""Generate pickled objects for Mocks to return in unit tests. This allows us to work
with real data, but prevents us from having to make additional calls to an external API
every time the tests are run."""

import logging
import pathlib
import pickle
from typing import Any

import requests

logger: logging.Logger = logging.getLogger()
logger.setLevel(logging.DEBUG)
logger.addHandler(logging.StreamHandler())


def main():
    """Pickle responses from external API calls for each fetcher."""

    tvmaze()


def pickle_data(data: Any, path: str) -> None:
    """Pickle some arbitrary data and store it in the fixtures directory under the path
    described by the given string."""

    # Ensure all parent directories are created for the file. The fixtures directory
    # should be a sibling of the `bin` directory which contains this script.
    file: pathlib.Path = (
        pathlib.Path(__file__).parent.parent.parent / "fixtures/" / pathlib.Path(path)
    )
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(pickle.dumps(data))


def tvmaze() -> None:
    """Make calls to the TVMaze API using the `requests` module, then pickle the
    responses for later loading and use by the unit tests for the TVMaze fetcher."""

    TVMAZE: str = "https://api.tvmaze.com"
    TRANSLATION = str.maketrans({" ": "-", "=": "-", "&": "-"})
    queries: list[dict[str, str]] = [
        {"api": "search/shows", "params": "q=Agents+of+SHIELD"},
        {"api": "search/shows", "params": "q=Ted+Lasso"},
        {"api": "search/shows", "params": "q=useless+search+string"},
        {"api": "seasons/112939/episodes", "params": ""},
        {"api": "shows/44458/episodebynumber", "params": "season=1&number=3"},
        {"api": "shows/44458/seasons", "params": ""},
        {"api": "singlesearch/shows", "params": "q=Ted+Lasso"},
        {"api": "singlesearch/shows", "params": "q=useless+search+string"},
    ]

    for query in queries:
        stem: str = f"{query['api']}-{query['params'].lower()}".translate(TRANSLATION)
        path: str = f"tv/{stem}.pickle".translate(TRANSLATION)
        uri: str = f"{TVMAZE}/{query['api']}?{query['params']}"
        response: requests.models.Response = requests.get(uri)

        logger.debug(response.json())

        pickle_data(response, path)


if __name__ == "__main__":
    main()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab textwidth=88
