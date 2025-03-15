document.addEventListener('DOMContentLoaded', function() {
    const messageForm = document.getElementById('message-form');
    const messageInput = document.getElementById('message-input');
    const chatMessages = document.getElementById('chat-messages');
    const newChatBtn = document.getElementById('new-chat-btn');

    // Auto-resize the textarea as user types
    messageInput.addEventListener('input', function() {
        this.style.height = 'auto';
        this.style.height = (this.scrollHeight) + 'px';
    });

    // Add keydown event listener to the message input
    messageInput.addEventListener('keydown', function(e) {
        // Check if Enter key is pressed without Shift key (Shift+Enter can be used for new line)
        if (e.key === 'Enter' && !e.shiftKey) {
            e.preventDefault(); // Prevent default behavior (new line)
            
            // Only submit if there's text in the input
            if (messageInput.value.trim() !== '') {
                messageForm.dispatchEvent(new Event('submit')); // Programmatically submit the form
            }
        }
    });

    // Handle form submission
    messageForm.addEventListener('submit', function(e) {
        e.preventDefault();
        
        const message = messageInput.value.trim();
        if (!message) return;
        
        // Add user message to chat
        addMessage(message, 'user');
        
        // Clear input
        messageInput.value = '';
        messageInput.style.height = 'auto';
        
        // Disable input during processing
        messageInput.disabled = true;
        
        // Show typing indicator
        const typingIndicator = addTypingIndicator();
        
        // Send message to server
        fetch('/api/send_message', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ message: message }),
        })
        .then(response => {
            if (!response.ok) {
                throw new Error('Network response was not ok');
            }
            return response.json();
        })
        .then(data => {
            // Remove typing indicator
            typingIndicator.remove();
            
            if (data.response) {
                if (data.animate) {
                    // Create message placeholder
                    const messageDiv = document.createElement('div');
                    messageDiv.className = 'message assistant';
                    
                    const contentDiv = document.createElement('div');
                    contentDiv.className = 'message-content';
                    
                    const paragraph = document.createElement('p');
                    paragraph.textContent = '';  // Start empty
                    
                    contentDiv.appendChild(paragraph);
                    messageDiv.appendChild(contentDiv);
                    chatMessages.appendChild(messageDiv);
                    
                    // Animate the text appearing character by character
                    const fullResponse = data.response;
                    let charIndex = 0;
                    const typingSpeed = 20; // milliseconds per character
                    
                    function typeNextChar() {
                        if (charIndex < fullResponse.length) {
                            paragraph.textContent += fullResponse.charAt(charIndex);
                            charIndex++;
                            chatMessages.scrollTop = chatMessages.scrollHeight;
                            setTimeout(typeNextChar, typingSpeed);
                        }
                    }
                    
                    typeNextChar();
                } else {
                    // Add assistant message to chat (no animation)
                    addMessage(data.response, 'assistant');
                }
            }
            
            // If music recommendations are included, display them
            if (data.music_recommendations) {
                setTimeout(() => {
                    displayMusicRecommendations(data.music_recommendations);
                }, 500);
            }
            
            // Re-enable input
            messageInput.disabled = false;
            messageInput.focus();
        })
        .catch(error => {
            console.error('Error:', error);
            typingIndicator.remove();
            
            // Add error message
            addMessage('Sorry, there was an error processing your request.', 'assistant');
            
            // Re-enable input
            messageInput.disabled = false;
            messageInput.focus();
        });
    });
    
    // New chat button
    newChatBtn.addEventListener('click', function() {
        // Clear chat messages except for the first greeting
        while (chatMessages.children.length > 1) {
            chatMessages.removeChild(chatMessages.lastChild);
        }
        
        // Clear history on server
        fetch('/api/clear_history', {
            method: 'POST',
        });
    });
    
    // Helper function to add a message to the chat
    function addMessage(content, role) {
        const messageDiv = document.createElement('div');
        messageDiv.className = `message ${role}`;
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const paragraph = document.createElement('p');
        paragraph.textContent = content;
        
        contentDiv.appendChild(paragraph);
        messageDiv.appendChild(contentDiv);
        chatMessages.appendChild(messageDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
    }
    
    // Helper function to add typing indicator
    function addTypingIndicator() {
        const indicatorDiv = document.createElement('div');
        indicatorDiv.className = 'message assistant';
        
        const contentDiv = document.createElement('div');
        contentDiv.className = 'message-content';
        
        const typingDiv = document.createElement('div');
        typingDiv.className = 'typing-indicator';
        
        // Add the three dots
        for (let i = 0; i < 3; i++) {
            const dot = document.createElement('span');
            typingDiv.appendChild(dot);
        }
        
        contentDiv.appendChild(typingDiv);
        indicatorDiv.appendChild(contentDiv);
        chatMessages.appendChild(indicatorDiv);
        
        // Scroll to bottom
        chatMessages.scrollTop = chatMessages.scrollHeight;
        
        return indicatorDiv;
    }
});

