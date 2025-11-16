"""Main image finder module that aggregates results from multiple sources."""

import concurrent.futures
from typing import List, Dict, Any, Optional
from src.models import ImageResult
from src.config import Config
from src.face_detector import FaceDetector
from src.sources.wikimedia import WikimediaSource
from src.sources.unsplash import UnsplashSource
from src.sources.pexels import PexelsSource
from src.sources.pixabay import PixabaySource


class LicensedImageFinder:
    """Find high-quality, license-safe images from multiple sources."""

    def __init__(self):
        """Initialize the image finder with all available sources."""
        self.sources = []
        self.face_detector = FaceDetector() if Config.ENABLE_FACE_DETECTION else None

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

        # Search all sources in parallel for better performance
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.sources)) as executor:
            future_to_source = {
                executor.submit(
                    source.search,
                    query,
                    Config.MAX_RESULTS_PER_SOURCE
                ): source for source in self.sources
            }

            for future in concurrent.futures.as_completed(future_to_source):
                source = future_to_source[future]
                try:
                    results = future.result()
                    all_results.extend(results)
                except Exception as e:
                    print(f"Error searching {source.get_source_name()}: {e}")

        # Apply face detection for person entities if enabled
        if entity_type.lower() == "person" and require_face and self.face_detector:
            all_results = self._filter_by_face_detection(all_results)

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

        for result in results:
            try:
                has_face, face_count = self.face_detector.detect_faces_from_url(
                    result.thumbnail_url or result.image_url
                )
                result.has_face = has_face

                if has_face:
                    filtered_results.append(result)
            except Exception as e:
                print(f"Error in face detection for {result.image_url}: {e}")
                # Include the image if face detection fails
                filtered_results.append(result)

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
                'Pixabay': 0.75
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
        return {
            'available_sources': self.get_available_sources(),
            'total_sources': len(self.sources),
            'face_detection_enabled': Config.ENABLE_FACE_DETECTION,
            'face_detection_available': self.face_detector.is_available() if self.face_detector else False,
            'config': {
                'max_results_per_source': Config.MAX_RESULTS_PER_SOURCE,
                'min_image_width': Config.MIN_IMAGE_WIDTH,
                'min_image_height': Config.MIN_IMAGE_HEIGHT,
            }
        }
