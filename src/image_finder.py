"""Main image finder module that aggregates results from multiple sources."""

import concurrent.futures
from typing import List, Dict, Any, Optional
from src.models import ImageResult
from src.config import Config
from src.face_detector import FaceDetector
from src.gender_detector import GenderDetector
from src.gender_classifier import GenderClassifier
from src.cache import ImageCache
from src.sources.wikimedia import WikimediaSource
from src.sources.unsplash import UnsplashSource
from src.sources.pexels import PexelsSource
from src.sources.pixabay import PixabaySource
from src.sources.infogouv import InfoGouvSource


class LicensedImageFinder:
    """Find high-quality, license-safe images from multiple sources."""

    def __init__(self, enable_cache: bool = True):
        """Initialize the image finder with all available sources.

        Args:
            enable_cache: Enable SQLite caching to avoid repeating API requests
        """
        self.sources = []
        self.cache = ImageCache() if enable_cache else None
        self.face_detector = FaceDetector(cache=self.cache) if Config.ENABLE_FACE_DETECTION else None
        self.gender_detector = GenderDetector() if Config.ENABLE_GENDER_FILTERING else None
        self.gender_classifier = GenderClassifier(cache=self.cache) if Config.ENABLE_GENDER_FILTERING else None

        # Initialize all image sources
        self._init_sources()

    def _init_sources(self):
        """Initialize all configured image sources."""
        # Wikimedia Commons (no API key needed)
        self.sources.append(WikimediaSource())

        # Unsplash (requires API key)
        if Config.UNSPLASH_ACCESS_KEY:
            self.sources.append(UnsplashSource(Config.UNSPLASH_ACCESS_KEY))

        # Pexels (requires API key)
        if Config.PEXELS_API_KEY:
            self.sources.append(PexelsSource(Config.PEXELS_API_KEY))

        # Pixabay (requires API key)
        if Config.PIXABAY_API_KEY:
            self.sources.append(PixabaySource(Config.PIXABAY_API_KEY))

        # Info.gouv.fr (requires both Ignira and Crawl.ninja API keys)
        if Config.IGNIRA_API_KEY and Config.CRAWL_NINJA_API_KEY:
            self.sources.append(InfoGouvSource(Config.IGNIRA_API_KEY, Config.CRAWL_NINJA_API_KEY))

    def _search_source_with_cache(self, source, query: str, entity_type: str) -> List[ImageResult]:
        """Search a source with cache support.

        Args:
            source: Image source to search
            query: Search query
            entity_type: Type of entity

        Returns:
            List of ImageResult objects
        """
        source_name = source.get_source_name()

        # Check cache first
        if self.cache:
            cached_results = self.cache.get(query, entity_type, source_name)
            if cached_results is not None:
                print(f"✓ Cache hit for {source_name}: {query}")
                # Convert cached dicts back to ImageResult objects
                return [ImageResult(**result) for result in cached_results]

        # Cache miss - fetch from API
        print(f"→ Fetching from {source_name}: {query}")
        results = source.search(query, Config.MAX_RESULTS_PER_SOURCE)

        # Store in cache
        if self.cache and results:
            # Convert ImageResult objects to dicts for caching
            cached_data = [result.to_dict() for result in results]
            self.cache.set(query, entity_type, source_name, cached_data)
            print(f"✓ Cached {len(results)} results from {source_name}")

        return results

    def find_images(
        self,
        query: str,
        entity_type: str = "person",
        max_results: int = 20,
        require_face: bool = True
    ) -> List[Dict[str, Any]]:
        """Find high-quality, license-safe images for the given query.

        Args:
            query: Search query (e.g., person name, entity)
            entity_type: Type of entity ("person", "place", "thing", etc.)
            max_results: Maximum number of results to return
            require_face: If True and entity_type is "person", filter for images with faces

        Returns:
            List of dictionaries containing image results with license information
        """
        all_results = []

        # Search all sources in parallel (with caching)
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.sources)) as executor:
            future_to_source = {
                executor.submit(
                    self._search_source_with_cache,
                    source,
                    query,
                    entity_type
                ): source for source in self.sources
            }

            for future in concurrent.futures.as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Error searching {source.get_source_name()}: {e}")

        # Filter by relevance: query must appear in title or description
        print(f"\nFiltering {len(all_results)} results for relevance to '{query}'...")
        all_results = self._filter_by_relevance(all_results, query)
        print(f"After relevance filtering: {len(all_results)} results")

        # Apply face detection for person entities if enabled
        if entity_type.lower() == "person" and require_face and self.face_detector:
            all_results = self._filter_by_face_detection(all_results)

        # Apply gender filtering for person entities if enabled
        if entity_type.lower() == "person" and self.gender_detector and self.gender_classifier:
            all_results = self._filter_by_gender(all_results, query)

        # Calculate quality scores
        all_results = self._calculate_quality_scores(all_results, entity_type)

        # Sort by quality score (highest first)
        all_results.sort(key=lambda x: x.quality_score or 0, reverse=True)

        # Return top results
        return [result.to_dict() for result in all_results[:max_results]]

    def _filter_by_face_detection(self, results: List[ImageResult]) -> List[ImageResult]:
        """Filter results to only include images with detected faces.

        Args:
            results: List of ImageResult objects

        Returns:
            Filtered list of ImageResult objects with faces
        """
        if not self.face_detector or not self.face_detector.is_available():
            return results

        filtered_results = []
        detection_errors = 0

        for result in results:
            try:
                has_face, face_count = self.face_detector.detect_faces_from_url(
                    result.thumbnail_url or result.image_url
                )
                result.has_face = has_face

                if has_face:
                    print(f"  ✓ Face detected in: {result.title[:50]}")
                    filtered_results.append(result)
                else:
                    print(f"  ✗ No face detected in: {result.title[:50]}")
            except Exception as e:
                print(f"  ⚠ Face detection failed for: {result.title[:50]} - {e}")
                detection_errors += 1
                # DO NOT include images where face detection fails
                # This ensures we only return images with confirmed faces

        if detection_errors > 0:
            print(f"\n⚠ Warning: Face detection failed for {detection_errors} images (excluded from results)")

        return filtered_results

    def _filter_by_gender(self, results: List[ImageResult], query: str) -> List[ImageResult]:
        """Filter results to only include images matching the expected gender.

        Args:
            results: List of ImageResult objects
            query: Search query (person name)

        Returns:
            Filtered list of ImageResult objects matching expected gender
        """
        if not self.gender_detector or not self.gender_classifier:
            return results

        if not self.gender_detector.enabled or not self.gender_classifier.is_available():
            return results

        # Detect expected gender from query using LLM
        expected_gender = self.gender_detector.detect_gender(query)

        if not expected_gender:
            print(f"\n⚠ Could not determine gender from query, skipping gender filtering")
            return results

        print(f"\nFiltering {len(results)} results for gender: {expected_gender}")

        filtered_results = []
        classification_errors = 0

        for result in results:
            try:
                detected_gender = self.gender_classifier.classify_gender_from_url(
                    result.thumbnail_url or result.image_url
                )

                if detected_gender == expected_gender:
                    print(f"  ✓ Gender match ({detected_gender}): {result.title[:50]}")
                    filtered_results.append(result)
                elif detected_gender:
                    print(f"  ✗ Gender mismatch (expected {expected_gender}, got {detected_gender}): {result.title[:50]}")
                else:
                    print(f"  ⚠ Could not detect gender: {result.title[:50]}")
                    # Include images where gender detection fails to avoid being too restrictive
                    filtered_results.append(result)

            except Exception as e:
                print(f"  ⚠ Gender classification failed for: {result.title[:50]} - {e}")
                classification_errors += 1
                # Include images where classification fails
                filtered_results.append(result)

        if classification_errors > 0:
            print(f"\n⚠ Warning: Gender classification failed for {classification_errors} images (included in results)")

        print(f"After gender filtering: {len(filtered_results)} results")
        return filtered_results

    def _filter_by_relevance(self, results: List[ImageResult], query: str) -> List[ImageResult]:
        """Filter results to only include images relevant to the query.

        Args:
            results: List of ImageResult objects
            query: Search query string

        Returns:
            Filtered list of ImageResult objects where query terms appear in title or description
        """
        filtered_results = []

        # Split query into individual words and filter out very short/common words
        query_words = query.lower().split()
        # Remove very short words (articles, prepositions, etc.)
        stop_words = {'a', 'an', 'the', 'le', 'la', 'les', 'de', 'du', 'des', 'et', 'ou', 'un', 'une'}
        significant_words = [w for w in query_words if len(w) > 2 and w not in stop_words]

        # If no significant words, fall back to full query matching
        if not significant_words:
            significant_words = query_words

        for result in results:
            title = (result.title or '').lower()
            description = (result.description or '').lower()
            combined_text = f"{title} {description}"

            # Check if ANY significant word from query appears in title or description
            matches = [word for word in significant_words if word in combined_text]

            if matches:
                filtered_results.append(result)
            else:
                print(f"  ✗ Irrelevant: '{result.title[:60] if result.title else 'No title'}' ({result.source})")

        return filtered_results

    def _calculate_quality_scores(
        self,
        results: List[ImageResult],
        entity_type: str
    ) -> List[ImageResult]:
        """Calculate quality scores for image results.

        Args:
            results: List of ImageResult objects
            entity_type: Type of entity being searched

        Returns:
            List of ImageResult objects with quality scores
        """
        for result in results:
            score = 0.0

            # Base score from source reliability
            source_scores = {
                'Wikimedia Commons': 0.8,
                'Unsplash': 0.9,
                'Pexels': 0.85,
                'Pixabay': 0.75,
                'Info.gouv.fr': 0.95  # High quality government source
            }
            score += source_scores.get(result.source, 0.5)

            # Image size quality
            if result.width and result.height:
                if result.width >= Config.MIN_IMAGE_WIDTH and result.height >= Config.MIN_IMAGE_HEIGHT:
                    score += 0.5
                    # Bonus for high resolution
                    if result.width >= 1920 and result.height >= 1080:
                        score += 0.3

            # Metadata completeness
            if result.title:
                score += 0.2
            if result.description:
                score += 0.15
            if result.author:
                score += 0.15

            # Face detection bonus for person entities
            if entity_type.lower() == "person" and result.has_face:
                score += 0.5

            # License preference (more permissive = higher score)
            license_scores = {
                'Public Domain': 1.0,
                'CC0 (Creative Commons Zero)': 1.0,
                'Etalab 2.0 Open License': 0.95,
                'Unsplash License': 0.95,
                'Pexels License': 0.95,
                'Pixabay License': 0.95,
                'CC BY (Attribution)': 0.9,
                'CC BY-SA (Attribution-ShareAlike)': 0.85,
            }
            score += license_scores.get(result.license_type, 0.5)

            result.quality_score = min(score, 5.0)  # Cap at 5.0

        return results

    def get_available_sources(self) -> List[str]:
        """Get list of available image sources.

        Returns:
            List of source names
        """
        return [source.get_source_name() for source in self.sources if source.is_available()]

    def get_status(self) -> Dict[str, Any]:
        """Get status of the image finder and its sources.

        Returns:
            Dictionary with status information
        """
        status = {
            'available_sources': self.get_available_sources(),
            'total_sources': len(self.sources),
            'face_detection_enabled': Config.ENABLE_FACE_DETECTION,
            'face_detection_available': self.face_detector.is_available() if self.face_detector else False,
            'cache_enabled': self.cache is not None,
            'config': {
                'max_results_per_source': Config.MAX_RESULTS_PER_SOURCE,
                'min_image_width': Config.MIN_IMAGE_WIDTH,
                'min_image_height': Config.MIN_IMAGE_HEIGHT,
            }
        }

        # Add cache statistics if caching is enabled
        if self.cache:
            status['cache_stats'] = self.cache.get_stats()

        return status
