"""European Commission (commission.europa.eu) image source using Ignira search and Crawl.ninja scraping."""

import requests
import re
from typing import List, Optional
from src.sources.base import ImageSource
from src.models import ImageResult, LicenseType
from src.config import Config


class EuropaSource(ImageSource):
    """Search commission.europa.eu for European Commission images under CC BY 4.0 license.

    This source:
    1. Searches using Ignira API with site:commission.europa.eu filter
    2. Scrapes each result page using Crawl.ninja to extract image credits
    3. Filters out copyrighted images (AP, Reuters, Getty, etc.)
    4. Returns images eligible for CC BY 4.0 (Attribution) license
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
        return "European Commission"

    def is_available(self) -> bool:
        """Check if both API keys are configured."""
        return self.ignira_api_key is not None and self.crawl_ninja_api_key is not None

    def search(self, query: str, max_results: int = 10) -> List[ImageResult]:
        """Search commission.europa.eu for images.

        Args:
            query: Search query string
            max_results: Maximum number of results to return

        Returns:
            List of ImageResult objects (filtered to exclude copyrighted images)
        """
        if not self.is_available():
            print(f"[European Commission] ✗ Source not available (missing API keys)")
            return []

        print(f"\n{'='*80}")
        print(f"[European Commission] Starting search for: '{query}'")
        print(f"{'='*80}")

        results = []

        try:
            # Step 1: Search using Ignira API with site:commission.europa.eu filter
            # Request more results (3x) since we'll filter out non-europa URLs
            search_query = f"{query} site:commission.europa.eu"
            print(f"[European Commission] STEP 1: Searching with Ignira API")
            print(f"[European Commission]   Query: '{search_query}'")
            search_limit = max_results * 3  # Request 3x to account for filtering
            search_results = self._search_images(search_query, search_limit)
            print(f"[European Commission]   ✓ Found {len(search_results)} image results from search API")

            # Step 1.5: Filter to ONLY commission.europa.eu URLs
            print(f"\n[European Commission] STEP 1.5: Filtering to ONLY commission.europa.eu URLs")
            filtered_results = []
            for result in search_results:
                url = result.get('url', '')
                if 'commission.europa.eu' in url.lower():
                    filtered_results.append(result)
                    print(f"[European Commission]   ✓ KEPT: {url}")
                else:
                    print(f"[European Commission]   ✗ REJECTED (not commission.europa.eu): {url}")

            print(f"[European Commission]   Filtered: {len(search_results)} → {len(filtered_results)} results")

            if len(filtered_results) == 0:
                print(f"[European Commission]   ✗ No commission.europa.eu URLs found in search results!")
                return []

            # Step 2: For each result, scrape the page and check credits
            print(f"\n[European Commission] STEP 2: Processing each result (relevance + credit filtering)")
            for idx, search_result in enumerate(filtered_results, 1):
                print(f"\n[European Commission] --- Result {idx}/{len(filtered_results)} ---")
                print(f"[European Commission]   Title: {search_result.get('title', 'No title')}")
                print(f"[European Commission]   URL: {search_result['url']}")
                print(f"[European Commission]   Thumbnail: {search_result.get('thumbnail', 'None')[:80]}...")

                # Check relevance: query must appear in title or description
                title = search_result.get('title', '')
                description = search_result.get('content', '')
                is_relevant = (
                    query.lower() in title.lower() or
                    query.lower() in description.lower()
                )

                if not is_relevant:
                    print(f"[European Commission]   ✗ SKIPPED: Query '{query}' not in title or description (irrelevant)")
                    continue

                print(f"[European Commission]   ✓ Relevant: Query found in {'title' if query.lower() in title.lower() else 'description'}")

                # Extract image credit from the page
                credit = self._extract_image_credit(search_result['url'], idx, len(filtered_results))

                # Step 3: Filter out copyrighted images (AP, Reuters, Getty, etc.)
                if credit and self._is_copyrighted(credit):
                    print(f"[European Commission]   ✗ SKIPPED: Copyrighted credit detected")
                    continue  # Skip copyrighted images

                print(f"[European Commission]   ✓ INCLUDED: Eligible for CC BY 4.0")

                # Create ImageResult for CC BY 4.0 eligible images
                result = ImageResult(
                    image_url=search_result.get('thumbnail') or search_result.get('url'),
                    thumbnail_url=search_result.get('thumbnail') or search_result.get('url'),
                    source=self.get_source_name(),
                    license_type=LicenseType.CC_BY.value,
                    license_url='https://commission.europa.eu/legal-notice_en#copyright-notice',
                    title=search_result.get('title'),
                    description=search_result.get('content'),
                    author=credit if credit else 'European Commission',
                    author_url=None,
                    width=None,  # Not provided by search API
                    height=None,  # Not provided by search API
                    page_url=search_result.get('url'),
                    download_url=search_result.get('thumbnail') or search_result.get('url')
                )
                results.append(result)

                # Stop if we have enough results
                if len(results) >= max_results:
                    print(f"[European Commission]   Reached max_results limit ({max_results})")
                    break

            print(f"\n{'='*80}")
            print(f"[European Commission] COMPLETE: Returning {len(results)} eligible images")
            print(f"{'='*80}\n")

        except requests.exceptions.RequestException as e:
            print(f"[European Commission] ✗ Error fetching from European Commission: {e}")
        except Exception as e:
            print(f"[European Commission] ✗ Unexpected error in European Commission source: {e}")
            import traceback
            traceback.print_exc()

        return results[:max_results]

    def _search_images(self, query: str, limit: int = 10) -> List[dict]:
        """Search for images using Ignira API.

        Args:
            query: Search query (already includes site:commission.europa.eu)
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

        print(f"[European Commission]   Ignira API Request:")
        print(f"[European Commission]     URL: {self.IGNIRA_BASE_URL}")
        print(f"[European Commission]     Payload: {payload}")

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

        print(f"[European Commission]   Ignira API Response:")
        print(f"[European Commission]     Status: {response.status_code}")
        print(f"[European Commission]     Total Results: {data.get('totalResults', 0)}")
        print(f"[European Commission]     Returned: {len(data.get('results', []))} results")

        # Show first 3 results for debugging
        results = data.get('results', [])
        for i, result in enumerate(results[:3], 1):
            print(f"[European Commission]       #{i}: {result.get('title', 'No title')[:60]}...")
            print(f"[European Commission]            URL: {result.get('url', 'No URL')}")

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
            print(f"[European Commission]   Scraping page with Crawl.ninja...")

            headers = {
                'X-API-Key': self.crawl_ninja_api_key,
                'Content-Type': 'application/json'
            }

            payload = {
                'url': url
            }

            print(f"[European Commission]     Request: {self.CRAWL_NINJA_BASE_URL}")
            print(f"[European Commission]     Timeout: {Config.SCRAPING_TIMEOUT}s")

            response = requests.post(
                self.CRAWL_NINJA_BASE_URL,
                headers=headers,
                json=payload,
                timeout=Config.SCRAPING_TIMEOUT  # Use dedicated scraping timeout
            )
            response.raise_for_status()
            data = response.json()

            print(f"[European Commission]     ✓ Scraping successful (status: {response.status_code})")

            if data.get('success') and data.get('data'):
                markdown = data['data'].get('markdown', '')

                print(f"[European Commission]     Scraped content length: {len(markdown)} chars")
                print(f"[European Commission]     First 300 chars of markdown:")
                print(f"[European Commission]       {markdown[:300]}")

                # Look for common credit patterns in English
                credit_patterns = [
                    ('credit', r'(?i)credit[:\s]*([^\n\.]+)'),
                    ('photo', r'(?i)photo[:\s]*([^\n\.]+)'),
                    ('image', r'(?i)image[:\s]*([^\n\.]+)'),
                    ('source', r'(?i)source[:\s]*([^\n\.]+)'),
                    ('©', r'(?i)©[:\s]*([^\n\.]+)'),
                    ('copyright', r'(?i)copyright[:\s]*([^\n\.]+)'),
                    ('photographer', r'(?i)photographer[:\s]*([^\n\.]+)'),
                ]

                print(f"[European Commission]     Attempting credit extraction with {len(credit_patterns)} patterns...")
                for pattern_name, pattern in credit_patterns:
                    match = re.search(pattern, markdown)
                    if match:
                        credit = match.group(1).strip()
                        print(f"[European Commission]     ✓ Credit found with pattern '{pattern_name}': {credit}")
                        print(f"[European Commission]     Checking for copyrighted sources...")
                        is_copyrighted = self._is_copyrighted(credit)
                        if is_copyrighted:
                            print(f"[European Commission]     ⚠ Copyrighted source detected in credit!")
                        else:
                            print(f"[European Commission]     ✓ No copyrighted sources detected")
                        return credit
                    else:
                        print(f"[European Commission]       Pattern '{pattern_name}' - no match")

                print(f"[European Commission]     ✗ No credit found with any pattern")
            else:
                print(f"[European Commission]     ✗ Scraping failed or no data returned")

            return None

        except requests.exceptions.RequestException as e:
            print(f"[European Commission]   ✗ Error scraping page: {e}")
            return None
        except Exception as e:
            print(f"[European Commission]   ✗ Unexpected error scraping: {e}")
            import traceback
            traceback.print_exc()
            return None

    def _is_copyrighted(self, credit: str) -> bool:
        """Check if credit contains copyrighted sources (AP, Reuters, Getty, etc.).

        Args:
            credit: Credit text to check

        Returns:
            True if copyrighted source is found in the credit
        """
        if not credit:
            return False

        # Check for common copyrighted news/photo agencies
        copyrighted_sources = [
            'ap',  # Associated Press
            'reuters',
            'getty',
            'getty images',
            'afp',  # Agence France-Presse
            'upi',  # United Press International
            'epa',  # European Pressphoto Agency
            'shutterstock',
            'alamy',
            'corbis',
        ]

        credit_lower = credit.lower()
        for source in copyrighted_sources:
            if source in credit_lower:
                print(f"[European Commission]     Found copyrighted source: {source}")
                return True

        return False
