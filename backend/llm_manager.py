import requests
import json
from typing import Dict, Optional, Generator, List
import re
from backend.logger import setup_logger

logger = setup_logger("llm_manager")

class LLMManager:
    def __init__(self, base_url: str = None):
        try:
            response = requests.get("http://localhost:11434", timeout=1)
            if response.status_code == 200:
                self.base_url = "http://localhost:11434"
                logger.info("✅ Connected to Ollama on localhost")
            else:
                self.base_url = "http://ollama:11434"
                logger.warning("⚠️ Falling back to Docker service name 'ollama'")
        except:
            self.base_url = "http://ollama:11434"
            logger.warning("⚠️ Couldn't connect to localhost, falling back to Docker service name")
        
        self.model = "deepseek-r1:1.5b"
        self.generate_endpoint = f"{self.base_url}/api/generate"
        self.chat_endpoint = f"{self.base_url}/api/chat"
    
    def chat(self, message: str, history: List[Dict] = None, stream: bool = True):
        """
        Send a message to the LLM model with conversation history
        """
        if history is None:
            history = []
            
        # Format the messages for Ollama's chat API
        messages = []
        
        # Add history
        for entry in history:
            if entry.get('role') == 'user':
                messages.append({"role": "user", "content": entry.get('content', '')})
            else:
                messages.append({"role": "assistant", "content": entry.get('content', '')})
        
        # Add current message
        messages.append({"role": "user", "content": message})
        
        payload = {
            "model": self.model,
            "messages": messages,
            "stream": stream,
            "options": {
                "temperature": 0.2,
                "top_p": 0.8
            }
        }
        
        # Use the chat endpoint for more context
        response = requests.post(self.chat_endpoint, json=payload)
        
        if not stream:
            result = response.json()
            # Clean response
            if "message" in result and "content" in result["message"]:
                result["message"]["content"] = self._clean_response(result["message"]["content"])
            return result
        else:
            return self._process_stream(response)
    
    def _process_stream(self, response):
        """
        Process a streaming response from the LLM
        """
        full_response = ""
        for line in response.iter_lines():
            if line:
                chunk = json.loads(line)
                if "message" in chunk and "content" in chunk["message"]:
                    content = chunk["message"]["content"]
                    # Clean each chunk of content
                    cleaned_content = self._clean_response(content)
                    full_response += cleaned_content
                    yield {"chunk": cleaned_content, "full": full_response}
                elif "done" in chunk and chunk["done"]:
                    break
    
    def is_model_ready(self) -> bool:
        """
        Check if the model is ready to use
        """
        try:
            response = requests.get(f"{self.base_url}/api/tags", timeout=3)
            
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m.get("name", "") for m in models]
                
                return any(self.model in model_name for model_name in model_names)
            return False
        except Exception as e:  
            logger.error(f"Error checking if model is ready: {e}")
            return False

    def _clean_response(self, text):
        """
        Remove <think> tags and clean up the response
        """
        # Remove <think> tags and their content
        cleaned = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL)
        # Remove any other thinking indicators
        cleaned = re.sub(r'(Thinking:|thinking:)', '', cleaned)
        # Trim extra whitespace
        cleaned = cleaned.strip()
        return cleaned
    
    def analyze_conversation_mood(self, conversation_history, user_message):
        """
        Analyze the conversation to detect if the user is explicitly asking for music
        Returns a dict with mood, recommendation_request flag, and genres
        """
        # Create a prompt for the mood analysis
        history_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in conversation_history[-3:]])
        
        prompt = f"""
            **Role**: You are a music recommendation expert specializing in mood analysis and contextual understanding. 
            **Task**: Analyze conversation history and latest message to determine if the user wants music recommendations.

            **Instructions**:
            1. Recommendation Trigger:
            - Set `wants_recommendations` to True ONLY if:
                a) User explicitly requests music (e.g., "recommend songs", "make me a playlist")
                b) User implies musical need through context (e.g., "I need study music", "What should I listen to?")

            2. Mood Detection:
            - Analyze ENTIRE conversation history to determine emotional state
            - Use these mood mappings (expand as needed):
                {{
                    "happy": ["joyful", "excited", "celebratory"],
                    "sad": ["melancholic", "heartbroken", "gloomy"],
                    "calm": ["relaxed", "peaceful", "meditative"],
                    "energetic": ["pumped", "hyped", "adrenaline"]
                }}

            3. Entity Extraction:
            - `genres`: ONLY include if explicitly mentioned in LATEST message (e.g., "rock", "lo-fi")
            - `artists`: ONLY include if named in LATEST message (e.g., "Taylor Swift", "BTS")

            **Examples**:

            1. User message: "Can you suggest some upbeat pop songs?"
            {{
                "wants_recommendations": true,
                "mood": "happy",
                "genres": ["pop"],
                "artists": [],
                "response": "I'll find some upbeat pop tracks! Any specific artists or sub-genres you prefer?"
            }}

            2. User message: "I just finished a workout"
            Conversation history: "User mentioned feeling tired after work earlier"
            {{
                "wants_recommendations": false,
                "mood": "neutral",
                "genres": [],
                "artists": [],
                "response": "Great job on the workout! Would you like some energetic music to keep the momentum going?"
            }}

            3. User message: "Play something like Radiohead"
            {{
                "wants_recommendations": true,
                "mood": "calm",
                "genres": [],
                "artists": ["Radiohead"],
                "response": "Creating a playlist with Radiohead's style. Shall I focus on their newer or older sound?"
            }}

            **Output Format**: STRICTLY use this JSON structure:
            {{
                "wants_recommendations": boolean,
                "mood": string (from: happy/sad/calm/energetic/neutral),
                "genres": array[string] (ONLY explicit in latest message),
                "artists": array[string] (ONLY explicit in latest message),
                "response": string (natural language reply ALWAYS addressing latest message)
            }}
            - `genres`: ONLY include if explicitly mentioned in LATEST message and must be one of the following: ["pop", "rock","bollywood", "lo-fi", "jazz", "classical", "hip-hop", "electronic"]
            **Current Analysis**:
            Conversation History:
            {history_text}

            Latest Message:
            {user_message}

            **Generate JSON Response**:
            """
                    
        # Call the LLM
        response = self.chat(prompt, stream=False)
        
        # Extract and parse the JSON response
        if "message" in response and "content" in response["message"]:
            content = response["message"]["content"]
            
            # Extract JSON from the response
            import json
            import re
            
            # Look for JSON pattern between triple backticks
            json_match = re.search(r'```json\s*(.*?)\s*```', content, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Try to find any JSON-like structure
                json_match = re.search(r'({.*})', content, re.DOTALL)
                if json_match:
                    json_str = json_match.group(1)
                else:
                    json_str = content
            
            try:
                result = json.loads(json_str)
                logger.info(f"Result from LLM: {result}")
                # Add additional safety check
                if not isinstance(result.get("wants_recommendations"), bool):
                    result["wants_recommendations"] = False
                return result
            except json.JSONDecodeError:
                logger.error("Failed to parse JSON from response")
                return {
                    "mood": "neutral",
                    "wants_recommendations": False,
                    "genres": [],
                    "artists": [],
                    "response": "I'm not sure what you're asking. Can you clarify?"
                }
        
        return {
            "mood": "neutral",
            "wants_recommendations": False,
            "genres": [],
            "artists": [],
            "response": "I'm not sure what you're asking. Can you clarify?"
        } 