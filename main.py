from fastapi import FastAPI, HTTPException, Query, Response
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import os
import aiofiles
from youtube_service import YouTubeService
from playlist_service import PlaylistService
import asyncio
import tempfile

app = FastAPI(
    title="YouTube Music Player API",
    description="A FastAPI service to search YouTube and stream music as MP3",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize services
youtube_service = YouTubeService()
playlist_service = PlaylistService()

class SearchResponse(BaseModel):
    id: str
    title: str
    channel: str
    duration: str
    views: str
    thumbnail: Optional[str]
    url: str

class AudioStreamResponse(BaseModel):
    title: str
    duration: int
    audio_url: str
    video_id: str

class PlaylistCreateRequest(BaseModel):
    name: str
    description: Optional[str] = ""

class PlaylistUpdateRequest(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

class AddSongRequest(BaseModel):
    id: str
    title: str
    channel: str
    duration: str
    thumbnail: Optional[str]
    url: str

class PlaylistResponse(BaseModel):
    id: str
    name: str
    description: str
    created_at: str
    updated_at: str
    songs: List[dict]
    total_duration: int

@app.get("/")
async def root():
    """Root endpoint with API information"""
    return {
        "message": "YouTube Music Player API",
        "version": "1.0.0",
        "endpoints": {
            "/search": "Search for YouTube videos",
            "/stream/{video_id}": "Get audio stream URL for a video",
            "/play/{video_id}": "Stream MP3 audio directly",
            "/download/{video_id}": "Download MP3 file",
            "/playlists": "Playlist management endpoints",
            "/playlists/create": "Create a new playlist",
            "/playlists/{playlist_id}": "Get, update, or delete a playlist",
            "/playlists/{playlist_id}/songs": "Add or remove songs from playlist"
        }
    }

@app.get("/search", response_model=List[SearchResponse])
async def search_youtube(
    q: str = Query(..., description="Search query"),
    limit: int = Query(10, ge=1, le=50, description="Number of results to return")
):
    """Search for YouTube videos"""
    try:
        results = await youtube_service.search_videos(q, limit)
        return results
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/stream/{video_id}", response_model=AudioStreamResponse)
async def get_audio_stream(video_id: str):
    """Get direct audio stream URL for a YouTube video"""
    try:
        stream_info = await youtube_service.get_audio_stream_url(video_id)
        return stream_info
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/play/{video_id}")
async def play_audio(video_id: str):
    """Stream MP3 audio directly"""
    try:
        # Get the audio stream URL
        stream_info = await youtube_service.get_audio_stream_url(video_id)
        audio_url = stream_info['audio_url']
        
        # Create a streaming response that proxies the audio
        async def generate():
            import httpx
            timeout = httpx.Timeout(30.0, connect=10.0)
            async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
                try:
                    async with client.stream('GET', audio_url, headers={
                        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                    }) as response:
                        if response.status_code == 200:
                            async for chunk in response.aiter_bytes(chunk_size=8192):
                                if chunk:
                                    yield chunk
                        else:
                            raise Exception(f"HTTP {response.status_code}")
                except Exception as e:
                    print(f"Streaming error: {e}")
                    raise
        
        return StreamingResponse(
            generate(),
            media_type="audio/mpeg",
            headers={
                "Content-Disposition": f"inline; filename=\"{stream_info['title']}.mp3\"",
                "Accept-Ranges": "bytes",
                "Access-Control-Allow-Origin": "*",
                "Access-Control-Allow-Methods": "GET",
                "Access-Control-Allow-Headers": "*",
                "Cache-Control": "no-cache"
            }
        )
    except Exception as e:
        print(f"Play audio error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/download/{video_id}")
async def download_audio(video_id: str):
    """Download MP3 file"""
    try:
        file_path = await youtube_service.download_audio(video_id)
        
        # Get file info for proper headers
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        return FileResponse(
            path=file_path,
            filename=filename,
            media_type="audio/mpeg",
            headers={
                "Content-Length": str(file_size),
                "Accept-Ranges": "bytes"
            }
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/info/{video_id}")
async def get_video_info(video_id: str):
    """Get detailed information about a YouTube video"""
    try:
        info = await youtube_service.get_audio_stream_url(video_id)
        return {
            "video_id": video_id,
            "title": info['title'],
            "duration": info['duration'],
            "has_audio": True,
            "url": f"https://www.youtube.com/watch?v={video_id}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Playlist endpoints
@app.get("/playlists")
async def get_all_playlists():
    """Get all playlists"""
    try:
        playlists = playlist_service.get_all_playlists()
        return playlists
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/playlists/create")
async def create_playlist(request: PlaylistCreateRequest):
    """Create a new playlist"""
    try:
        playlist = playlist_service.create_playlist(request.name, request.description)
        return playlist
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlists/{playlist_id}")
async def get_playlist(playlist_id: str):
    """Get a specific playlist"""
    try:
        playlist = playlist_service.get_playlist(playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return playlist
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/playlists/{playlist_id}")
async def update_playlist(playlist_id: str, request: PlaylistUpdateRequest):
    """Update a playlist"""
    try:
        playlist = playlist_service.update_playlist(playlist_id, request.name, request.description)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return playlist
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/playlists/{playlist_id}")
async def delete_playlist(playlist_id: str):
    """Delete a playlist"""
    try:
        success = playlist_service.delete_playlist(playlist_id)
        if not success:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return {"message": "Playlist deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/playlists/{playlist_id}/songs")
async def add_song_to_playlist(playlist_id: str, song: AddSongRequest):
    """Add a song to a playlist"""
    try:
        song_dict = song.dict()
        playlist = playlist_service.add_song_to_playlist(playlist_id, song_dict)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return playlist
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/playlists/{playlist_id}/songs/{song_id}")
async def remove_song_from_playlist(playlist_id: str, song_id: str):
    """Remove a song from a playlist"""
    try:
        playlist = playlist_service.remove_song_from_playlist(playlist_id, song_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        return playlist
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlists/search/{query}")
async def search_playlists(query: str):
    """Search playlists by name or description"""
    try:
        playlists = playlist_service.search_playlists(query)
        return playlists
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlists/stats/overview")
async def get_playlist_stats():
    """Get playlist statistics"""
    try:
        stats = playlist_service.get_playlist_stats()
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlists/recent/{limit}")
async def get_recent_playlists(limit: int = 5):
    """Get recently updated playlists"""
    try:
        playlists = playlist_service.get_recent_playlists(limit)
        return playlists
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/playlists/{playlist_id}/reorder")
async def reorder_playlist(playlist_id: str, song_indices: List[int]):
    """Reorder songs in a playlist"""
    try:
        playlist = playlist_service.reorder_playlist(playlist_id, song_indices)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found or invalid indices")
        return playlist
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/playlists/{playlist_id}/play")
async def play_playlist(playlist_id: str, shuffle: bool = False):
    """Get playlist in play order (optionally shuffled)"""
    try:
        playlist = playlist_service.get_playlist(playlist_id)
        if not playlist:
            raise HTTPException(status_code=404, detail="Playlist not found")
        
        songs = playlist["songs"].copy()
        if shuffle:
            import random
            random.shuffle(songs)
        
        return {
            "playlist_id": playlist_id,
            "playlist_name": playlist["name"],
            "songs": songs,
            "total_songs": len(songs),
            "shuffled": shuffle
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Cleanup on shutdown
@app.on_event("shutdown")
async def shutdown_event():
    youtube_service.cleanup_temp_files()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 