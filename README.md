# OpenImage - Licensed Image Finder

Find high-quality, license-safe images for commercial use in news aggregation and other applications.

## Overview

OpenImage is a Python-based image finder that automatically retrieves legally-safe images from multiple trusted sources. It ensures all images are free from copyright restrictions or have appropriate commercial-use licenses, making them safe for use in commercial applications.

## Features

- **Multiple Image Sources**: Queries Wikimedia Commons, Unsplash, Pexels, and Pixabay
- **License Verification**: Ensures all images are safe for commercial use
- **Face Detection**: For person entities, verifies images contain recognizable faces using OpenCV
- **Quality Scoring**: Ranks images by quality, resolution, metadata completeness, and relevance
- **Comprehensive Metadata**: Returns URLs, licenses, authors, descriptions, and more
- **Parallel Searching**: Queries multiple sources concurrently for faster results
- **SQLite Caching**: Automatically caches API responses to avoid rate limits and improve speed
- **Flexible CLI**: Easy-to-use command-line interface with multiple options
- **Web GUI**: Modern web interface with live image thumbnails and visual search

## Installation

### Option 1: Using uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer that handles Python version management automatically.

1. Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

2. Clone and setup:
```bash
git clone https://github.com/amrsobhy/openimage.git
cd openimage
uv sync  # Automatically installs Python 3.12 and all dependencies
```

3. Run commands with uv:
```bash
uv run python3 web_gui.py
# or
uv run python3 main.py "search query"
```

### Option 2: Using pip

1. Clone the repository:
```bash
git clone https://github.com/amrsobhy/openimage.git
cd openimage
```

2. Create virtual environment and install dependencies:
```bash
python3.12 -m venv venv  # Requires Python 3.11-3.13
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. (Optional) Configure API keys for additional sources:
```bash
cp .env.example .env
# Edit .env and add your API keys
```

**Note:** Python 3.11-3.13 recommended. Python 3.14+ may have compatibility issues with some dependencies.

### API Keys (Optional but Recommended)

While Wikimedia Commons works without API keys, you can get better results by adding keys for:

- **Unsplash**: https://unsplash.com/developers
- **Pexels**: https://www.pexels.com/api/
- **Pixabay**: https://pixabay.com/api/docs/

Add these to your `.env` file.

## Usage

### Web GUI (Recommended for Testing)

The easiest way to search and visualize results is using the web interface:

```bash
python3 web_gui.py
```

Then open your browser to: **http://localhost:5000**

**Features:**
- 🔍 Live search with instant results
- 🖼️ Visual thumbnail grid sorted by quality score
- 📊 See all metadata (license, author, dimensions, score)
- 👤 Toggle face detection on/off
- 📥 Direct download and view links
- 📱 Responsive design (works on mobile)

![Web GUI Screenshot](https://via.placeholder.com/800x400.png?text=OpenImage+Web+GUI)

### Command-Line Interface

For programmatic use or automation, use the CLI:

#### Basic Usage

Search for a person with face detection:
```bash
python3 main.py "Albert Einstein"
```

### Command-Line Options

```bash
python3 main.py [query] [options]

Arguments:
  query                 Search query (e.g., person name, entity)

Options:
  --entity-type TYPE    Type of entity: person, place, thing, other (default: person)
  --max-results N       Maximum number of results (default: 20)
  --no-face-filter      Disable face detection for person entities
  --output FILE         Save results to JSON file
  --status              Show status of available sources
```

### Examples

Search for a person with face detection:
```bash
python3 main.py "Marie Curie" --max-results 5
```

Search without face filtering:
```bash
python3 main.py "Eiffel Tower" --entity-type place --no-face-filter
```

Save results to a file:
```bash
python3 main.py "Leonardo da Vinci" --output results.json
```

Check system status:
```bash
python3 main.py --status test
```

## Output Format

The tool returns JSON with the following structure:

```json
{
  "query": "Albert Einstein",
  "entity_type": "person",
  "total_results": 5,
  "face_filter_applied": true,
  "images": [
    {
      "image_url": "https://...",
      "thumbnail_url": "https://...",
      "source": "Wikimedia Commons",
      "license_type": "Public Domain",
      "license_url": "https://...",
      "title": "Image title",
      "description": "Image description",
      "author": "Author name",
      "width": 2523,
      "height": 3313,
      "quality_score": 3.1,
      "has_face": true,
      "page_url": "https://...",
      "download_url": "https://..."
    }
  ]
}
```

## Supported Licenses

All returned images have one of these commercial-safe licenses:

- **Public Domain**: No restrictions
- **CC0 (Creative Commons Zero)**: No restrictions
- **CC BY (Attribution)**: Requires attribution
- **CC BY-SA (Attribution-ShareAlike)**: Requires attribution and same license
- **Unsplash License**: Free for commercial use
- **Pexels License**: Free for commercial use
- **Pixabay License**: Free for commercial use

## Quality Scoring

Images are scored based on:
- Source reliability (Unsplash: 0.9, Pexels: 0.85, Wikimedia: 0.8, Pixabay: 0.75)
- Image resolution (bonus for HD and higher)
- Metadata completeness (title, description, author)
- Face detection (bonus for person entities)
- License permissiveness

Higher scores indicate better quality and relevance.

## Programmatic Usage

You can also use OpenImage as a Python library:

```python
from src.image_finder import LicensedImageFinder

