"""Face detection module for verifying person images."""

import face_recognition
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Tuple
from src.config import Config


class FaceDetector:
    """Detect faces in images to verify relevance for person entities."""

    # Minimum size for a face relative to image dimensions
    # This helps filter out tiny detections that are likely false positives
    MIN_FACE_SIZE_RATIO = 0.05  # Face must be at least 5% of image width/height

    # Detection model: "hog" (faster, CPU) or "cnn" (more accurate, GPU/CPU)
    # Using "hog" for speed since we process many images
    DETECTION_MODEL = "hog"

    def __init__(self):
        """Initialize the face detector with face_recognition library."""
        self.is_initialized = True
        print("✓ Face detection initialized (using face_recognition library)")

    def detect_faces_from_url(self, image_url: str) -> Tuple[bool, int]:
        """Detect faces in an image from a URL using face_recognition library.

        This uses dlib's CNN-based face detector which is state-of-the-art
        and significantly more accurate than Haar Cascade.

        Args:
            image_url: URL of the image to analyze

        Returns:
            Tuple of (has_face: bool, face_count: int)
        """
        if not self.is_initialized:
            return False, 0

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

            # Convert to PIL Image
            img = Image.open(BytesIO(response.content))

            # Convert to RGB if needed (face_recognition requires RGB)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert to numpy array
            img_array = np.array(img)

            # Get image dimensions
            img_height, img_width = img_array.shape[:2]

            # Detect faces using face_recognition library
            # Returns list of face locations: [(top, right, bottom, left), ...]
            face_locations = face_recognition.face_locations(
                img_array,
                model=self.DETECTION_MODEL
            )

            # Count valid faces (filter by size to reduce false positives)
            valid_face_count = 0

            for (top, right, bottom, left) in face_locations:
                # Calculate face dimensions
                face_width = right - left
                face_height = bottom - top

                # Check if face is large enough (filters out tiny false positives)
                min_dimension = min(img_width, img_height) * self.MIN_FACE_SIZE_RATIO
                if face_width >= min_dimension and face_height >= min_dimension:
                    valid_face_count += 1

            has_face = valid_face_count > 0

            return has_face, valid_face_count

        except requests.exceptions.RequestException as e:
            print(f"Error downloading image for face detection: {e}")
            return False, 0
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return False, 0

    def is_available(self) -> bool:
        """Check if face detection is available."""
        return self.is_initialized