// Function to display music recommendations
function displayMusicRecommendations(recommendations) {
    // Create recommendations container
    const recommendationsDiv = document.createElement('div');
    recommendationsDiv.className = 'music-recommendations';
    
    // Add header
    const headerDiv = document.createElement('div');
    headerDiv.className = 'recommendation-header';
    headerDiv.textContent = 'Music Recommendations';
    recommendationsDiv.appendChild(headerDiv);
    
    // Add mood tag if available
    if (recommendations.mood) {
        const moodSpan = document.createElement('span');
        moodSpan.className = 'recommendation-mood';
        moodSpan.textContent = recommendations.mood;
        recommendationsDiv.appendChild(moodSpan);
    }
    
    // Add genre tags if available
    if (recommendations.genres && recommendations.genres.length > 0) {
        const genresDiv = document.createElement('div');
        genresDiv.className = 'recommendation-genres';
        
        recommendations.genres.forEach(genre => {
            const genreSpan = document.createElement('span');
            genreSpan.className = 'recommendation-genre';
            genreSpan.textContent = genre;
            genresDiv.appendChild(genreSpan);
        });
        
        recommendationsDiv.appendChild(genresDiv);
    }
    
    // Add tracks container
    const tracksContainer = document.createElement('div');
    tracksContainer.id = 'recommendation-tracks';
    tracksContainer.className = 'track-container';
    recommendationsDiv.appendChild(tracksContainer);
    
    // Ensure we have a reasonable number of tracks showing
    const tracksToShow = recommendations.tracks.slice(0, 12); // Limit to 12 tracks
    
    // Display each track
    tracksToShow.forEach(track => {
        const trackCard = document.createElement('div');
        trackCard.className = 'track-card';
        
        // Use default image if none provided
        const imageUrl = track.image_url || 'https://developer.spotify.com/assets/branding-guidelines/icon3@2x.png';
        
        trackCard.innerHTML = `
            <img class="track-image" src="${imageUrl}" alt="${track.name} album art" onerror="this.src='https://developer.spotify.com/assets/branding-guidelines/icon3@2x.png'">
            <div class="track-info">
                <div class="track-name">${track.name}</div>
                <div class="track-artist">${track.artist}</div>
                <div class="track-buttons">
                    ${track.preview_url ? 
                        `<button class="track-button preview-button" data-preview="${track.preview_url}">
                            ▶ Preview
                        </button>` : 
                        ''}
                    <a href="${track.spotify_url}" target="_blank" class="track-button">
                        Open in Spotify
                    </a>
                </div>
            </div>
        `;
        
        tracksContainer.appendChild(trackCard);
    });
    
    // Add event listeners for preview buttons
    const previewButtons = recommendationsDiv.querySelectorAll('.preview-button');
    previewButtons.forEach(button => {
        button.addEventListener('click', function() {
            const previewUrl = this.getAttribute('data-preview');
            playPreview(previewUrl, this);
        });
    });
    
    // Append recommendations to chat messages
    const chatMessages = document.getElementById('chat-messages');
    chatMessages.appendChild(recommendationsDiv);
    
    // Scroll to show the recommendations
    setTimeout(() => {
        recommendationsDiv.scrollIntoView({ behavior: 'smooth', block: 'nearest' });
    }, 100);
}

// Audio preview functionality
let currentAudio = null;
let currentButton = null;

function playPreview(url, button) {
    // Stop any currently playing preview
    if (currentAudio) {
        currentAudio.pause();
        if (currentButton) {
            currentButton.innerHTML = '▶ Preview';
        }
    }
    
    // If clicking the same button that's playing, just stop
    if (currentButton === button && currentAudio && !currentAudio.paused) {
        currentAudio = null;
        currentButton = null;
        return;
    }
    
    // Play the new preview
    currentAudio = new Audio(url);
    currentButton = button;
    currentAudio.play();
    button.innerHTML = '⏸ Pause';
    
    // Reset button when audio ends
    currentAudio.onended = function() {
        button.innerHTML = '▶ Preview';
        currentAudio = null;
        currentButton = null;
    };
} 