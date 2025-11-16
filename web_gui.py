#!/usr/bin/env python3
"""Web-based GUI for the Licensed Image Finder."""

import sys
import io
import json
import threading
import queue
from flask import Flask, render_template, request, jsonify, Response
from src.image_finder import LicensedImageFinder
from src.config import Config

app = Flask(__name__)

# Lazy initialization - create finder on first request to avoid hanging during startup
finder = None

def get_finder():
    """Get or create the LicensedImageFinder instance."""
    global finder
    if finder is None:
        print("Initializing LicensedImageFinder (this may download ML models on first run)...")
        finder = LicensedImageFinder()
        print("✓ LicensedImageFinder initialized")
    return finder


class StreamCapture:
    """Capture stdout and make it available for streaming."""

    def __init__(self):
        self.queue = queue.Queue()
        self.original_stdout = sys.stdout

    def write(self, text):
        """Write to both original stdout and queue."""
        self.original_stdout.write(text)
        self.original_stdout.flush()
        if text.strip():
            self.queue.put(text)

    def flush(self):
        """Flush the original stdout."""
        self.original_stdout.flush()

    def get_lines(self):
        """Get all available lines from the queue."""
        lines = []
        while not self.queue.empty():
            try:
                lines.append(self.queue.get_nowait())
            except queue.Empty:
                break
        return lines


@app.route('/')
def index():
    """Render the main search page."""
    status = get_finder().get_status()
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
    results = get_finder().find_images(
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


@app.route('/search-stream', methods=['POST'])
def search_stream():
    """Handle search requests with real-time progress streaming via SSE."""
    data = request.get_json()
    query = data.get('query', '')
    entity_type = data.get('entity_type', 'person')
    max_results = int(data.get('max_results', 20))
    require_face = data.get('require_face', True)

    if not query:
        return jsonify({'error': 'Query is required'}), 400

    def generate():
        """Generator function to stream progress updates."""
        # Create a StreamCapture instance to capture stdout in real-time
        stream_capture = StreamCapture()
        old_stdout = sys.stdout
        sys.stdout = stream_capture

        # Store results from the search thread
        search_results = {'data': None, 'error': None}

        def run_search():
            """Run the search in a background thread."""
            try:
                results = get_finder().find_images(
                    query=query,
                    entity_type=entity_type,
                    max_results=max_results,
                    require_face=require_face and entity_type == 'person'
                )
                search_results['data'] = results
            except Exception as e:
                search_results['error'] = str(e)

        try:
            # Start the search
            yield f"data: {json.dumps({'type': 'status', 'message': 'Starting search...'})}\n\n"

            # Start search in background thread
            search_thread = threading.Thread(target=run_search)
            search_thread.start()

            # Stream progress messages as they arrive
            while search_thread.is_alive() or not stream_capture.queue.empty():
                lines = stream_capture.get_lines()
                for line in lines:
                    yield f"data: {json.dumps({'type': 'progress', 'message': line})}\n\n"

                # Small delay to avoid busy-waiting
                if search_thread.is_alive() and stream_capture.queue.empty():
                    threading.Event().wait(0.1)

            # Wait for thread to complete
            search_thread.join()

            # Restore stdout
            sys.stdout = old_stdout

            # Check for errors
            if search_results['error']:
                yield f"data: {json.dumps({'type': 'error', 'message': search_results['error']})}\n\n"
                return

            # Send the final results
            result_data = {
                'type': 'complete',
                'results': {
                    'query': query,
                    'entity_type': entity_type,
                    'total_results': len(search_results['data']),
                    'face_filter_applied': require_face and entity_type == 'person',
                    'images': search_results['data']
                }
            }
            yield f"data: {json.dumps(result_data)}\n\n"

        except Exception as e:
            sys.stdout = old_stdout
            yield f"data: {json.dumps({'type': 'error', 'message': str(e)})}\n\n"

    return Response(generate(), mimetype='text/event-stream')


@app.route('/status')
def status():
    """Get the current status of the image finder."""
    return jsonify(get_finder().get_status())


if __name__ == '__main__':
    print("Starting Licensed Image Finder Web GUI...")
    print("Initializing image finder (this may take a moment on first run)...")

    # Initialize finder eagerly when running directly
    image_finder = get_finder()

    print("\nOpen your browser and navigate to: http://localhost:8080")
    print("\nAvailable sources:", ', '.join(image_finder.get_available_sources()))
    print("\nPress Ctrl+C to stop the server")
    app.run(debug=True, host='0.0.0.0', port=8080)
