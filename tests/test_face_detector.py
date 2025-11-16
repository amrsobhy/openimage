"""Tests for face detection."""

import pytest
from src.face_detector import FaceDetector


def test_face_detector_initialization():
    """Test face detector initialization."""
    detector = FaceDetector()
    # Should initialize without errors
    assert detector is not None


def test_face_detector_availability():
    """Test checking if face detector is available."""
    detector = FaceDetector()
    # Should be available if OpenCV is properly installed
    available = detector.is_available()
    assert isinstance(available, bool)


@pytest.mark.skipif(not FaceDetector().is_available(), reason="Face detector not available")
def test_face_detection_with_image():
    """Test face detection with a real image URL."""
    detector = FaceDetector()

    # Test with a known image that should have a face (Wikimedia Commons)
    # This is a public domain image of Albert Einstein
    test_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/d3/Albert_Einstein_Head.jpg/220px-Albert_Einstein_Head.jpg"

    has_face, face_count = detector.detect_faces_from_url(test_url)

    # Should detect at least one face
    assert isinstance(has_face, bool)
    assert isinstance(face_count, int)
    # This specific image should have a face
    assert has_face is True
    assert face_count >= 1


def test_face_detection_with_invalid_url():
    """Test face detection with invalid URL."""
    detector = FaceDetector()

    has_face, face_count = detector.detect_faces_from_url("https://invalid-url-that-does-not-exist.com/image.jpg")

    # Should return False and 0 for invalid URLs
    assert has_face is False
    assert face_count == 0
