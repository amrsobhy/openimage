"""Gender classification for images using OpenCV DNN (lightweight alternative to TensorFlow)."""

import requests
from io import BytesIO
from PIL import Image
import cv2
import numpy as np
from typing import Optional, Literal, TYPE_CHECKING
from src.config import Config
import time
import gc
import os
import sys

if TYPE_CHECKING:
    from src.cache import ImageCache


def _get_memory_usage():
    """Get current memory usage in MB."""
    try:
        import psutil
        process = psutil.Process()
        mem_info = process.memory_info()
        return mem_info.rss / 1024 / 1024  # Convert to MB
    except:
        return -1


class GenderClassifier:
    """Classify gender in images using OpenCV DNN (lightweight, no TensorFlow)."""

    # Gender labels for the model
    GENDER_LIST = ['Male', 'Female']

    # Model input size (required by the Caffe model)
    MODEL_MEAN_VALUES = (78.4263377603, 87.7689143744, 114.895847746)

    def __init__(self, cache: Optional['ImageCache'] = None):
        """Initialize the gender classifier with OpenCV DNN.

        Args:
            cache: Optional ImageCache instance for caching gender detection results
        """
        self.cache = cache
        self.last_analysis_time = 0
        self.min_delay_between_calls = 0.1  # Much faster than DeepFace - only 100ms delay
        self.gender_net = None
        self.is_initialized = False

        print(f"[DEBUG] Memory before loading OpenCV gender model: {_get_memory_usage():.1f} MB")
        sys.stdout.flush()

        # Load the gender classification model
        try:
            model_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'models')
            gender_proto = os.path.join(model_dir, 'gender_deploy.prototxt')
            gender_model = os.path.join(model_dir, 'gender_net.caffemodel')

            if not os.path.exists(gender_proto) or not os.path.exists(gender_model):
                print(f"⚠ Gender classification models not found in {model_dir}")
                print(f"  Expected: gender_deploy.prototxt and gender_net.caffemodel")
                return

            print("✓ Loading OpenCV gender classification model...")
            sys.stdout.flush()

            self.gender_net = cv2.dnn.readNet(gender_model, gender_proto)

            # Use CPU backend (no GPU needed)
            self.gender_net.setPreferableBackend(cv2.dnn.DNN_BACKEND_OPENCV)
            self.gender_net.setPreferableTarget(cv2.dnn.DNN_TARGET_CPU)

            self.is_initialized = True

            print(f"✓ Gender classification initialized (OpenCV DNN - lightweight)")
            print(f"[DEBUG] Memory after loading model: {_get_memory_usage():.1f} MB")
            sys.stdout.flush()

        except Exception as e:
            print(f"⚠ Failed to load gender classification model: {e}")
            import traceback
            traceback.print_exc()
            sys.stdout.flush()

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

        # Rate limiting: Add delay between calls
        elapsed = time.time() - self.last_analysis_time
        if elapsed < self.min_delay_between_calls:
            time.sleep(self.min_delay_between_calls - elapsed)

        try:
            print(f"[DEBUG] Memory before image download: {_get_memory_usage():.1f} MB")
            sys.stdout.flush()

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

            print(f"[DEBUG] Image downloaded, converting to OpenCV format...")
            sys.stdout.flush()

            # Convert to PIL Image first
            img = Image.open(BytesIO(response.content))

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert PIL Image to OpenCV format (BGR)
            img_array = np.array(img)
            img_cv = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            print(f"[DEBUG] Memory before gender classification: {_get_memory_usage():.1f} MB")
            sys.stdout.flush()

            # Classify gender using OpenCV DNN
            print(f"[Gender Classification] Analyzing image with OpenCV DNN...")
            sys.stdout.flush()

            analysis_start = time.time()

            # Prepare the image for the model (224x224 input size)
            blob = cv2.dnn.blobFromImage(
                img_cv,
                1.0,
                (227, 227),
                self.MODEL_MEAN_VALUES,
                swapRB=False
            )

            # Set input and run forward pass
            self.gender_net.setInput(blob)
            gender_preds = self.gender_net.forward()

            analysis_duration = time.time() - analysis_start

            # Get the gender with highest confidence
            gender_idx = gender_preds[0].argmax()
            gender_confidence = gender_preds[0][gender_idx] * 100

            gender_label = self.GENDER_LIST[gender_idx]

            # Map to our standard format
            gender = 'male' if gender_label == 'Male' else 'female'

            print(f"[Gender Classification] Detected: {gender} (confidence: {gender_confidence:.1f}%) in {analysis_duration:.3f}s")
            print(f"[DEBUG] Memory after classification: {_get_memory_usage():.1f} MB")
            sys.stdout.flush()

            # Cache the result
            if self.cache:
                self.cache.set_gender_classification(image_url, gender)

            # Update last analysis time for rate limiting
            self.last_analysis_time = time.time()

            # Force garbage collection to free memory
            gc.collect()

            print(f"[DEBUG] Memory after cleanup: {_get_memory_usage():.1f} MB")
            sys.stdout.flush()

            return gender

        except requests.exceptions.RequestException as e:
            print(f"[Gender Classification] Error downloading image: {e}")
            return None
        except Exception as e:
            print(f"[Gender Classification] EXCEPTION in classify_gender_from_url!")
            print(f"[DEBUG] Error type: {type(e).__name__}")
            print(f"[DEBUG] Error message: {e}")
            print(f"[DEBUG] Full traceback:")
            import traceback
            traceback.print_exc()
            print(f"[DEBUG] Memory at error: {_get_memory_usage():.1f} MB")
            sys.stdout.flush()
            return None

    def is_available(self) -> bool:
        """Check if gender classification is available."""
        return self.is_initialized
