from fastapi import FastAPI, Request, Response, Depends, HTTPException, status, Form
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.security import OAuth2PasswordBearer
from starlette.middleware.sessions import SessionMiddleware
import uvicorn
import json
from pydantic import BaseModel
from typing import Optional, Dict, List, Any
import os
from fastapi.middleware.cors import CORSMiddleware
import asyncio
import requests

from backend.llm_manager import LLMManager
from backend.spotify_api import SpotifyAPI
from backend.auth import SpotifyAuth
from backend.conversation_store import ConversationStore
from backend.logger import setup_logger

# Initialize FastAPI app
app = FastAPI()
app.add_middleware(
    SessionMiddleware, 
    secret_key=os.urandom(24),
    max_age=3600,  # 1 hour session
    same_site="lax",  # Allow cross-site requests for OAuth
    https_only=False  # Set to True in production
)

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Set up templates
templates = Jinja2Templates(directory="templates")

# Initialize Spotify authentication
CLIENT_ID = os.getenv("SPOTIFY_CLIENT_ID", "5c2bfce5570a46c394675a810b5cb895")
REDIRECT_URI = os.getenv("SPOTIFY_REDIRECT_URI", "http://localhost:8888/callback")
spotify_auth = SpotifyAuth(CLIENT_ID, REDIRECT_URI)

# Initialize LLM Manager
llm_manager = LLMManager()

# Initialize Spotify API client
spotify_api = SpotifyAPI(spotify_auth)

# Initialize conversation store
conversation_store = ConversationStore()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydantic model for message requests
class MessageRequest(BaseModel):
    message: str

# Add logging functionality
logger = setup_logger("main")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    if 'display_name' in request.session:
        return RedirectResponse(url="/chat", status_code=303)
    return templates.TemplateResponse("login.html", {"request": request})

@app.get("/login")
async def login(request: Request):
    # Store code verifier in session for later use
    request.session['code_verifier'] = spotify_auth.code_verifier
    
    # Redirect to Spotify authorization page
    auth_url = spotify_auth.get_auth_url()
    return RedirectResponse(url=auth_url, status_code=303)

@app.get("/callback")
async def callback(request: Request, code: Optional[str] = None, error: Optional[str] = None):
    if error:
        return RedirectResponse(url="/", status_code=303)
    
    if not code:
        return RedirectResponse(url="/", status_code=303)
    
    # Restore code verifier from session
    code_verifier = request.session.get('code_verifier')
    if not code_verifier:
        return RedirectResponse(url="/", status_code=303)
        
    spotify_auth.code_verifier = code_verifier
    
    # Exchange authorization code for tokens
    tokens = spotify_auth.get_tokens(code)
    
    if 'error' in tokens:
        return RedirectResponse(url="/", status_code=303)
    
    # Store tokens in session
    request.session['access_token'] = tokens.get('access_token')
    request.session['refresh_token'] = tokens.get('refresh_token')
    
    # Get user profile info
    user_profile = spotify_auth.get_user_profile(request.session['access_token'])
    
    # Store in session with proper fallback
    request.session['display_name'] = user_profile.get('display_name', 'Spotify User')
    
    return RedirectResponse(url="/chat", status_code=303)

@app.get("/chat", response_class=HTMLResponse)
async def chat(request: Request):
    if 'display_name' not in request.session:
        return RedirectResponse(url="/", status_code=303)
    
    display_name = request.session.get('display_name')
    return templates.TemplateResponse(
        "chat.html", 
        {"request": request, "display_name": display_name}
    )

@app.post("/api/send_message")
async def send_message(message_request: MessageRequest, request: Request):
    try:
        # Get user access token
        access_token = request.session.get('access_token', None)
        if not access_token:
            return {"response": "Your Spotify session has expired. Please log in again."}
        
        user_id = access_token
        user_message = message_request.message
        
        # Add user message to history
        conversation_store.add_message(user_id, "user", user_message)
        
        # Get history for context 
        history = conversation_store.get_history(user_id)
        
        # Check if model is ready
        if not llm_manager.is_model_ready():
            return {
                "response": "The AI model is not loaded yet. Please run: `ollama pull deepseek-r1:1.5b`"
            }
        
        # First, analyze the conversation for mood and recommendation intent
        mood_analysis = llm_manager.analyze_conversation_mood(history, user_message)
        
        # Only proceed with recommendations if needed
        if mood_analysis.get("wants_recommendations", False):
            # Get user's top artists and tracks
            top_artists = spotify_api.get_user_top_items(access_token, "artists")
            top_tracks = spotify_api.get_user_top_items(access_token, "tracks")
            
            # Create a search query
            query = spotify_api.create_recommendation_query(
                mood_analysis.get("mood", ""), 
                top_artists.get("items", []),
                top_tracks.get("items", [])
            )
            
            # Add genres if available
            if mood_analysis.get("genres"):
                for genre in mood_analysis.get("genres", ["bollywood"])[:1]:
                    query += f" genre:{genre}"
            
            # Search Spotify
            logger.info(f"Query : {query}")
            search_results = spotify_api.search(
                access_token, 
                query, 
                types=["track", "artist"], 
                limit=5
            )
            
            # Process tracks for display
            tracks = search_results.get("tracks", {}).get("items", [])
            processed_tracks = []
            
            for track in tracks:
                processed_tracks.append({
                    "name": track.get("name", "Unknown"),
                    "artist": ", ".join([artist.get("name", "") for artist in track.get("artists", [])]),
                    "album": track.get("album", {}).get("name", ""),
                    "image_url": track.get("album", {}).get("images", [{}])[0].get("url", ""),
                    "preview_url": track.get("preview_url", ""),
                    "spotify_url": track.get("external_urls", {}).get("spotify", "")
                })
            
            # Generate a response message
            response_message = f"Based on our conversation, I've created a playlist for your {mood_analysis.get('mood', 'current')} mood. Here are some tracks I think you'll enjoy:"
            
            # Add the assistant message to history
            conversation_store.add_message(user_id, "assistant", response_message)
            
            # Return both text response and music recommendations
            return {
                "response": response_message,
                "animate": True,
                "music_recommendations": {
                    "tracks": processed_tracks,
                    "mood": mood_analysis.get("mood", ""),
                    "genres": mood_analysis.get("genres", [])
                }
            }
        
        # If no recommendation needed, proceed with normal chat
        try:
            # Use the response from mood analysis
            response_text = mood_analysis.get("response", "")
            
            # Add the assistant message to history
            conversation_store.add_message(user_id, "assistant", response_text)
            
            return {"response": response_text, "animate": True}
            
        except Exception as e:
            return {"response": f"I encountered an error: {str(e)}"}
        
    except Exception as e:
        return {"response": f"An error occurred: {str(e)}"}

@app.post("/api/clear_history")
async def clear_history(request: Request):
    user_id = request.session.get('access_token', 'anonymous')
    conversation_store.clear_history(user_id)
    return {"success": True}

@app.get("/logout")
async def logout(request: Request):
    request.session.clear()
    return RedirectResponse(url="/", status_code=303)

if __name__ == "__main__":
    logger.info("Starting Spotify Chat application...")
    uvicorn.run("main:app", host="0.0.0.0", port=8888, reload=True) 