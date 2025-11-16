"""Face detection module for verifying person images."""

import mediapipe as mp
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Tuple
from src.config import Config


class FaceDetector:
    """Detect faces in images to verify relevance for person entities."""

    # Minimum confidence threshold for face detection (0.0 to 1.0)
    # Higher values = fewer false positives but might miss some real faces
    MIN_DETECTION_CONFIDENCE = 0.7

    # Minimum size for a face relative to image dimensions
    # This helps filter out tiny detections that are likely false positives
    MIN_FACE_SIZE_RATIO = 0.05  # Face must be at least 5% of image width/height

    def __init__(self):
        """Initialize the face detector with MediaPipe's Face Detection."""
        self.face_detection = None
        try:
            # Initialize MediaPipe Face Detection
            # model_selection: 0 for faces within 2 meters, 1 for faces within 5 meters
            # min_detection_confidence: minimum confidence threshold
            mp_face_detection = mp.solutions.face_detection
            self.face_detection = mp_face_detection.FaceDetection(
                model_selection=1,  # Use model for faces within 5 meters (better for photos)
                min_detection_confidence=self.MIN_DETECTION_CONFIDENCE
            )
            print("✓ MediaPipe Face Detection initialized successfully")
        except Exception as e:
            print(f"Warning: Could not load MediaPipe face detector: {e}")

    def detect_faces_from_url(self, image_url: str) -> Tuple[bool, int]:
        """Detect faces in an image from a URL using MediaPipe.

        Args:
            image_url: URL of the image to analyze

        Returns:
            Tuple of (has_face: bool, face_count: int)
        """
        if not self.face_detection:
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

            # Convert to RGB if needed (MediaPipe requires RGB)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert to numpy array
            img_array = np.array(img)

            # Get image dimensions
            img_height, img_width = img_array.shape[:2]

            # Process the image with MediaPipe
            results = self.face_detection.process(img_array)

            # Count valid faces (filter by size to reduce false positives)
            valid_face_count = 0

            if results.detections:
                for detection in results.detections:
                    # Get bounding box
                    bbox = detection.location_data.relative_bounding_box

                    # Calculate face size in pixels
                    face_width = bbox.width * img_width
                    face_height = bbox.height * img_height

                    # Check if face is large enough (filters out tiny false positives)
                    min_dimension = min(img_width, img_height) * self.MIN_FACE_SIZE_RATIO
                    if face_width >= min_dimension and face_height >= min_dimension:
                        # Get detection confidence score
                        confidence = detection.score[0] if detection.score else 0

                        # Only count if confidence is above threshold
                        if confidence >= self.MIN_DETECTION_CONFIDENCE:
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
        return self.face_detection is not None

    def __del__(self):
        """Cleanup MediaPipe resources."""
        if self.face_detection:
            self.face_detection.close()
