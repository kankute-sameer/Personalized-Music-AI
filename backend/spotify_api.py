import requests
from typing import Dict, List, Optional, Any
import json
from backend.logger import setup_logger
logger = setup_logger("spotify_api")

class SpotifyAPI:
    def __init__(self, auth_manager):
        self.auth_manager = auth_manager
        self.base_url = "https://api.spotify.com/v1"
    
    def _get_headers(self, access_token: str) -> Dict[str, str]:
        """Generate headers with authorization for Spotify API requests"""
        return {
            "Authorization": f"Bearer {access_token}",
            "Content-Type": "application/json"
        }
    
    def get_user_top_items(self, access_token: str, item_type: str, limit: int = 10, 
                           time_range: str = "medium_term") -> Dict[str, Any]:
        """
        Get user's top artists or tracks
        item_type: 'artists' or 'tracks'
        time_range: 'short_term' (4 weeks), 'medium_term' (6 months), 'long_term' (years)
        """
        endpoint = f"{self.base_url}/me/top/{item_type}"
        headers = self._get_headers(access_token)
        params = {
            "limit": limit,
            "time_range": time_range
        }
        
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting top {item_type}: {response.status_code}")
            logger.debug(response.text)
            return {"items": []}
    
    def search(self, access_token: str, query: str, types: List[str] = ["track"], 
               limit: int = 5, market: Optional[str] = None) -> Dict[str, Any]:
        """
        Search for tracks, artists, albums, etc.
        types: List of item types to search across ('track', 'artist', 'album', 'playlist')
        """
        endpoint = f"{self.base_url}/search"
        headers = self._get_headers(access_token)
        
        # Join types with commas
        type_param = ",".join(types)
        
        params = {
            "q": query,
            "type": type_param,
            "limit": limit
        }
        
        if market:
            params["market"] = market
            
        response = requests.get(endpoint, headers=headers, params=params)
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error searching Spotify: {response.status_code}")
            logger.debug(response.text)
            return {}
    
    def create_recommendation_query(self, mood: str, top_artists: List[Dict], 
                                  top_tracks: List[Dict]) -> str:
        """
        Create a search query based on user's mood and top artists/tracks
        """
        # Validate mood - only use if it's a recognized mood word
        valid_moods = [
            "happy", "sad", "energetic", "relaxed", "calm", "excited", 
            "peaceful", "angry", "romantic", "melancholy", "upbeat", "chill"
        ]
        
        # Default to neutral if not recognized
        if mood.lower() not in valid_moods:
            mood = "chill"
        
        # Extract artist names and track names
        artist_names = [artist.get("name", "") for artist in top_artists[:3]]
        
        # Build the query with mood and artists
        query_parts = [mood]
        
        if artist_names:
            # Add top artist to query
            top_artist = f"artist:{artist_names[1]}"
            query_parts.append(top_artist)
        
        # Join all parts with spaces
        query = " ".join(query_parts)
        return query 