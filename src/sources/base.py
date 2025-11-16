"""Base class for image source providers."""

from abc import ABC, abstractmethod
from typing import List
from src.models import ImageResult


class ImageSource(ABC):
    """Abstract base class for image source providers."""

    def __init__(self, api_key: str = None):
        """Initialize the image source.

        Args:
            api_key: Optional API key for the source
        """
        self.api_key = api_key

    @abstractmethod
    def search(self, query: str, max_results: int = 10) -> List[ImageResult]:
        """Search for images matching the query.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of ImageResult objects
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """Get the name of this image source."""
        pass

    def is_available(self) -> bool:
        """Check if this source is available (has API key if required)."""
        return True
