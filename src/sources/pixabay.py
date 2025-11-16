"""Pixabay image source."""

import requests
from typing import List
from src.sources.base import ImageSource
from src.models import ImageResult, LicenseType
from src.config import Config


class PixabaySource(ImageSource):
    """Search Pixabay for freely licensed images."""

    BASE_URL = "https://pixabay.com/api/"

    def get_source_name(self) -> str:
        return "Pixabay"

    def is_available(self) -> bool:
        """Check if Pixabay API key is configured."""
        return self.api_key is not None

    def search(self, query: str, max_results: int = 10) -> List[ImageResult]:
        """Search Pixabay for images.

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
            params = {
                'key': self.api_key,
                'q': query,
                'image_type': 'photo',
                'per_page': min(max_results, 200),  # API limit
                'safesearch': 'true'
            }

            response = requests.get(
                self.BASE_URL,
                params=params,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            for photo in data.get('hits', []):
                result = ImageResult(
                    image_url=photo.get('largeImageURL', photo.get('webformatURL')),
                    thumbnail_url=photo.get('previewURL'),
                    source=self.get_source_name(),
                    license_type=LicenseType.PIXABAY.value,
                    license_url='https://pixabay.com/service/license/',
                    title=photo.get('tags'),
                    description=photo.get('tags'),
                    author=photo.get('user'),
                    author_url=f"https://pixabay.com/users/{photo.get('user')}-{photo.get('user_id')}/" if photo.get('user') else None,
                    width=photo.get('imageWidth'),
                    height=photo.get('imageHeight'),
                    page_url=photo.get('pageURL'),
                    download_url=photo.get('largeImageURL', photo.get('webformatURL'))
                )
                results.append(result)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Pixabay: {e}")
        except Exception as e:
            print(f"Unexpected error in Pixabay source: {e}")

        return results[:max_results]
