import json
import os
from typing import List, Dict, Optional
from datetime import datetime
import uuid

class PlaylistService:
    def __init__(self):
        self.playlists_file = "playlists.json"
        self.playlists = self.load_playlists()
    
    def load_playlists(self) -> Dict:
        """Load playlists from JSON file"""
        try:
            if os.path.exists(self.playlists_file):
                with open(self.playlists_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return {}
        except Exception as e:
            print(f"Error loading playlists: {e}")
            return {}
    
    def save_playlists(self):
        """Save playlists to JSON file"""
        try:
            with open(self.playlists_file, 'w', encoding='utf-8') as f:
                json.dump(self.playlists, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving playlists: {e}")
    
    def create_playlist(self, name: str, description: str = "") -> Dict:
        """Create a new playlist"""
        playlist_id = str(uuid.uuid4())
        playlist = {
            "id": playlist_id,
            "name": name,
            "description": description,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat(),
            "songs": [],
            "total_duration": 0
        }
        
        self.playlists[playlist_id] = playlist
        self.save_playlists()
        return playlist
    
    def get_playlist(self, playlist_id: str) -> Optional[Dict]:
        """Get a specific playlist"""
        return self.playlists.get(playlist_id)
    
    def get_all_playlists(self) -> List[Dict]:
        """Get all playlists"""
        return list(self.playlists.values())
    
    def update_playlist(self, playlist_id: str, name: str = None, description: str = None) -> Optional[Dict]:
        """Update playlist metadata"""
        if playlist_id not in self.playlists:
            return None
        
        playlist = self.playlists[playlist_id]
        if name is not None:
            playlist["name"] = name
        if description is not None:
            playlist["description"] = description
        playlist["updated_at"] = datetime.now().isoformat()
        
        self.save_playlists()
        return playlist
    
    def delete_playlist(self, playlist_id: str) -> bool:
        """Delete a playlist"""
        if playlist_id in self.playlists:
            del self.playlists[playlist_id]
            self.save_playlists()
            return True
        return False
    
    def add_song_to_playlist(self, playlist_id: str, song: Dict) -> Optional[Dict]:
        """Add a song to a playlist"""
        if playlist_id not in self.playlists:
            return None
        
        playlist = self.playlists[playlist_id]
        
        # Check if song already exists in playlist
        for existing_song in playlist["songs"]:
            if existing_song["id"] == song["id"]:
                return playlist  # Song already exists
        
        # Add song with additional metadata
        song_data = {
            "id": song["id"],
            "title": song["title"],
            "channel": song["channel"],
            "duration": song["duration"],
            "thumbnail": song["thumbnail"],
            "url": song["url"],
            "added_at": datetime.now().isoformat()
        }
        
        playlist["songs"].append(song_data)
        playlist["updated_at"] = datetime.now().isoformat()
        
        # Update total duration (convert duration string to seconds for calculation)
        try:
            duration_parts = song["duration"].split(":")
            if len(duration_parts) == 2:
                minutes, seconds = map(int, duration_parts)
                duration_seconds = minutes * 60 + seconds
                playlist["total_duration"] += duration_seconds
        except:
            pass  # If duration parsing fails, skip duration update
        
        self.save_playlists()
        return playlist
    
    def remove_song_from_playlist(self, playlist_id: str, song_id: str) -> Optional[Dict]:
        """Remove a song from a playlist"""
        if playlist_id not in self.playlists:
            return None
        
        playlist = self.playlists[playlist_id]
        
        # Find and remove the song
        for i, song in enumerate(playlist["songs"]):
            if song["id"] == song_id:
                removed_song = playlist["songs"].pop(i)
                playlist["updated_at"] = datetime.now().isoformat()
                
                # Update total duration
                try:
                    duration_parts = removed_song["duration"].split(":")
                    if len(duration_parts) == 2:
                        minutes, seconds = map(int, duration_parts)
                        duration_seconds = minutes * 60 + seconds
                        playlist["total_duration"] = max(0, playlist["total_duration"] - duration_seconds)
                except:
                    pass
                
                self.save_playlists()
                return playlist
        
        return playlist  # Song not found, but return playlist anyway
    
    def reorder_playlist(self, playlist_id: str, song_indices: List[int]) -> Optional[Dict]:
        """Reorder songs in a playlist"""
        if playlist_id not in self.playlists:
            return None
        
        playlist = self.playlists[playlist_id]
        songs = playlist["songs"]
        
        if len(song_indices) != len(songs):
            return None  # Invalid indices
        
        try:
            # Reorder songs based on provided indices
            reordered_songs = [songs[i] for i in song_indices]
            playlist["songs"] = reordered_songs
            playlist["updated_at"] = datetime.now().isoformat()
            
            self.save_playlists()
            return playlist
        except (IndexError, ValueError):
            return None  # Invalid indices
    
    def get_playlist_stats(self) -> Dict:
        """Get statistics about all playlists"""
        total_playlists = len(self.playlists)
        total_songs = sum(len(playlist["songs"]) for playlist in self.playlists.values())
        total_duration = sum(playlist.get("total_duration", 0) for playlist in self.playlists.values())
        
        # Convert total duration to readable format
        hours = total_duration // 3600
        minutes = (total_duration % 3600) // 60
        seconds = total_duration % 60
        
        duration_str = f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        
        return {
            "total_playlists": total_playlists,
            "total_songs": total_songs,
            "total_duration_seconds": total_duration,
            "total_duration_formatted": duration_str
        }
    
    def search_playlists(self, query: str) -> List[Dict]:
        """Search playlists by name or description"""
        query = query.lower()
        results = []
        
        for playlist in self.playlists.values():
            if (query in playlist["name"].lower() or 
                query in playlist.get("description", "").lower()):
                results.append(playlist)
        
        return results
    
    def get_recent_playlists(self, limit: int = 5) -> List[Dict]:
        """Get recently updated playlists"""
        all_playlists = list(self.playlists.values())
        # Sort by updated_at in descending order
        all_playlists.sort(key=lambda x: x.get("updated_at", ""), reverse=True)
        return all_playlists[:limit] 