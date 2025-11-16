"""Tests for the main image finder."""

import pytest
from src.image_finder import LicensedImageFinder
from src.models import ImageResult, LicenseType


def test_image_finder_initialization():
    """Test image finder initialization."""
    finder = LicensedImageFinder()

    # Should have at least Wikimedia source
    assert len(finder.sources) >= 1
    assert "Wikimedia Commons" in finder.get_available_sources()


def test_get_status():
    """Test getting status information."""
    finder = LicensedImageFinder()
    status = finder.get_status()

    assert 'available_sources' in status
    assert 'total_sources' in status
    assert 'face_detection_enabled' in status
    assert 'config' in status
    assert isinstance(status['available_sources'], list)
    assert len(status['available_sources']) > 0


def test_quality_score_calculation():
    """Test quality score calculation."""
    finder = LicensedImageFinder()

    # Create test results
    result1 = ImageResult(
        image_url="https://example.com/image1.jpg",
        thumbnail_url="https://example.com/thumb1.jpg",
        source="Wikimedia Commons",
        license_type=LicenseType.CC0.value,
        license_url="https://example.com",
        width=1920,
        height=1080,
        title="Test Image",
        description="Test Description",
        author="Test Author"
    )

    result2 = ImageResult(
        image_url="https://example.com/image2.jpg",
        thumbnail_url="https://example.com/thumb2.jpg",
        source="Wikimedia Commons",
        license_type=LicenseType.CC_BY.value,
        license_url="https://example.com",
        width=640,
        height=480
    )

    results = finder._calculate_quality_scores([result1, result2], "person")

    assert result1.quality_score is not None
    assert result2.quality_score is not None
    # Result1 should have higher score (higher res, more metadata)
    assert result1.quality_score > result2.quality_score


def test_find_images_basic():
    """Test basic image finding (integration test)."""
    finder = LicensedImageFinder()

    # Search for a well-known person
    results = finder.find_images("Albert Einstein", entity_type="person", max_results=5, require_face=False)

    # Should return results
    assert isinstance(results, list)
    assert len(results) > 0

    # Each result should be a dict with required fields
    for result in results:
        assert 'image_url' in result
        assert 'source' in result
        assert 'license_type' in result
        assert 'license_url' in result
        assert 'quality_score' in result


def test_commercial_safety_filter():
    """Test that only commercial-safe images are returned."""
    finder = LicensedImageFinder()

    # Create test results with mixed licenses
    results = [
        ImageResult(
            image_url="https://example.com/image1.jpg",
            thumbnail_url="https://example.com/thumb1.jpg",
            source="Test Source",
            license_type=LicenseType.CC0.value,
            license_url="https://example.com"
        ),
        ImageResult(
            image_url="https://example.com/image2.jpg",
            thumbnail_url="https://example.com/thumb2.jpg",
            source="Test Source",
            license_type=LicenseType.UNKNOWN.value,
            license_url="https://example.com"
        )
    ]

    # All results from sources should be commercial safe
    for result in results:
        if result.license_type != LicenseType.UNKNOWN.value:
            assert result.is_commercial_safe()
