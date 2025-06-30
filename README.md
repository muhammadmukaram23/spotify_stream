# YouTube Music Player API

A FastAPI-based service that allows you to search YouTube and stream music as MP3. This API provides endpoints to search for videos, get audio streams, and play music directly.

## Features

- 🔍 Search YouTube videos
- 🎵 Stream audio as MP3
- ⬇️ Download MP3 files
- 🚀 Fast and lightweight API
- 📱 CORS enabled for web applications

## Installation

1. **Clone or create the project directory:**
   ```bash
   mkdir youtube-music-api
   cd youtube-music-api
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install FFmpeg (required for audio conversion):**
   
   **Windows:**
   - Download FFmpeg from https://ffmpeg.org/download.html
   - Add FFmpeg to your system PATH
   
   **macOS:**
   ```bash
   brew install ffmpeg
   ```
   
   **Linux (Ubuntu/Debian):**
   ```bash
   sudo apt update
   sudo apt install ffmpeg
   ```

## Usage

1. **Start the API server:**
   ```bash
   python main.py
   ```
   
   Or using uvicorn directly:
   ```bash
   uvicorn main:app --host 0.0.0.0 --port 8000 --reload
   ```

2. **Access the API:**
   - API will be available at: `http://localhost:8000`
   - Interactive documentation: `http://localhost:8000/docs`
   - Alternative docs: `http://localhost:8000/redoc`

## API Endpoints

### 1. Search Videos
```http
GET /search?q={query}&limit={limit}
```

**Parameters:**
- `q` (required): Search query
- `limit` (optional): Number of results (1-50, default: 10)

**Example:**
```bash
curl "http://localhost:8000/search?q=imagine%20dragons&limit=5"
```

**Response:**
```json
[
  {
    "id": "ktvTqknDobU",
    "title": "Imagine Dragons - Radioactive",
    "channel": "ImagineDragonsVEVO",
    "duration": "3:07",
    "views": "1.2B views",
    "thumbnail": "https://...",
    "url": "https://www.youtube.com/watch?v=ktvTqknDobU"
  }
]
```

### 2. Get Audio Stream URL
```http
GET /stream/{video_id}
```

**Example:**
```bash
curl "http://localhost:8000/stream/ktvTqknDobU"
```

**Response:**
```json
{
  "title": "Imagine Dragons - Radioactive",
  "duration": 187,
  "audio_url": "https://...",
  "video_id": "ktvTqknDobU"
}
```

### 3. Play Audio (Stream MP3)
```http
GET /play/{video_id}
```

**Example:**
```bash
curl "http://localhost:8000/play/ktvTqknDobU" --output song.mp3
```

This endpoint streams the audio directly as MP3. You can:
- Play it directly in a browser
- Use it as a source for HTML audio elements
- Download it using curl/wget

### 4. Download MP3 File
```http
GET /download/{video_id}
```

**Example:**
```bash
curl "http://localhost:8000/download/ktvTqknDobU" --output song.mp3
```

### 5. Get Video Information
```http
GET /info/{video_id}
```

**Example:**
```bash
curl "http://localhost:8000/info/ktvTqknDobU"
```

## Usage Examples

### Python Client Example
```python
import requests
import json

# Search for videos
response = requests.get("http://localhost:8000/search", params={"q": "bohemian rhapsody", "limit": 5})
videos = response.json()

# Get the first video
video_id = videos[0]["id"]
print(f"Playing: {videos[0]['title']}")

# Stream the audio
audio_response = requests.get(f"http://localhost:8000/play/{video_id}", stream=True)
with open("song.mp3", "wb") as f:
    for chunk in audio_response.iter_content(chunk_size=8192):
        f.write(chunk)
```

### JavaScript/Web Example
```javascript
// Search for videos
async function searchVideos(query) {
    const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}`);
    return await response.json();
}

// Play audio in browser
function playAudio(videoId) {
    const audio = new Audio(`http://localhost:8000/play/${videoId}`);
    audio.play();
}

// Usage
searchVideos("your favorite song").then(videos => {
    if (videos.length > 0) {
        playAudio(videos[0].id);
    }
});
```

### HTML Audio Player Example
```html
<!DOCTYPE html>
<html>
<head>
    <title>YouTube Music Player</title>
</head>
<body>
    <input type="text" id="searchInput" placeholder="Search for music...">
    <button onclick="search()">Search</button>
    
    <div id="results"></div>
    
    <audio id="audioPlayer" controls style="width: 100%; margin-top: 20px;">
        Your browser does not support the audio element.
    </audio>

    <script>
        async function search() {
            const query = document.getElementById('searchInput').value;
            const response = await fetch(`http://localhost:8000/search?q=${encodeURIComponent(query)}`);
            const videos = await response.json();
            
            const resultsDiv = document.getElementById('results');
            resultsDiv.innerHTML = '';
            
            videos.forEach(video => {
                const div = document.createElement('div');
                div.innerHTML = `
                    <h3>${video.title}</h3>
                    <p>${video.channel} - ${video.duration}</p>
                    <button onclick="playVideo('${video.id}')">Play</button>
                `;
                resultsDiv.appendChild(div);
            });
        }
        
        function playVideo(videoId) {
            const audioPlayer = document.getElementById('audioPlayer');
            audioPlayer.src = `http://localhost:8000/play/${videoId}`;
            audioPlayer.load();
            audioPlayer.play();
        }
    </script>
</body>
</html>
```

## Dependencies

- **FastAPI**: Web framework
- **yt-dlp**: YouTube video/audio downloader
- **youtube-search-python**: YouTube search functionality
- **uvicorn**: ASGI server
- **aiofiles**: Async file operations
- **httpx**: HTTP client for streaming

## Notes

- The API uses temporary files for downloaded content
- Files are automatically cleaned up on server shutdown
- FFmpeg is required for audio format conversion
- Some videos might not be available due to regional restrictions or copyright
- The API respects YouTube's terms of service

## Error Handling

The API returns appropriate HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `500`: Internal Server Error (download/conversion failed)

Error responses include a detailed message:
```json
{
  "detail": "Error message describing what went wrong"
}
```

## Legal Notice

This tool is for educational and personal use only. Please respect YouTube's Terms of Service and copyright laws. The developers are not responsible for any misuse of this software. 