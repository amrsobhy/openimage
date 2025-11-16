"""Pexels image source."""

import requests
from typing import List
from src.sources.base import ImageSource
from src.models import ImageResult, LicenseType
from src.config import Config


class PexelsSource(ImageSource):
    """Search Pexels for freely licensed images."""

    BASE_URL = "https://api.pexels.com/v1"

    def get_source_name(self) -> str:
        return "Pexels"

    def is_available(self) -> bool:
        """Check if Pexels API key is configured."""
        return self.api_key is not None

    def search(self, query: str, max_results: int = 10) -> List[ImageResult]:
        """Search Pexels for images.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of ImageResult objects
        """
        if not self.is_available():
            return []

        results = []

        try:
            headers = {
                'Authorization': self.api_key
            }

            params = {
                'query': query,
                'per_page': min(max_results, 80),  # API limit
                'orientation': 'landscape'
            }

            response = requests.get(
                f"{self.BASE_URL}/search",
                headers=headers,
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            for photo in data.get('photos', []):
                result = ImageResult(
                    image_url=photo['src']['large'],
                    thumbnail_url=photo['src']['small'],
                    source=self.get_source_name(),
                    license_type=LicenseType.PEXELS.value,
                    license_url='https://www.pexels.com/license/',
                    title=photo.get('alt'),
                    description=photo.get('alt'),
                    author=photo.get('photographer'),
                    author_url=photo.get('photographer_url'),
                    width=photo.get('width'),
                    height=photo.get('height'),
                    page_url=photo.get('url'),
                    download_url=photo['src']['original']
                )
                results.append(result)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Pexels: {e}")
        except Exception as e:
            print(f"Unexpected error in Pexels source: {e}")

        return results[:max_results]
