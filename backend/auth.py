import base64
import hashlib
import json
import os
import random
import requests
import string
from typing import Dict, Optional
from backend.logger import setup_logger

logger = setup_logger("spotify_auth")

class SpotifyAuth:
    def __init__(self, client_id: str, redirect_uri: str):
        self.client_id = client_id
        self.redirect_uri = redirect_uri
        self.code_verifier = self._generate_code_verifier()
        self.code_challenge = self._generate_code_challenge()
        
    def _generate_code_verifier(self) -> str:
        """Generate a random code verifier for PKCE"""
        code_verifier = ''.join(random.choice(string.ascii_letters + string.digits) for _ in range(64))
        return code_verifier
        
    def _generate_code_challenge(self) -> str:
        """Generate the code challenge from the code verifier using SHA256"""
        code_challenge = hashlib.sha256(self.code_verifier.encode('utf-8')).digest()
        code_challenge = base64.urlsafe_b64encode(code_challenge).decode('utf-8')
        code_challenge = code_challenge.replace('=', '')
        return code_challenge
    
    def get_auth_url(self) -> str:
        """Generate the Spotify authorization URL"""
        scope = "user-read-private user-read-email user-top-read"
        
        auth_url = "https://accounts.spotify.com/authorize?" + \
                   "client_id=" + self.client_id + \
                   "&response_type=code" + \
                   "&redirect_uri=" + self.redirect_uri + \
                   "&code_challenge_method=S256" + \
                   "&code_challenge=" + self.code_challenge + \
                   "&scope=" + scope
        
        return auth_url
    
    def get_tokens(self, authorization_code: str) -> Dict:
        """Exchange authorization code for access and refresh tokens"""
        token_url = "https://accounts.spotify.com/api/token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "client_id": self.client_id,
            "grant_type": "authorization_code",
            "code": authorization_code,
            "redirect_uri": self.redirect_uri,
            "code_verifier": self.code_verifier
        }
        
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting tokens: {response.status_code}")
            logger.debug(response.text)
            return {"error": "Failed to get tokens"}
    
    def refresh_token(self, refresh_token: str) -> Dict:
        """Refresh the access token using the refresh token"""
        token_url = "https://accounts.spotify.com/api/token"
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        data = {
            "client_id": self.client_id,
            "grant_type": "refresh_token",
            "refresh_token": refresh_token
        }
        
        response = requests.post(token_url, headers=headers, data=data)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error refreshing token: {response.status_code}")
            logger.debug(response.text)
            return {"error": "Failed to refresh token"}
    
    def get_user_profile(self, access_token: str) -> Dict:
        """Get the user's Spotify profile"""
        url = "https://api.spotify.com/v1/me"
        
        headers = {
            "Authorization": f"Bearer {access_token}"
        }
        
        response = requests.get(url, headers=headers)
        
        if response.status_code == 200:
            return response.json()
        else:
            logger.error(f"Error getting user profile: {response.status_code}")
            logger.debug(response.text)
            return {"error": "Failed to get user profile"} 