"""Unsplash image source."""

import requests
from typing import List
from src.sources.base import ImageSource
from src.models import ImageResult, LicenseType
from src.config import Config


class UnsplashSource(ImageSource):
    """Search Unsplash for freely licensed images."""

    BASE_URL = "https://api.unsplash.com"

    def get_source_name(self) -> str:
        return "Unsplash"

    def is_available(self) -> bool:
        """Check if Unsplash API key is configured."""
        return self.api_key is not None

    def search(self, query: str, max_results: int = 10) -> List[ImageResult]:
        """Search Unsplash for images.

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
                'Authorization': f'Client-ID {self.api_key}'
            }

            params = {
                'query': query,
                'per_page': min(max_results, 30),  # API limit
                'orientation': 'landscape'
            }

            response = requests.get(
                f"{self.BASE_URL}/search/photos",
                headers=headers,
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            for photo in data.get('results', []):
                result = ImageResult(
                    image_url=photo['urls']['regular'],
                    thumbnail_url=photo['urls']['small'],
                    source=self.get_source_name(),
                    license_type=LicenseType.UNSPLASH.value,
                    license_url='https://unsplash.com/license',
                    title=photo.get('description') or photo.get('alt_description'),
                    description=photo.get('description'),
                    author=photo['user'].get('name'),
                    author_url=photo['user'].get('links', {}).get('html'),
                    width=photo.get('width'),
                    height=photo.get('height'),
                    page_url=photo['links'].get('html'),
                    download_url=photo['urls']['full']
                )
                results.append(result)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Unsplash: {e}")
        except Exception as e:
            print(f"Unexpected error in Unsplash source: {e}")

        return results[:max_results]
