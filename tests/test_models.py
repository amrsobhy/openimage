"""Tests for data models."""

import pytest
from src.models import ImageResult, LicenseType


def test_image_result_creation():
    """Test creating an ImageResult."""
    result = ImageResult(
        image_url="https://example.com/image.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
        source="Test Source",
        license_type=LicenseType.CC0.value,
        license_url="https://creativecommons.org/publicdomain/zero/1.0/",
        title="Test Image"
    )

    assert result.image_url == "https://example.com/image.jpg"
    assert result.source == "Test Source"
    assert result.license_type == LicenseType.CC0.value


def test_image_result_to_dict():
    """Test converting ImageResult to dictionary."""
    result = ImageResult(
        image_url="https://example.com/image.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
        source="Test Source",
        license_type=LicenseType.CC_BY.value,
        license_url="https://creativecommons.org/licenses/by/4.0/",
        title="Test Image",
        author="Test Author"
    )

    result_dict = result.to_dict()

    assert isinstance(result_dict, dict)
    assert result_dict['image_url'] == "https://example.com/image.jpg"
    assert result_dict['title'] == "Test Image"
    assert result_dict['author'] == "Test Author"
    assert 'description' not in result_dict  # None values should be excluded


def test_is_commercial_safe():
    """Test commercial safety check."""
    # Safe licenses
    safe_result = ImageResult(
        image_url="https://example.com/image.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
        source="Test Source",
        license_type=LicenseType.CC0.value,
        license_url="https://creativecommons.org/publicdomain/zero/1.0/"
    )
    assert safe_result.is_commercial_safe() is True

    # Unsafe license
    unsafe_result = ImageResult(
        image_url="https://example.com/image.jpg",
        thumbnail_url="https://example.com/thumb.jpg",
        source="Test Source",
        license_type=LicenseType.UNKNOWN.value,
        license_url="https://example.com"
    )
    assert unsafe_result.is_commercial_safe() is False


def test_all_major_licenses_are_commercial_safe():
    """Test that all major free licenses are considered commercial safe."""
    commercial_licenses = [
        LicenseType.PUBLIC_DOMAIN,
        LicenseType.CC0,
        LicenseType.CC_BY,
        LicenseType.CC_BY_SA,
        LicenseType.UNSPLASH,
        LicenseType.PEXELS,
        LicenseType.PIXABAY,
    ]

    for license_type in commercial_licenses:
        result = ImageResult(
            image_url="https://example.com/image.jpg",
            thumbnail_url="https://example.com/thumb.jpg",
            source="Test Source",
            license_type=license_type.value,
            license_url="https://example.com"
        )
        assert result.is_commercial_safe() is True, f"{license_type.value} should be commercial safe"
