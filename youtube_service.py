import os
import tempfile
import asyncio
from typing import List, Dict, Optional
import yt_dlp
import httpx
from pathlib import Path
import json
import re

class YouTubeService:
    def __init__(self):
        self.temp_dir = tempfile.mkdtemp()
        
    async def search_videos(self, query: str, limit: int = 10) -> List[Dict]:
        """Search for videos on YouTube using yt-dlp"""
        try:
            loop = asyncio.get_event_loop()
            
            def perform_search():
                # Create search query for yt-dlp
                search_query = f"ytsearch{limit}:{query}"
                
                ydl_opts = {
                    'quiet': True,
                    'no_warnings': True,
                    'extract_flat': True,
                    'skip_download': True,
                }
                
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    try:
                        # Extract info for search results
                        search_results = ydl.extract_info(search_query, download=False)
                        return search_results
                    except Exception as e:
                        print(f"Search error: {e}")
                        return None
            
            results = await loop.run_in_executor(None, perform_search)
            
            formatted_results = []
            if results and 'entries' in results:
                for video in results['entries']:
                    if video and video.get('id'):
                        # Format duration
                        duration = video.get('duration')
                        if duration and isinstance(duration, (int, float)):
                            minutes = int(duration) // 60
                            seconds = int(duration) % 60
                            duration_str = f"{minutes}:{seconds:02d}"
                        else:
                            duration_str = "Live" if video.get('is_live') else "N/A"
                        
                        # Format view count
                        view_count = video.get('view_count')
                        if view_count and isinstance(view_count, (int, float)):
                            if view_count >= 1000000:
                                views_str = f"{view_count/1000000:.1f}M views"
                            elif view_count >= 1000:
                                views_str = f"{view_count/1000:.1f}K views"
                            else:
                                views_str = f"{int(view_count)} views"
                        else:
                            views_str = "N/A"
                        
                        # Get thumbnail URL
                        thumbnail_url = None
                        if video.get('thumbnails'):
                            # Get the best quality thumbnail
                            thumbnails = video['thumbnails']
                            if thumbnails:
                                thumbnail_url = thumbnails[-1].get('url')  # Last one is usually highest quality
                        
                        if not thumbnail_url:
                            # Fallback to YouTube's default thumbnail format
                            thumbnail_url = f"https://img.youtube.com/vi/{video['id']}/maxresdefault.jpg"
                        
                        formatted_results.append({
                            'id': video['id'],
                            'title': video.get('title', 'Unknown Title'),
                            'channel': video.get('uploader', video.get('channel', 'Unknown Channel')),
                            'duration': duration_str,
                            'views': views_str,
                            'thumbnail': thumbnail_url,
                            'url': f"https://www.youtube.com/watch?v={video['id']}"
                        })
            
            return formatted_results[:limit]  # Ensure we don't exceed the limit
            
        except Exception as e:
            raise Exception(f"Error searching videos: {str(e)}")
    
    async def get_audio_stream_url(self, video_id: str) -> Dict:
        """Get direct audio stream URL for a YouTube video"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            
            ydl_opts = {
                'format': 'bestaudio[ext=m4a]/bestaudio[ext=webm]/bestaudio/best',
                'noplaylist': True,
                'quiet': True,
                'no_warnings': True,
                'extractaudio': True,
                'audioformat': 'mp3',
                'audioquality': '192',
            }
            
            loop = asyncio.get_event_loop()
            
            def extract_info():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    return ydl.extract_info(url, download=False)
            
            info = await loop.run_in_executor(None, extract_info)
            
            # Find the best audio format
            audio_url = None
            title = info.get('title', 'Unknown')
            duration = info.get('duration', 0)
            
            # Try to get the direct URL
            if 'url' in info:
                audio_url = info['url']
            elif 'formats' in info:
                # Look for audio-only formats first
                audio_formats = [f for f in info['formats'] 
                               if f.get('acodec') != 'none' and f.get('vcodec') == 'none']
                
                if audio_formats:
                    # Sort by quality and get the best one
                    best_audio = max(audio_formats, 
                                   key=lambda x: x.get('abr', 0) or x.get('tbr', 0) or 0)
                    audio_url = best_audio.get('url')
                else:
                    # Fallback to any format with audio
                    for fmt in info['formats']:
                        if fmt.get('acodec') != 'none' and fmt.get('url'):
                            audio_url = fmt.get('url')
                            break
            
            if not audio_url:
                raise Exception("No audio stream found")
            
            return {
                'title': title,
                'duration': duration,
                'audio_url': audio_url,
                'video_id': video_id
            }
            
        except Exception as e:
            raise Exception(f"Error getting audio stream: {str(e)}")
    
    async def download_audio(self, video_id: str) -> str:
        """Download audio as MP3 file and return file path"""
        try:
            url = f"https://www.youtube.com/watch?v={video_id}"
            output_path = os.path.join(self.temp_dir, f"{video_id}.%(ext)s")
            
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': output_path,
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': True,
                'no_warnings': True,
            }
            
            loop = asyncio.get_event_loop()
            
            def download():
                with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                    ydl.download([url])
            
            await loop.run_in_executor(None, download)
            
            # Find the downloaded file
            mp3_file = os.path.join(self.temp_dir, f"{video_id}.mp3")
            if os.path.exists(mp3_file):
                return mp3_file
            else:
                # Sometimes the file might have a different name
                for file in os.listdir(self.temp_dir):
                    if file.startswith(video_id) and file.endswith('.mp3'):
                        return os.path.join(self.temp_dir, file)
                
                raise Exception("Downloaded file not found")
                
        except Exception as e:
            raise Exception(f"Error downloading audio: {str(e)}")
    
    def cleanup_temp_files(self):
        """Clean up temporary files"""
        try:
            import shutil
            if os.path.exists(self.temp_dir):
                shutil.rmtree(self.temp_dir)
        except Exception:
            pass 