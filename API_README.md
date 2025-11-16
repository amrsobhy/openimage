# OpenImage API Documentation

REST API for searching openly licensed images with face detection and gender filtering.

## Table of Contents

- [Quick Start](#quick-start)
- [API Endpoints](#api-endpoints)
- [Request & Response Examples](#request--response-examples)
- [Error Handling](#error-handling)
- [Features](#features)

## Quick Start

### Using Docker

```bash
# Build the Docker image
docker build -t openimage-api .

# Run the container
docker run -p 8000:8000 \
  -e ZEUS_LLM_API_KEY=your_key_here \
  -e IGNIRA_API_KEY=your_key_here \
  -e CRAWL_NINJA_API_KEY=your_key_here \
  openimage-api

# Or use docker-compose
docker-compose up
```

### Using Python Directly

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export ZEUS_LLM_API_KEY=your_key_here

# Run the API server
python api_server.py
```

The API will be available at `http://localhost:8000`

## API Endpoints

### 1. Health Check

Check if the API is running.

**Endpoint:** `GET /health`

**Response:**
```json
{
  "status": "healthy",
  "service": "OpenImage API",
  "version": "0.1.0"
}
```

**Example:**
```bash
curl http://localhost:8000/health
```

---

### 2. Get System Status

Get information about configured image sources and API keys.

**Endpoint:** `GET /api/status`

**Response:**
```json
{
  "success": true,
  "data": {
    "face_detection_enabled": true,
    "gender_filtering_enabled": true,
    "sources": {
      "wikimedia": true,
      "unsplash": false,
      "pexels": false,
      "pixabay": false,
      "infogouv": true
    }
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/status
```

---

### 3. Get Available Sources

Get list of available image sources.

**Endpoint:** `GET /api/sources`

**Response:**
```json
{
  "success": true,
  "data": {
    "sources": ["Wikimedia Commons", "Info.gouv.fr"],
    "count": 2
  }
}
```

**Example:**
```bash
curl http://localhost:8000/api/sources
```

---

### 4. Search for Images

Search for openly licensed images with optional face detection and gender filtering.

**Endpoint:** `POST /api/search`

**Request Body:**
```json
{
  "query": "Emmanuel Macron",
  "entity_type": "person",
  "max_results": 20,
  "require_face": true
}
```

**Parameters:**

| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| `query` | string | Yes | - | Search term (person name, place, etc.) |
| `entity_type` | string | No | `"person"` | Type of entity: `"person"`, `"place"`, `"thing"`, `"other"` |
| `max_results` | integer | No | `20` | Maximum results to return (1-100) |
| `require_face` | boolean | No | `true` | For person entities, filter images with faces |

**Response:**
```json
{
  "success": true,
  "data": {
    "query": "Emmanuel Macron",
    "entity_type": "person",
    "total_results": 15,
    "face_filter_applied": true,
    "gender_filter_applied": true,
    "images": [
      {
        "title": "Emmanuel Macron official portrait",
        "description": "Official portrait of French President",
        "image_url": "https://...",
        "thumbnail_url": "https://...",
        "source": "Wikimedia Commons",
        "author": "Government of France",
        "license": "Etalab 2.0 Open License",
        "license_url": "https://...",
        "source_url": "https://...",
        "width": 3000,
        "height": 4000,
        "file_size": null,
        "quality_score": 8.5,
        "has_face": true
      }
    ]
  }
}
```

**Example:**
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Emmanuel Macron",
    "entity_type": "person",
    "max_results": 10
  }'
```

## Request & Response Examples

### Example 1: Search for a Person

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Aurore Bergé",
    "entity_type": "person",
    "max_results": 20,
    "require_face": true
  }'
```

**What happens:**
1. Searches all configured sources (Wikimedia, Info.gouv.fr, WhiteHouse.gov, European Commission, etc.)
2. Uses Zeus LLM to detect gender ("female")
3. Filters images to only include those with detected faces
4. Uses DeepFace to classify gender in each image
5. Filters out images with mismatched gender
6. Returns top 20 results sorted by quality score

### Example 2: Search for a Place

```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Eiffel Tower",
    "entity_type": "place",
    "max_results": 15
  }'
```

**What happens:**
1. Searches all configured sources
2. No face detection or gender filtering (not a person)
3. Returns top 15 results sorted by quality score

### Example 3: Using Python

```python
import requests

# Search for images
response = requests.post('http://localhost:8000/api/search', json={
    'query': 'Le Monde journal',
    'entity_type': 'thing',
    'max_results': 10,
    'require_face': False
})

data = response.json()

if data['success']:
    images = data['data']['images']
    print(f"Found {len(images)} images")

    for img in images:
        print(f"- {img['title']}")
        print(f"  License: {img['license']}")
        print(f"  URL: {img['image_url']}")
        print()
else:
    print(f"Error: {data['error']}")
```

### Example 4: Using JavaScript (Browser)

```javascript
async function searchImages(query) {
  const response = await fetch('http://localhost:8000/api/search', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      query: query,
      entity_type: 'person',
      max_results: 20
    })
  });

  const data = await response.json();

  if (data.success) {
    console.log(`Found ${data.data.total_results} images`);
    return data.data.images;
  } else {
    throw new Error(data.error);
  }
}

// Usage
searchImages('Emmanuel Macron')
  .then(images => {
    images.forEach(img => {
      console.log(`${img.title} - ${img.license}`);
    });
  })
  .catch(err => console.error(err));
```

## Error Handling

All API responses include a `success` field indicating whether the request succeeded.

### Success Response
```json
{
  "success": true,
  "data": { ... }
}
```

### Error Response
```json
{
  "success": false,
  "error": "Error message describing what went wrong"
}
```

### HTTP Status Codes

| Code | Meaning | Description |
|------|---------|-------------|
| 200 | OK | Request successful |
| 400 | Bad Request | Invalid parameters or missing required fields |
| 404 | Not Found | Endpoint does not exist |
| 500 | Internal Server Error | Server error during processing |

### Common Errors

**Missing query parameter:**
```json
{
  "success": false,
  "error": "Missing required field: query"
}
```

**Invalid entity type:**
```json
{
  "success": false,
  "error": "Invalid entity_type. Must be one of: person, place, thing, other"
}
```

**Invalid max_results:**
```json
{
  "success": false,
  "error": "max_results must be between 1 and 100"
}
```

## Features

### 🔍 Multi-Source Search
Searches across multiple image sources:
- **Wikimedia Commons** - Free media repository
- **Info.gouv.fr** - French government images (requires Ignira + Crawl.ninja API keys)
- **WhiteHouse.gov** - US government images (requires Ignira + Crawl.ninja API keys)
- **European Commission** - EU official images under CC BY 4.0 (requires Ignira + Crawl.ninja API keys)
- **Unsplash** - High-quality photos (optional, requires API key)
- **Pexels** - Free stock photos (optional, requires API key)
- **Pixabay** - Free images (optional, requires API key)

### 👤 Face Detection
For person entities, automatically filters images to include only those with detected faces using state-of-the-art face recognition.

### ⚧ Gender Filtering
For person entities, uses AI to:
1. Detect expected gender from query (using Zeus LLM)
2. Classify gender in each image (using DeepFace)
3. Filter out images with mismatched gender

### 📜 License-Safe
All images come with:
- Clear license information
- Author attribution
- License URLs
- Source URLs for verification

### 🎯 Relevance Filtering
Smart filtering ensures results match your query:
- For 2-word queries: requires BOTH words to appear
- For longer queries: requires at least 50% of words to match
- Removes stop words (le, la, the, etc.)

### ⚡ Performance
- Results cached in SQLite database
- Parallel API requests to all sources
- Gender classification results cached
- Face detection results cached

## Environment Variables

Configure the API using environment variables:

```bash
# Required for government sources (Info.gouv.fr, WhiteHouse.gov, European Commission)
IGNIRA_API_KEY=your_ignira_api_key
CRAWL_NINJA_API_KEY=your_crawl_ninja_api_key

# Required for gender filtering
ZEUS_LLM_API_KEY=your_zeus_llm_api_key

# Optional: Additional image sources
UNSPLASH_ACCESS_KEY=your_unsplash_key
PEXELS_API_KEY=your_pexels_key
PIXABAY_API_KEY=your_pixabay_key

# Server configuration
PORT=8000           # API server port (default: 8000)
HOST=0.0.0.0        # API server host (default: 0.0.0.0)
DEBUG=false         # Enable debug mode (default: false)
```

## Docker Deployment

### Build and Run

```bash
# Build the image
docker build -t openimage-api .

# Run with environment variables
docker run -d \
  --name openimage \
  -p 8000:8000 \
  -e ZEUS_LLM_API_KEY=your_key \
  -e IGNIRA_API_KEY=your_key \
  -e CRAWL_NINJA_API_KEY=your_key \
  openimage-api

# View logs
docker logs -f openimage

# Stop the container
docker stop openimage
```

### Using Docker Compose

Create a `.env` file with your API keys:
```
ZEUS_LLM_API_KEY=your_key_here
IGNIRA_API_KEY=your_key_here
CRAWL_NINJA_API_KEY=your_key_here
```

Then run:
```bash
docker-compose up -d
```

## Testing

### Test Health Endpoint
```bash
curl http://localhost:8000/health
```

Expected: `{"status": "healthy", ...}`

### Test Status Endpoint
```bash
curl http://localhost:8000/api/status
```

Expected: List of configured sources

### Test Search Endpoint
```bash
curl -X POST http://localhost:8000/api/search \
  -H "Content-Type: application/json" \
  -d '{"query": "test", "entity_type": "thing", "max_results": 5}'
```

Expected: Search results with images

## Support

For issues, questions, or contributions, please visit the project repository.
