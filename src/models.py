"""Data models for licensed images."""

from dataclasses import dataclass, asdict
from typing import Optional, Dict, Any
from enum import Enum


class LicenseType(Enum):
    """Common license types for images."""
    PUBLIC_DOMAIN = "Public Domain"
    CC0 = "CC0 (Creative Commons Zero)"
    CC_BY = "CC BY (Attribution)"
    CC_BY_SA = "CC BY-SA (Attribution-ShareAlike)"
    CC_BY_ND = "CC BY-ND (Attribution-NoDerivs)"
    UNSPLASH = "Unsplash License"
    PEXELS = "Pexels License"
    PIXABAY = "Pixabay License"
    UNKNOWN = "Unknown"


@dataclass
class ImageResult:
    """Represents a single image result with license information."""

    # Required fields
    image_url: str
    thumbnail_url: str
    source: str
    license_type: str
    license_url: str

    # Optional metadata
    title: Optional[str] = None
    description: Optional[str] = None
    author: Optional[str] = None
    author_url: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None

    # Quality indicators
    has_face: Optional[bool] = None
    quality_score: Optional[float] = None

    # Additional metadata
    page_url: Optional[str] = None
    download_url: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {k: v for k, v in asdict(self).items() if v is not None}

    def is_commercial_safe(self) -> bool:
        """Check if image is safe for commercial use."""
        commercial_licenses = [
            LicenseType.PUBLIC_DOMAIN.value,
            LicenseType.CC0.value,
            LicenseType.CC_BY.value,
            LicenseType.CC_BY_SA.value,
            LicenseType.UNSPLASH.value,
            LicenseType.PEXELS.value,
            LicenseType.PIXABAY.value,
        ]
        return self.license_type in commercial_licenses
