"""Wikimedia Commons image source."""

import requests
from typing import List
from src.sources.base import ImageSource
from src.models import ImageResult, LicenseType
from src.config import Config


class WikimediaSource(ImageSource):
    """Search Wikimedia Commons for freely licensed images."""

    BASE_URL = "https://commons.wikimedia.org/w/api.php"

    def get_source_name(self) -> str:
        return "Wikimedia Commons"

    def search(self, query: str, max_results: int = 10) -> List[ImageResult]:
        """Search Wikimedia Commons for images.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of ImageResult objects
        """
        results = []

        try:
            # Search for images using the MediaWiki API
            search_params = {
                'action': 'query',
                'format': 'json',
                'generator': 'search',
                'gsrsearch': f'filetype:bitmap {query}',
                'gsrlimit': max_results,
                'gsrnamespace': 6,  # File namespace
                'prop': 'imageinfo|categories',
                'iiprop': 'url|size|extmetadata',
                'iiurlwidth': 400,  # Thumbnail width
            }

            headers = {
                'User-Agent': Config.USER_AGENT
            }

            response = requests.get(
                self.BASE_URL,
                params=search_params,
                headers=headers,
                timeout=Config.REQUEST_TIMEOUT
            )
            response.raise_for_status()
            data = response.json()

            if 'query' not in data or 'pages' not in data['query']:
                return results

            for page_id, page in data['query']['pages'].items():
                if 'imageinfo' not in page:
                    continue

                image_info = page['imageinfo'][0]
                extmetadata = image_info.get('extmetadata', {})

                # Extract license information
                license_info = extmetadata.get('LicenseShortName', {}).get('value', '')
                license_url = extmetadata.get('LicenseUrl', {}).get('value', '')

                # Determine license type
                license_type = self._parse_license(license_info)

                # Get author information
                author = extmetadata.get('Artist', {}).get('value', 'Unknown')
                # Remove HTML tags from author
                import re
                author = re.sub('<[^<]+?>', '', author) if author else 'Unknown'

                # Get description
                description = extmetadata.get('ImageDescription', {}).get('value', '')
                description = re.sub('<[^<]+?>', '', description) if description else None

                result = ImageResult(
                    image_url=image_info.get('url', ''),
                    thumbnail_url=image_info.get('thumburl', image_info.get('url', '')),
                    source=self.get_source_name(),
                    license_type=license_type,
                    license_url=license_url or 'https://commons.wikimedia.org/wiki/Commons:Licensing',
                    title=page.get('title', '').replace('File:', ''),
                    description=description[:200] if description else None,
                    author=author[:100] if author else None,
                    width=image_info.get('width'),
                    height=image_info.get('height'),
                    page_url=image_info.get('descriptionurl', ''),
                    download_url=image_info.get('url', '')
                )

                # Only include if it's commercially safe
                if result.is_commercial_safe():
                    results.append(result)

        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Wikimedia: {e}")
        except Exception as e:
            print(f"Unexpected error in Wikimedia source: {e}")

        return results[:max_results]

    def _parse_license(self, license_str: str) -> str:
        """Parse license string to standard license type."""
        license_str_lower = license_str.lower()

        if 'cc0' in license_str_lower or 'cc-zero' in license_str_lower:
            return LicenseType.CC0.value
        elif 'cc-by-sa' in license_str_lower:
            return LicenseType.CC_BY_SA.value
        elif 'cc-by' in license_str_lower:
            return LicenseType.CC_BY.value
        elif 'public domain' in license_str_lower or 'pd' in license_str_lower:
            return LicenseType.PUBLIC_DOMAIN.value
        else:
            # Default to CC BY for Wikimedia if unclear
            return LicenseType.CC_BY.value
