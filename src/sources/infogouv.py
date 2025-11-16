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
            print(f"[Info.gouv.fr] ✗ Source not available (missing API keys)")
            return []

        print(f"\n{'='*80}")
        print(f"[Info.gouv.fr] Starting search for: '{query}'")
        print(f"{'='*80}")

        results = []

        try:
            # Step 1: Search using Ignira API with site:info.gouv.fr filter
            # Request more results (3x) since we'll filter out non-info.gouv.fr URLs
            search_query = f"{query} site:info.gouv.fr"
            print(f"[Info.gouv.fr] STEP 1: Searching with Ignira API")
            print(f"[Info.gouv.fr]   Query: '{search_query}'")
            search_limit = max_results * 3  # Request 3x to account for filtering
            search_results = self._search_images(search_query, search_limit)
            print(f"[Info.gouv.fr]   ✓ Found {len(search_results)} image results from search API")

            # Step 1.5: Filter to ONLY info.gouv.fr URLs (search API returns garbage)
            print(f"\n[Info.gouv.fr] STEP 1.5: Filtering to ONLY info.gouv.fr URLs")
            filtered_results = []
            for result in search_results:
                url = result.get('url', '')
                if 'info.gouv.fr' in url.lower():
                    filtered_results.append(result)
                    print(f"[Info.gouv.fr]   ✓ KEPT: {url}")
                else:
                    print(f"[Info.gouv.fr]   ✗ REJECTED (not info.gouv.fr): {url}")

            print(f"[Info.gouv.fr]   Filtered: {len(search_results)} → {len(filtered_results)} results")

            if len(filtered_results) == 0:
                print(f"[Info.gouv.fr]   ✗ No info.gouv.fr URLs found in search results!")
                return []

            # Step 2: For each result, scrape the page and check credits
            print(f"\n[Info.gouv.fr] STEP 2: Processing each result (scraping + filtering)")
            for idx, search_result in enumerate(filtered_results, 1):
                print(f"\n[Info.gouv.fr] --- Result {idx}/{len(filtered_results)} ---")
                print(f"[Info.gouv.fr]   Title: {search_result.get('title', 'No title')}")
                print(f"[Info.gouv.fr]   URL: {search_result['url']}")
                print(f"[Info.gouv.fr]   Thumbnail: {search_result.get('thumbnail', 'None')[:80]}...")

                # Extract image credit from the page
                credit = self._extract_image_credit(search_result['url'], idx, len(filtered_results))

                # Step 3: Filter out AFP-credited images
                if credit and self._is_afp_credit(credit):
                    print(f"[Info.gouv.fr]   ✗ SKIPPED: AFP credit detected")
                    continue  # Skip AFP images

                print(f"[Info.gouv.fr]   ✓ INCLUDED: Eligible for Etalab 2.0")

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
                    print(f"[Info.gouv.fr]   Reached max_results limit ({max_results})")
                    break

            print(f"\n{'='*80}")
            print(f"[Info.gouv.fr] COMPLETE: Returning {len(results)} eligible images")
            print(f"{'='*80}\n")

        except requests.exceptions.RequestException as e:
            print(f"[Info.gouv.fr] ✗ Error fetching from Info.gouv.fr: {e}")
        except Exception as e:
            print(f"[Info.gouv.fr] ✗ Unexpected error in Info.gouv.fr source: {e}")
            import traceback
            traceback.print_exc()

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
            'Authorization': f'Bearer {self.ignira_api_key[:20]}...',
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

        print(f"[Info.gouv.fr]   Ignira API Request:")
        print(f"[Info.gouv.fr]     URL: {self.IGNIRA_BASE_URL}")
        print(f"[Info.gouv.fr]     Payload: {payload}")

        # Use actual API key for request
        actual_headers = {
            'Authorization': f'Bearer {self.ignira_api_key}',
            'Content-Type': 'application/json',
            'User-Agent': Config.USER_AGENT
        }

        response = requests.post(
            self.IGNIRA_BASE_URL,
            headers=actual_headers,
            json=payload,
            timeout=Config.REQUEST_TIMEOUT
        )
        response.raise_for_status()
        data = response.json()

        print(f"[Info.gouv.fr]   Ignira API Response:")
        print(f"[Info.gouv.fr]     Status: {response.status_code}")
        print(f"[Info.gouv.fr]     Total Results: {data.get('totalResults', 0)}")
        print(f"[Info.gouv.fr]     Returned: {len(data.get('results', []))} results")

        # Show first 3 results for debugging
        results = data.get('results', [])
        for i, result in enumerate(results[:3], 1):
            print(f"[Info.gouv.fr]       #{i}: {result.get('title', 'No title')[:60]}...")
            print(f"[Info.gouv.fr]            URL: {result.get('url', 'No URL')}")

        return results

    def _extract_image_credit(self, url: str, idx: int = 0, total: int = 0) -> Optional[str]:
        """Extract image credit from a page using Crawl.ninja scraping.

        Args:
            url: URL of the page to scrape
            idx: Current result index (for logging)
            total: Total results (for logging)

        Returns:
            Image credit text or None if not found
        """
        try:
            print(f"[Info.gouv.fr]   Scraping page with Crawl.ninja...")

            headers = {
                'X-API-Key': self.crawl_ninja_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'url': url
            }

            print(f"[Info.gouv.fr]     Request: {self.CRAWL_NINJA_BASE_URL}")
            print(f"[Info.gouv.fr]     Timeout: {Config.SCRAPING_TIMEOUT}s")

            response = requests.post(
                self.CRAWL_NINJA_BASE_URL,
                headers=headers,
                json=payload,
                timeout=Config.SCRAPING_TIMEOUT  # Use dedicated scraping timeout
            )
            response.raise_for_status()
            data = response.json()

            print(f"[Info.gouv.fr]     ✓ Scraping successful (status: {response.status_code})")

            if data.get('success') and data.get('data'):
                markdown = data['data'].get('markdown', '')

                print(f"[Info.gouv.fr]     Scraped content length: {len(markdown)} chars")
                print(f"[Info.gouv.fr]     First 300 chars of markdown:")
                print(f"[Info.gouv.fr]       {markdown[:300]}")

                # Look for common credit patterns in French
                credit_patterns = [
                    ('crédit', r'(?i)crédit[:\s]*([^\n\.]+)'),
                    ('photo', r'(?i)photo[:\s]*([^\n\.]+)'),
                    ('source', r'(?i)source[:\s]*([^\n\.]+)'),
                    ('©', r'(?i)©[:\s]*([^\n\.]+)'),
                    ('copyright', r'(?i)copyright[:\s]*([^\n\.]+)'),
                ]

                print(f"[Info.gouv.fr]     Attempting credit extraction with {len(credit_patterns)} patterns...")
                for pattern_name, pattern in credit_patterns:
                    match = re.search(pattern, markdown)
                    if match:
                        credit = match.group(1).strip()
                        print(f"[Info.gouv.fr]     ✓ Credit found with pattern '{pattern_name}': {credit}")
                        print(f"[Info.gouv.fr]     Checking for AFP...")
                        is_afp = 'afp' in credit.lower()
                        if is_afp:
                            print(f"[Info.gouv.fr]     ⚠ AFP detected in credit!")
                        else:
                            print(f"[Info.gouv.fr]     ✓ No AFP detected")
                        return credit
                    else:
                        print(f"[Info.gouv.fr]       Pattern '{pattern_name}' - no match")

                print(f"[Info.gouv.fr]     ✗ No credit found with any pattern")
            else:
                print(f"[Info.gouv.fr]     ✗ Scraping failed or no data returned")

            return None

        except requests.exceptions.RequestException as e:
            print(f"[Info.gouv.fr]   ✗ Error scraping page: {e}")
            return None
        except Exception as e:
            print(f"[Info.gouv.fr]   ✗ Unexpected error scraping: {e}")
            import traceback
            traceback.print_exc()
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
