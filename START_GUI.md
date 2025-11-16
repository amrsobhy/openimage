# Quick Start Guide - Web GUI

## Starting the Web GUI

1. Make sure dependencies are installed:
```bash
pip install -r requirements.txt
```

2. Start the web server:
```bash
python3 web_gui.py
```

3. Open your browser and navigate to:
```
http://localhost:5000
```

## Using the Web Interface

### Search for Images

1. **Enter your search query** (e.g., "Albert Einstein", "Eiffel Tower")
2. **Select entity type**:
   - Person (enables face detection)
   - Place
   - Thing
   - Other
3. **Set max results** (1-100)
4. **Toggle face detection** (for person entities only)
5. **Click "Search Images"**

### Understanding Results

Each image card shows:

- **#Rank**: Position sorted by quality score
- **⭐ Score**: Quality score (0-5, higher is better)
- **👤 Badge**: Face detected (for person entities)
- **Thumbnail**: Visual preview
- **Title**: Image title or description
- **Source**: Where the image came from (Wikimedia, Unsplash, etc.)
- **License**: License type (all commercial-safe)
- **Author**: Image creator
- **Size**: Image dimensions in pixels

### Actions

- **View Full**: Opens full-resolution image in new tab
- **Details**: Opens source page with complete information
- **Download**: Direct download link (when available)

## Quality Score Breakdown

Images are scored based on:
- **Source reliability**: Unsplash (0.9), Pexels (0.85), Wikimedia (0.8), Pixabay (0.75)
- **Image resolution**: Bonus for HD (800x600+) and Full HD (1920x1080+)
- **Metadata completeness**: Title, description, author information
- **Face detection**: Bonus 0.5 for person entities with detected faces
- **License permissiveness**: Public Domain (1.0), CC0 (1.0), others (0.85-0.95)

Maximum score: 5.0

## Tips for Best Results

1. **For people**: Enable face detection to ensure images show actual faces
2. **For places/things**: Disable face detection for better results
3. **Increase max results**: Get more options to choose from (up to 100)
4. **Check licenses**: All are commercial-safe, but some require attribution
5. **Use specific queries**: "Leonardo da Vinci portrait" vs just "Leonardo"

## API Keys (Optional)

For more sources, add API keys to `.env`:

```bash
cp .env.example .env
# Edit .env and add your keys
```

Then restart the web server to enable Unsplash, Pexels, and Pixabay.

## Troubleshooting

**Port already in use:**
```bash
# Kill existing process
pkill -f web_gui.py
# Or use a different port
python3 web_gui.py --port 8000
```

**No images found:**
- Try broader search terms
- Disable face detection
- Check if Wikimedia Commons is accessible

**Images not loading:**
- Check internet connection
- Some sources may have rate limits
- Try refreshing the page

## Stopping the Server

Press `Ctrl+C` in the terminal where the server is running.
