#!/usr/bin/env python3

"""Generate pickled objects for Mocks to return in unit tests."""

import logging
import pathlib
import pickle
from typing import Any

import requests

logger: logging.Logger = logging.getLogger(__name__)
logger.addHandler(logging.NullHandler())


def main():
    """Pickle responses from external API calls for each fetcher."""

    tvmaze()


def pickle_data(data: Any, path: str) -> None:
    """Pickle some arbitrary data and store it in the fixtures directory under the path
    described by the given string."""

    # Ensure all parent directories are created for the file. The fixtures directory
    # should be a sibling of the `bin` directory which contains this script.
    file: pathlib.Path = (
        pathlib.Path(__file__).parent.parent / "fixtures/" / pathlib.Path(path)
    )
    file.parent.mkdir(parents=True, exist_ok=True)
    file.write_bytes(pickle.dumps(data))


def tvmaze() -> None:
    """Make calls to the TVMaze API using the `requests` module, then pickle the
    responses for later loading and use by the unit tests for the TVMaze fetcher."""

    TVMAZE: str = "https://api.tvmaze.com/"
    queries: list[dict[str, str]] = [
        {"api": "singlesearch", "params": "Ted Lasso"},
        {
            "api": "search",
            "params": "Agents of SHIELD",
        },
    ]

    for query in queries:
        stem: str = f"{query['api']}-{query['params'].lower()}".replace(" ", "-")
        path: str = f"tv/{stem}.pickle"
        response: requests.models.Response = requests.get(
            f"{TVMAZE}/{query['api']}/shows?q={query['params']}"
        )

        logger.info(response)

        if response.ok:
            pickle_data(response, path)


if __name__ == "__main__":
    main()


# vim: tabstop=4 softtabstop=4 shiftwidth=4 expandtab
