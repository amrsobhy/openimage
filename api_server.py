#!/usr/bin/env python3
"""REST API server for the Licensed Image Finder."""

# CRITICAL: Import CPU-only TensorFlow configuration FIRST
# This MUST be the first import to prevent CUDA initialization errors
from src.tf_cpu_init import configure_tensorflow_cpu

import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from src.image_finder import LicensedImageFinder
from src.config import Config

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Lazy initialization to avoid hanging during startup
finder = None

def get_finder():
    """Get or create the LicensedImageFinder instance."""
    global finder
    if finder is None:
        print("Initializing LicensedImageFinder...")
        finder = LicensedImageFinder()
        print("✓ LicensedImageFinder initialized")
    return finder


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint."""
    return jsonify({
        'status': 'healthy',
        'service': 'OpenImage API',
        'version': '0.1.0'
    }), 200


@app.route('/api/status', methods=['GET'])
def get_status():
    """Get the current status of the image finder."""
    try:
        status = get_finder().get_status()
        return jsonify({
            'success': True,
            'data': status
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/sources', methods=['GET'])
def get_sources():
    """Get list of available image sources."""
    try:
        sources = get_finder().get_available_sources()
        return jsonify({
            'success': True,
            'data': {
                'sources': sources,
                'count': len(sources)
            }
        }), 200
    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/search', methods=['POST'])
def search():
    """
    Search for images.

    Request body:
    {
        "query": "search term",
        "entity_type": "person|place|thing",  // optional, default: "person"
        "max_results": 20,                     // optional, default: 20
        "require_face": true                   // optional, default: true for person entities
    }

    Response:
    {
        "success": true,
        "data": {
            "query": "search term",
            "entity_type": "person",
            "total_results": 15,
            "face_filter_applied": true,
            "gender_filter_applied": true,
            "images": [...]
        }
    }
    """
    try:
        # Validate request
        if not request.is_json:
            return jsonify({
                'success': False,
                'error': 'Content-Type must be application/json'
            }), 400

        data = request.get_json()

        # Extract parameters
        query = data.get('query')
        if not query:
            return jsonify({
                'success': False,
                'error': 'Missing required field: query'
            }), 400

        entity_type = data.get('entity_type', 'person')
        max_results = int(data.get('max_results', 20))
        require_face = data.get('require_face', True)

        # Validate entity_type
        valid_types = ['person', 'place', 'thing', 'other']
        if entity_type not in valid_types:
            return jsonify({
                'success': False,
                'error': f'Invalid entity_type. Must be one of: {", ".join(valid_types)}'
            }), 400

        # Validate max_results
        if max_results < 1 or max_results > 100:
            return jsonify({
                'success': False,
                'error': 'max_results must be between 1 and 100'
            }), 400

        # Perform the search
        results = get_finder().find_images(
            query=query,
            entity_type=entity_type,
            max_results=max_results,
            require_face=require_face and entity_type == 'person'
        )

        return jsonify({
            'success': True,
            'data': {
                'query': query,
                'entity_type': entity_type,
                'total_results': len(results),
                'face_filter_applied': require_face and entity_type == 'person',
                'gender_filter_applied': Config.ENABLE_GENDER_FILTERING and entity_type == 'person',
                'images': results
            }
        }), 200

    except Exception as e:
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({
        'success': False,
        'error': 'Endpoint not found'
    }), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({
        'success': False,
        'error': 'Internal server error'
    }), 500


if __name__ == '__main__':
    print("=" * 60)
    print("OpenImage API Server")
    print("=" * 60)
    print("\nInitializing...")

    # Get configuration info
    port = int(os.environ.get('PORT', 8000))
    host = os.environ.get('HOST', '0.0.0.0')
    debug = os.environ.get('DEBUG', 'false').lower() == 'true'

    print(f"\n✓ Server will start on http://{host}:{port}")
    print(f"✓ Debug mode: {debug}")
    print(f"✓ Face detection: {Config.ENABLE_FACE_DETECTION}")
    print(f"✓ Gender filtering: {Config.ENABLE_GENDER_FILTERING}")

    print("\nAPI Endpoints:")
    print("  GET  /health           - Health check")
    print("  GET  /api/status       - Get system status")
    print("  GET  /api/sources      - Get available sources")
    print("  POST /api/search       - Search for images")

    print("\nPress Ctrl+C to stop the server")
    print("=" * 60)

    app.run(host=host, port=port, debug=debug)
