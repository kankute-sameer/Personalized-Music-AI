from typing import Dict, List

class ConversationStore:
    def __init__(self):
        self.conversations = {}  # Dict to store conversations by user ID
        
    def add_message(self, user_id, role, content):
        if user_id not in self.conversations:
            self.conversations[user_id] = []
        self.conversations[user_id].append({"role": role, "content": content})
        
    def get_history(self, user_id):
        return self.conversations.get(user_id, [])
    
    def clear_history(self, user_id):
        if user_id in self.conversations:
            self.conversations[user_id] = [] 