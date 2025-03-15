# **Demo** : Proof of Conecept
To demonstrate the feasibility of my initial solution, I have developed a proof of concept (PoC) and created a demo video showcasing the initial implementation. This highlights my understanding of the project requirements and my ability to contribute effectively. The final approach which will be in proposal will be more sophisticated than this.


https://github.com/user-attachments/assets/622fcba6-4760-49a0-9826-d26d8207464a

What is happening behind the scenes?
Behind the scenes, the **LLM (Deepseek-r1 1.5b)** analyzes the user's query and conversation history to determine their **mood and preferences**. It extracts whether the user is seeking recommendations, their emotional state, and any specified **genres or artists**. An example response from the LLM is:  

```
{'wants_recommendations': True, 'mood': 'happy', 'genres': [], 'artists': [], 'response': "I'm happy to help you with some upbeat pop tracks! Would you like me to suggest a playlist of songs that are easy to listen to and perfect for your mood?"}
```

Here, `wants_recommendations` is **True** since the user appears to be requesting music suggestions. If the user specifies preferences, the `genres` and `artists` fields are populated accordingly.  

However, **if the user's query does not indicate a request for recommendations** (e.g., general conversation, factual inquiries, or unrelated topics), then `wants_recommendations` is set to **False**, and the system does not generate song suggestions and the response is returned to the user.

How the Search Query is Constructed
When the user requests a recommendation, the system constructs a Spotify search query using the detected mood and top artists. For example:
```
happy artist:Vishal-Shekhar
```
- The mood (e.g., "happy") is extracted by the LLM's mood detection.
- The artist (e.g., "Vishal-Shekhar") is retrieved from Spotify's /me/top/artists endpoint, which fetches the user's most listened-to artists.

These elements are combined into a search query sent to Spotify’s search API, ensuring personalized recommendations that align with the user's current mood and musical preferences.

# Setting Up the repo:


### **Step 1: Setting Up Ollama with DeepSeek Model**

Follow these steps to set up **Ollama** with the **DeepSeek 5B model** and ensure your **Spotify Developer app** is configured correctly.

------
## **1. Pull the Deepseek-r1:1.5b Model**
To download the **Deepseek-r1:1.5b** model, run the following command in your terminal:

```bash
ollama pull deepseek-r1:1.5b
```

- This process **downloads the model files (~1.5GB)**.
- The time required depends on your internet speed.

---

### **Step 2. Configure Your Spotify Developer App**
Ensure that your **Spotify Developer app** is correctly configured:

1. **Log in to the Spotify Developer Dashboard**  
   - Go to [Spotify Developer Dashboard](https://developer.spotify.com/dashboard).
   - Select your app.

2. **Verify the Redirect URI**  
   - The **Redirect URI** should be set to:  
     ```
     http://localhost:8888/callback
     ```
   - If it's incorrect, update it in your app settings.

3. **Enable Required Scopes**  
   - Check that your app has the following **scopes enabled**:  
     - `user-read-private`
     - `user-read-email`
     - `user-top-read`  
   - These permissions allow the application to retrieve user-specific data.

---

### **3. Restart Your SpotifyChat Application**
Once the **DeepSeek model** has been downloaded and the **Spotify settings** are verified:

- Restart your **SpotifyChat** application to apply the changes.

```bash
python -m uvicorn main:app --host 0.0.0.0 --port 8888 --reload
```

Your **Ollama instance** will now use the **DeepSeek 5B model**, and Spotify authentication should work correctly.

---

If you encounter any issues, ensure:
✅ Ollama is installed and running.  
✅ The DeepSeek model is successfully pulled.  
✅ Your Spotify Developer app settings are correct.
