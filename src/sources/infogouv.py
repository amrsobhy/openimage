"""Info.gouv.fr image source using Ignira search and Crawl.ninja scraping."""

import requests
import re
from typing import List, Optional
from src.sources.base import ImageSource
from src.models import ImageResult, LicenseType
from src.config import Config


class InfoGouvSource(ImageSource):
    """Search info.gouv.fr for French government images under Etalab 2.0 license.

    This source:
    1. Searches using Ignira API with site:info.gouv.fr filter
    2. Scrapes each result page using Crawl.ninja to extract image credits
    3. Filters out AFP-credited images
    4. Returns images eligible for Etalab 2.0 open license
    """

    IGNIRA_BASE_URL = "https://api.ignira.xyz/api/search"
    CRAWL_NINJA_BASE_URL = "https://api.crawl.ninja/scrape/markdown"

    def __init__(self, ignira_api_key: str = None, crawl_ninja_api_key: str = None):
        """Initialize with both API keys.

        Args:
            ignira_api_key: API key for Ignira search
            crawl_ninja_api_key: API key for Crawl.ninja scraping
        """
        super().__init__(api_key=ignira_api_key)
        self.ignira_api_key = ignira_api_key
        self.crawl_ninja_api_key = crawl_ninja_api_key

    def get_source_name(self) -> str:
        return "Info.gouv.fr"

    def is_available(self) -> bool:
        """Check if both API keys are configured."""
        return self.ignira_api_key is not None and self.crawl_ninja_api_key is not None

    def search(self, query: str, max_results: int = 10) -> List[ImageResult]:
        """Search info.gouv.fr for images.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of ImageResult objects (filtered to exclude AFP credits)
        """
        if not self.is_available():
            return []

        results = []

        try:
            # Step 1: Search using Ignira API with site:info.gouv.fr filter
            search_query = f"{query} site:info.gouv.fr"
            search_results = self._search_images(search_query, max_results)

            # Step 2: For each result, scrape the page and check credits
            for search_result in search_results:
                # Extract image credit from the page
                credit = self._extract_image_credit(search_result['url'])

                # Step 3: Filter out AFP-credited images
                if credit and self._is_afp_credit(credit):
                    continue  # Skip AFP images

                # Create ImageResult for Etalab 2.0 eligible images
                result = ImageResult(
                    image_url=search_result.get('thumbnail') or search_result.get('url'),
                    thumbnail_url=search_result.get('thumbnail') or search_result.get('url'),
                    source=self.get_source_name(),
                    license_type=LicenseType.ETALAB_2_0.value,
                    license_url='https://www.etalab.gouv.fr/licence-ouverte-open-licence/',
                    title=search_result.get('title'),
                    description=search_result.get('content'),
                    author=credit if credit else search_result.get('author'),
                    author_url=None,
                    width=None,  # Not provided by search API
                    height=None,  # Not provided by search API
                    page_url=search_result.get('url'),
                    download_url=search_result.get('thumbnail') or search_result.get('url')
                )
                results.append(result)

                # Stop if we have enough results
                if len(results) >= max_results:
                    break

        except requests.exceptions.RequestException as e:
            print(f"Error fetching from Info.gouv.fr: {e}")
        except Exception as e:
            print(f"Unexpected error in Info.gouv.fr source: {e}")

        return results[:max_results]

    def _search_images(self, query: str, limit: int = 10) -> List[dict]:
        """Search for images using Ignira API.

        Args:
            query: Search query (already includes site:info.gouv.fr)
            limit: Maximum number of results

        Returns:
            List of search results
        """
        headers = {
            'Authorization': f'Bearer {self.ignira_api_key}',
            'Content-Type': 'application/json',
            'User-Agent': Config.USER_AGENT
        }

        payload = {
            'query': query,
            'limit': limit,
            'neuralSearch': False,
            'neuralAlpha': 0.7,
            'filters': {
                'categories': 'images'
            }
        }

        response = requests.post(
            self.IGNIRA_BASE_URL,
            headers=headers,
            json=payload,
            timeout=Config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        return data.get('results', [])

    def _extract_image_credit(self, url: str) -> Optional[str]:
        """Extract image credit from a page using Crawl.ninja scraping.

        Args:
            url: URL of the page to scrape

        Returns:
            Image credit text or None if not found
        """
        try:
            headers = {
                'X-API-Key': self.crawl_ninja_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'url': url
            }

            response = requests.post(
                self.CRAWL_NINJA_BASE_URL,
                headers=headers,
                json=payload,
                timeout=Config.REQUEST_TIMEOUT * 2  # Allow more time for scraping
            )
            response.raise_for_status()
            data = response.json()

            if data.get('success') and data.get('data'):
                markdown = data['data'].get('markdown', '')

                # Look for common credit patterns in French
                credit_patterns = [
                    r'(?i)crédit[:\s]*([^\n\.]+)',
                    r'(?i)photo[:\s]*([^\n\.]+)',
                    r'(?i)source[:\s]*([^\n\.]+)',
                    r'(?i)©[:\s]*([^\n\.]+)',
                    r'(?i)copyright[:\s]*([^\n\.]+)',
                ]

                for pattern in credit_patterns:
                    match = re.search(pattern, markdown)
                    if match:
                        return match.group(1).strip()

            return None

        except requests.exceptions.RequestException as e:
            print(f"Error scraping page {url}: {e}")
            return None
        except Exception as e:
            print(f"Unexpected error scraping {url}: {e}")
            return None

    def _is_afp_credit(self, credit: str) -> bool:
        """Check if credit contains AFP (Agence France-Presse).

        Args:
            credit: Credit text to check

        Returns:
            True if AFP is found in the credit
        """
        if not credit:
            return False

        # Case-insensitive check for AFP
        return 'afp' in credit.lower()
