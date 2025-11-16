"""Tests for image sources."""

import pytest
from src.sources.wikimedia import WikimediaSource
from src.sources.unsplash import UnsplashSource
from src.sources.pexels import PexelsSource
from src.sources.pixabay import PixabaySource


def test_wikimedia_source_initialization():
    """Test Wikimedia source initialization."""
    source = WikimediaSource()
    assert source.get_source_name() == "Wikimedia Commons"
    assert source.is_available() is True  # Wikimedia doesn't need API key


def test_wikimedia_source_search():
    """Test Wikimedia source search (integration test)."""
    source = WikimediaSource()
    results = source.search("Albert Einstein", max_results=5)

    # Should return some results
    assert isinstance(results, list)
    # Results should have required fields
    for result in results:
        assert result.image_url
        assert result.source == "Wikimedia Commons"
        assert result.license_type
        assert result.license_url
        assert result.is_commercial_safe()


def test_unsplash_source_initialization():
    """Test Unsplash source initialization."""
    source = UnsplashSource(api_key="test_key")
    assert source.get_source_name() == "Unsplash"
    assert source.is_available() is True

    source_no_key = UnsplashSource()
    assert source_no_key.is_available() is False


def test_pexels_source_initialization():
    """Test Pexels source initialization."""
    source = PexelsSource(api_key="test_key")
    assert source.get_source_name() == "Pexels"
    assert source.is_available() is True

    source_no_key = PexelsSource()
    assert source_no_key.is_available() is False


def test_pixabay_source_initialization():
    """Test Pixabay source initialization."""
    source = PixabaySource(api_key="test_key")
    assert source.get_source_name() == "Pixabay"
    assert source.is_available() is True

    source_no_key = PixabaySource()
    assert source_no_key.is_available() is False


def test_wikimedia_license_parsing():
    """Test Wikimedia license parsing."""
    source = WikimediaSource()

    assert "CC0" in source._parse_license("CC0")
    assert "CC BY" in source._parse_license("CC-BY-4.0")
    assert "CC BY-SA" in source._parse_license("CC-BY-SA-3.0")
    assert "Public Domain" in source._parse_license("Public Domain")
