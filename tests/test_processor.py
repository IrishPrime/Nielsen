"""Tests for the nielsen.processor module."""

import pathlib

from pytest_mock import MockType

import nielsen.config
import nielsen.media
import nielsen.fetcher
import nielsen.processor


def test_processor_init() -> None:
    """Test construction of new Processor objects."""

    processor: nielsen.processor.Processor = nielsen.processor.Processor(
        nielsen.media.Media, nielsen.fetcher.TVMaze()
    )

    assert hasattr(processor, "media_type")
    assert hasattr(processor, "fetcher")
    assert issubclass(processor.media_type, nielsen.media.Media)
    assert isinstance(processor.fetcher, nielsen.fetcher.TVMaze)


def test_processor_factory_init() -> None:
    """Test construction of new ProcessorFactory objects."""

    factory: nielsen.processor.ProcessorFactory = nielsen.processor.ProcessorFactory(
        nielsen.media.Media, nielsen.fetcher.TVMaze
    )

    assert hasattr(factory, "media_type")
    assert hasattr(factory, "fetcher")
    assert issubclass(factory.media_type, nielsen.media.Media)
    # factory.fetcher must be a subclass of Fetcher, but not an instance of it
    assert issubclass(factory.fetcher, nielsen.fetcher.TVMaze)
    assert not isinstance(factory.fetcher, nielsen.fetcher.TVMaze)


def test_processor_factory_call() -> None:
    """Calling the Factory should return a Processor."""

    factory: nielsen.processor.ProcessorFactory = nielsen.processor.ProcessorFactory(
        nielsen.media.TV, nielsen.fetcher.TVMaze
    )

    processor: nielsen.processor.Processor = factory()
    assert isinstance(processor, nielsen.processor.Processor)


def test_processor_process(mocker) -> None:
    """The process method should call all other high-level Media/Fetcher functions."""

    # This test should be expanded as more Media and Fetcher types are added
    mock_fetcher: MockType = mocker.Mock(spec_set=nielsen.fetcher.TVMaze)
    mock_rename: MockType = mocker.patch("nielsen.media.Media.rename")
    mock_organize: MockType = mocker.patch("nielsen.media.Media.organize")

    media_path: pathlib.Path = pathlib.Path("ted.lasso.s01e01.1080p.web.h264-ggwp")

    processor: nielsen.processor.Processor = nielsen.processor.Processor(
        nielsen.media.TV, mock_fetcher
    )

    # Assert all options are enabled
    assert nielsen.config.config.getboolean("tv", "fetch")
    assert nielsen.config.config.getboolean("tv", "rename")
    assert nielsen.config.config.getboolean("tv", "organize")

    # Process media
    processed: nielsen.media.Media = processor.process(media_path)

    # Assert functions are called
    mock_fetcher.fetch.assert_called_with(processed)
    mock_rename.assert_called_once()
    mock_organize.assert_called_once()

    # Assert returned type of processed Media matches
    assert isinstance(processed, nielsen.media.TV)
