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

    # Ignira Search API for info.gouv.fr
    IGNIRA_API_KEY: Optional[str] = os.getenv('IGNIRA_API_KEY')

    # Crawl.ninja Scraping API
    CRAWL_NINJA_API_KEY: Optional[str] = os.getenv('CRAWL_NINJA_API_KEY')

    # Zeus LLM API for gender detection
    ZEUS_LLM_API_KEY: Optional[str] = os.getenv('ZEUS_LLM_API_KEY')
    ZEUS_LLM_ENDPOINT: str = "https://api.zeusllm.com/v1/ai"
    ZEUS_LLM_PIPELINE_ID: str = "pipe_1752648182552_ac1qsbb18"
    ZEUS_LLM_TEMPERATURE: float = 0.7

    # Request settings
    REQUEST_TIMEOUT: int = 30  # seconds - for standard API calls
    SCRAPING_TIMEOUT: int = 60  # seconds - for web scraping operations
    MAX_RESULTS_PER_SOURCE: int = 10
    USER_AGENT: str = "LicensedImageFinder/1.0 (https://github.com/openimage; educational/research)"

    # Face detection settings for person entities
    ENABLE_FACE_DETECTION: bool = True
    MIN_FACE_CONFIDENCE: float = 0.5

    # Gender filtering settings for person entities
    ENABLE_GENDER_FILTERING: bool = True

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
            'wikimedia': True,  # No API key needed
            'infogouv': cls.IGNIRA_API_KEY is not None and cls.CRAWL_NINJA_API_KEY is not None
        }