finder = LicensedImageFinder()

# Find images
results = finder.find_images(
    query="Albert Einstein",
    entity_type="person",
    max_results=10,
    require_face=True
)

# Check status
status = finder.get_status()
print(f"Available sources: {status['available_sources']}")

# Process results
for image in results:
    print(f"{image['title']}: {image['license_type']}")
```

## Testing

Run the comprehensive test suite:

```bash
# Run all tests
python3 -m pytest tests/ -v

# Run specific test file
python3 -m pytest tests/test_image_finder.py -v

# Run with coverage
python3 -m pytest tests/ --cov=src --cov-report=html
```

All 19 tests cover:
- Data models and license verification
- All image source integrations
- Face detection functionality
- Quality scoring algorithm
- End-to-end image search

## Project Structure

```
openimage/
├── src/
│   ├── __init__.py
│   ├── config.py              # Configuration and settings
│   ├── models.py              # Data models (ImageResult, LicenseType)
│   ├── image_finder.py        # Main finder class with caching
│   ├── face_detector.py       # Face detection using OpenCV
│   ├── cache.py               # SQLite caching system
│   └── sources/
│       ├── __init__.py
│       ├── base.py            # Base source class
│       ├── wikimedia.py       # Wikimedia Commons integration
│       ├── unsplash.py        # Unsplash integration
│       ├── pexels.py          # Pexels integration
│       └── pixabay.py         # Pixabay integration
├── tests/
│   ├── test_models.py
│   ├── test_sources.py
│   ├── test_image_finder.py
│   └── test_face_detector.py
├── templates/
│   └── index.html             # Web GUI template
├── static/
│   └── css/
│       └── style.css          # Web GUI styles
├── data/
│   └── image_cache.db         # SQLite cache database (auto-created)
├── main.py                    # CLI entry point
├── web_gui.py                 # Web GUI entry point
├── cache_manager.py           # Cache management utility
├── requirements.txt
├── .env.example
└── README.md
```

## Configuration

Edit `src/config.py` to customize:

- `MAX_RESULTS_PER_SOURCE`: Max results from each source (default: 10)
- `REQUEST_TIMEOUT`: HTTP request timeout in seconds (default: 10)
- `MIN_IMAGE_WIDTH`: Minimum image width (default: 800)
- `MIN_IMAGE_HEIGHT`: Minimum image height (default: 600)
- `ENABLE_FACE_DETECTION`: Enable/disable face detection (default: True)

## Caching System

OpenImage automatically caches all API responses in a local SQLite database to:
- **Avoid rate limits**: Never repeat the same API request
- **Improve speed**: Cached results return instantly
- **Save bandwidth**: Reduce unnecessary API calls

### Cache Features

- **30-day TTL**: Cache entries expire after 30 days by default
- **Per-source caching**: Each image source is cached separately
- **Query-specific**: Cache keys based on query + entity type + source
- **Hit tracking**: Monitors cache usage statistics
- **Auto-cleanup**: Expired entries can be removed

### Cache Management

View cache statistics:
```bash
python3 cache_manager.py stats
```

Search cached queries:
```bash
python3 cache_manager.py search "einstein"
```

Clear expired cache entries:
```bash
python3 cache_manager.py clear --expired
```

Clear all cache entries:
```bash
python3 cache_manager.py clear
```

### Cache Output

When running searches, you'll see cache activity:
```
→ Fetching from Wikimedia Commons: Albert Einstein
✓ Cached 10 results from Wikimedia Commons
```

Second search for the same query:
```
✓ Cache hit for Wikimedia Commons: Albert Einstein
```

### Cache Location

- Database: `data/image_cache.db`
- Automatically created on first search
- Excluded from git (in `.gitignore`)

### Disable Caching

To disable caching programmatically:
```python
from src.image_finder import LicensedImageFinder

finder = LicensedImageFinder(enable_cache=False)
```

## Legal & Licensing

This tool is designed to help you find legally-safe images. However:

- Always verify license requirements before using images commercially
- Some licenses (like CC BY) require attribution
- Check the `license_url` field for full license details
- When in doubt, consult with legal counsel

## Contributing

Contributions welcome! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details

## Author

Built for news aggregation applications requiring high-quality, license-safe images.
