"""Face detection module for verifying person images."""

import cv2
import numpy as np
import requests
from io import BytesIO
from PIL import Image
from typing import Optional, Tuple
from src.config import Config


class FaceDetector:
    """Detect faces in images to verify relevance for person entities."""

    def __init__(self):
        """Initialize the face detector with OpenCV's Haar Cascade."""
        # Use OpenCV's pre-trained Haar Cascade classifier
        self.face_cascade = None
        try:
            # Try to load the Haar Cascade classifier for face detection
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
        except Exception as e:
            print(f"Warning: Could not load face detector: {e}")

    def detect_faces_from_url(self, image_url: str) -> Tuple[bool, int]:
        """Detect faces in an image from a URL.

        Args:
            image_url: URL of the image to analyze

        Returns:
            Tuple of (has_face: bool, face_count: int)
        """
        if not self.face_cascade:
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

            # Convert to RGB if needed
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Convert to numpy array for OpenCV
            img_array = np.array(img)

            # Convert RGB to BGR (OpenCV uses BGR)
            img_bgr = cv2.cvtColor(img_array, cv2.COLOR_RGB2BGR)

            # Convert to grayscale for face detection
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

            # Detect faces
            faces = self.face_cascade.detectMultiScale(
                gray,
                scaleFactor=1.1,
                minNeighbors=5,
                minSize=(30, 30)
            )

            face_count = len(faces)
            has_face = face_count > 0

            return has_face, face_count

        except requests.exceptions.RequestException as e:
            print(f"Error downloading image for face detection: {e}")
            return False, 0
        except Exception as e:
            print(f"Error detecting faces: {e}")
            return False, 0

    def is_available(self) -> bool:
        """Check if face detection is available."""
        return self.face_cascade is not None
