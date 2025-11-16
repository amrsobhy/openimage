"""Configuration management for the Licensed Image Finder."""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file if it exists
load_dotenv()


class Config:
    """Configuration class for API keys and settings."""

    # API Keys (optional - sources will work without keys but may have limitations)
    UNSPLASH_ACCESS_KEY: Optional[str] = os.getenv('UNSPLASH_ACCESS_KEY')
    PEXELS_API_KEY: Optional[str] = os.getenv('PEXELS_API_KEY')
    PIXABAY_API_KEY: Optional[str] = os.getenv('PIXABAY_API_KEY')

    # Request settings
    REQUEST_TIMEOUT: int = 10  # seconds
    MAX_RESULTS_PER_SOURCE: int = 10
    USER_AGENT: str = "LicensedImageFinder/1.0 (https://github.com/openimage; educational/research)"

    # Face detection settings for person entities
    ENABLE_FACE_DETECTION: bool = True
    MIN_FACE_CONFIDENCE: float = 0.5

    # Image quality settings
    MIN_IMAGE_WIDTH: int = 800
    MIN_IMAGE_HEIGHT: int = 600

    @classmethod
    def validate(cls) -> dict:
        """Validate configuration and return status of API keys."""
        return {
            'unsplash': cls.UNSPLASH_ACCESS_KEY is not None,
            'pexels': cls.PEXELS_API_KEY is not None,
            'pixabay': cls.PIXABAY_API_KEY is not None,
            'wikimedia': True  # No API key needed
        }
