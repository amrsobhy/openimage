"""Gender classification for images to filter person search results."""

# CRITICAL: Import CPU-only TensorFlow configuration FIRST
from src.tf_cpu_init import configure_tensorflow_cpu

import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Tuple, TYPE_CHECKING, Literal
from src.config import Config

if TYPE_CHECKING:
    from src.cache import ImageCache

# Try to import DeepFace, but make it optional
# Wrap in comprehensive error handling to prevent worker crashes
try:
    from deepface import DeepFace
    DEEPFACE_AVAILABLE = True
    print("✓ DeepFace imported successfully")
except ImportError as e:
    DEEPFACE_AVAILABLE = False
    print(f"⚠ DeepFace not available: {e}")
except Exception as e:
    # Catch any other errors during DeepFace import (e.g., TensorFlow initialization errors)
    DEEPFACE_AVAILABLE = False
    print(f"⚠ DeepFace initialization failed: {e}")
    print("  Gender classification will be disabled")


class GenderClassifier:
    """Classify gender in images for person entity filtering."""

    def __init__(self, cache: Optional['ImageCache'] = None):
        """Initialize the gender classifier.

        Args:
            cache: Optional ImageCache instance for caching gender detection results
        """
        self.is_initialized = DEEPFACE_AVAILABLE
        self.cache = cache

        if self.is_initialized:
            print("✓ Gender classification initialized (using DeepFace)")
        else:
            print("⚠ DeepFace not available - gender filtering disabled")
            print("  Install with: pip install deepface")

    def classify_gender_from_url(self, image_url: str) -> Optional[Literal['male', 'female']]:
        """Classify the dominant gender in an image from a URL.

        Args:
            image_url: URL of the image to analyze

        Returns:
            'male', 'female', or None if detection fails or is unavailable
        """
        if not self.is_initialized:
            return None

        # Check cache first
        if self.cache:
            cached_result = self.cache.get_gender_classification(image_url)
            if cached_result is not None:
                return cached_result

        try:
            # Download the image
            headers = {
                'User-Agent': Config.USER_AGENT
            }
            response = requests.get(
                image_url,
                timeout=Config.REQUEST_TIMEOUT,
                headers=headers,
                stream=True
            )
            response.raise_for_status()

            # Convert to PIL Image and save to temporary location
            img = Image.open(BytesIO(response.content))

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Save to temporary file (DeepFace works with file paths)
            import tempfile
            with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as tmp_file:
                img.save(tmp_file.name, format='JPEG')
                tmp_path = tmp_file.name

            try:
                # Analyze the image for gender
                # enforce_detection=False allows processing even if face detection fails
                # This is useful for images where face detection might be imperfect
                # Wrap in try-except to catch any TensorFlow/CUDA errors
                analysis = DeepFace.analyze(
                    img_path=tmp_path,
                    actions=['gender'],
                    enforce_detection=False,
                    silent=True,
                    detector_backend='opencv'  # Use OpenCV instead of default to avoid TF issues
                )

                # DeepFace returns a list of results (one per detected face)
                # We'll use the first/dominant result
                if isinstance(analysis, list) and len(analysis) > 0:
                    result = analysis[0]
                else:
                    result = analysis

                # Extract gender with highest confidence
                gender_data = result.get('gender', {})

                # DeepFace returns probabilities like {'Man': 99.5, 'Woman': 0.5}
                if isinstance(gender_data, dict):
                    man_score = gender_data.get('Man', 0)
                    woman_score = gender_data.get('Woman', 0)

                    if man_score > woman_score:
                        gender = 'male'
                    else:
                        gender = 'female'

                    print(f"[Gender Classification] Detected: {gender} (Man: {man_score:.1f}%, Woman: {woman_score:.1f}%)")
                else:
                    # Fallback: DeepFace sometimes returns 'Man' or 'Woman' as dominant_gender
                    dominant = result.get('dominant_gender', '').lower()
                    if 'man' in dominant:
                        gender = 'male'
                    elif 'woman' in dominant:
                        gender = 'female'
                    else:
                        print(f"[Gender Classification] Could not determine gender from result: {result}")
                        return None

                # Cache the result
                if self.cache:
                    self.cache.set_gender_classification(image_url, gender)

                return gender

            finally:
                # Clean up temporary file
                import os
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

        except requests.exceptions.RequestException as e:
            print(f"[Gender Classification] Error downloading image: {e}")
            return None
        except Exception as e:
            print(f"[Gender Classification] Error classifying gender: {e}")
            return None

    def is_available(self) -> bool:
        """Check if gender classification is available."""
        return self.is_initialized
