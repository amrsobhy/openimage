"""Gender classification for images to filter person search results."""

# CRITICAL: Import CPU-only TensorFlow configuration FIRST
from src.tf_cpu_init import configure_tensorflow_cpu

import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Tuple, TYPE_CHECKING, Literal
from src.config import Config
import time
import gc
from multiprocessing import Process, Queue, TimeoutError
from queue import Empty

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


def _analyze_gender_in_process(tmp_path: str, result_queue: Queue):
    """Run DeepFace analysis in a separate process to isolate crashes.

    Args:
        tmp_path: Path to the temporary image file
        result_queue: Queue to put the result in
    """
    try:
        # CRITICAL: Ensure CPU-only mode in subprocess
        import os
        os.environ['CUDA_VISIBLE_DEVICES'] = '-1'
        os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

        # Import DeepFace in the subprocess
        from deepface import DeepFace

        # Analyze the image
        analysis = DeepFace.analyze(
            img_path=tmp_path,
            actions=['gender'],
            enforce_detection=False,
            silent=True,
            detector_backend='opencv'
        )

        # Put the result in the queue
        result_queue.put(('success', analysis))
    except Exception as e:
        result_queue.put(('error', str(e)))


class GenderClassifier:
    """Classify gender in images for person entity filtering."""

    def __init__(self, cache: Optional['ImageCache'] = None):
        """Initialize the gender classifier.

        Args:
            cache: Optional ImageCache instance for caching gender detection results
        """
        self.is_initialized = DEEPFACE_AVAILABLE
        self.cache = cache
        self.last_analysis_time = 0
        self.min_delay_between_calls = 0.5  # Minimum 500ms between DeepFace calls

        if self.is_initialized:
            print("✓ Gender classification initialized (using DeepFace)")
        else:
            print("⚠ DeepFace not available - gender filtering disabled")
            print("  Install with: pip install deepface")

    def classify_gender_from_url(self, image_url: str) -> Optional[Literal['male', 'female']]:
        """Classify the dominant gender in an image from a URL.

        Uses process isolation and timeouts to prevent crashes.

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

        # Rate limiting: Add delay between calls to prevent resource exhaustion
        elapsed = time.time() - self.last_analysis_time
        if elapsed < self.min_delay_between_calls:
            time.sleep(self.min_delay_between_calls - elapsed)

        tmp_path = None
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

            # Run DeepFace in a separate process with timeout to isolate crashes
            result_queue = Queue()
            process = Process(target=_analyze_gender_in_process, args=(tmp_path, result_queue))
            process.start()

            # Wait for result with timeout (10 seconds max per image)
            process.join(timeout=10)

            if process.is_alive():
                # Process timed out - kill it
                print(f"[Gender Classification] Analysis timed out for: {image_url[:50]}...")
                process.terminate()
                process.join(timeout=2)
                if process.is_alive():
                    process.kill()
                    process.join()
                return None

            # Check if process exited with error
            if process.exitcode != 0:
                print(f"[Gender Classification] Process crashed with exit code {process.exitcode}")
                return None

            # Get result from queue
            try:
                status, result = result_queue.get_nowait()
            except Empty:
                print(f"[Gender Classification] No result from process")
                return None

            if status == 'error':
                print(f"[Gender Classification] Error in subprocess: {result}")
                return None

            # Parse the DeepFace analysis result
            analysis = result
            if isinstance(analysis, list) and len(analysis) > 0:
                result_data = analysis[0]
            else:
                result_data = analysis

            # Extract gender with highest confidence
            gender_data = result_data.get('gender', {})

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
                dominant = result_data.get('dominant_gender', '').lower()
                if 'man' in dominant:
                    gender = 'male'
                elif 'woman' in dominant:
                    gender = 'female'
                else:
                    print(f"[Gender Classification] Could not determine gender from result: {result_data}")
                    return None

            # Cache the result
            if self.cache:
                self.cache.set_gender_classification(image_url, gender)

            # Update last analysis time for rate limiting
            self.last_analysis_time = time.time()

            # Force garbage collection to free memory
            gc.collect()

            return gender

        except requests.exceptions.RequestException as e:
            print(f"[Gender Classification] Error downloading image: {e}")
            return None
        except Exception as e:
            print(f"[Gender Classification] Error classifying gender: {e}")
            import traceback
            traceback.print_exc()
            return None
        finally:
            # Clean up temporary file
            if tmp_path:
                import os
                try:
                    os.unlink(tmp_path)
                except Exception:
                    pass

    def is_available(self) -> bool:
        """Check if gender classification is available."""
        return self.is_initialized
