#!/usr/bin/env python3
"""Web-based GUI for the Licensed Image Finder."""

from flask import Flask, render_template, request, jsonify
from src.image_finder import LicensedImageFinder
from src.config import Config

app = Flask(__name__)
finder = LicensedImageFinder()


@app.route('/')
def index():
    """Render the main search page."""
    status = finder.get_status()
    return render_template('index.html', status=status)


@app.route('/search', methods=['POST'])
def search():
    """Handle search requests and return results."""
    data = request.get_json()
    query = data.get('query', '')
    entity_type = data.get('entity_type', 'person')
    max_results = int(data.get('max_results', 20))
    require_face = data.get('require_face', True)

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    # Perform the search
    results = finder.find_images(
        query=query,
        entity_type=entity_type,
        max_results=max_results,
        require_face=require_face and entity_type == 'person'
    )

    return jsonify({
        'query': query,
        'entity_type': entity_type,
        'total_results': len(results),
        'face_filter_applied': require_face and entity_type == 'person',
        'images': results
    })


@app.route('/status')
def status():
    """Get the current status of the image finder."""
    return jsonify(finder.get_status())


if __name__ == '__main__':
    print("Starting Licensed Image Finder Web GUI...")
    print("Open your browser and navigate to: http://localhost:5000")
    print("\nAvailable sources:", ', '.join(finder.get_available_sources()))
    print("\nPress Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=5000)
