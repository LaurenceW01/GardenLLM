import logging
from datetime import datetime, timedelta
from typing import Dict, List
import tiktoken

# Set up logging for the conversation manager
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Constants for token management
MODEL_NAME = "gpt-4-turbo"  # The model name used for encoding
MAX_TOKENS = 4096            # Maximum allowed tokens for a conversation
TOKEN_BUFFER = 512           # Buffer to prevent exceeding the token limit

class ConversationManager:
    """
    Manages in-memory conversation history for AI chat sessions.
    Handles session storage, token counting, timeouts, and message trimming.
    """
    def __init__(self):
        self.conversations: Dict[str, Dict] = {}  # Stores all conversations by ID
        self.encoding = tiktoken.encoding_for_model(MODEL_NAME)  # Token encoder for the model
        self.conversation_timeout = timedelta(minutes=30)  # Timeout for inactive conversations

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string using the model's encoding."""
        return len(self.encoding.encode(text))  # Encode and count tokens

    def _count_message_tokens(self, message: Dict) -> int:
        """Count tokens in a message, including role and content (text or image)."""
        total = 0  # Initialize total token count
        total += self._count_tokens(message.get("role", ""))  # Count tokens in the role
        content = message.get("content", "")  # Get the content from the message
        if isinstance(content, list):  # If content is a list (e.g., text and images)
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        total += self._count_tokens(item.get("text", ""))  # Count text tokens
                    elif item.get("type") == "image_url":
                        total += 100  # Approximate token cost for image
                else:
                    total += self._count_tokens(str(item))  # Count tokens for other items
        else:
            total += self._count_tokens(str(content))  # Count tokens for plain text content
        return total  # Return the total token count

    def _is_conversation_active(self, conversation_id: str) -> bool:
        """Check if a conversation is still active based on last activity and timeout."""
        if conversation_id not in self.conversations:
            return False  # Conversation ID not found
        last_activity = self.conversations[conversation_id].get('last_activity')
        if not last_activity:
            return False  # No last activity timestamp
        return datetime.now() - last_activity < self.conversation_timeout  # Check timeout

    def add_message(self, conversation_id: str, message: Dict) -> None:
        """Add a message to the conversation, managing token limits and timeouts."""
        if conversation_id not in self.conversations:
            logger.info(f"Creating new conversation {conversation_id}")
            self.conversations[conversation_id] = {
                'messages': [],
                'last_activity': datetime.now()
            }
        self.conversations[conversation_id]['last_activity'] = datetime.now()  # Update last activity
        self.conversations[conversation_id]['messages'].append(message)  # Add the message
        logger.info(f"Added message to conversation {conversation_id}. Total messages: {len(self.conversations[conversation_id]['messages'])}")
        # Trim messages if token limit exceeded
        while self._get_total_tokens(conversation_id) > (MAX_TOKENS - TOKEN_BUFFER):
            if len(self.conversations[conversation_id]['messages']) > 2:
                logger.info(f"Trimming conversation {conversation_id} due to token limit")
                del self.conversations[conversation_id]['messages'][1]  # Remove oldest after system message
            else:
                break  # Only two messages left, stop trimming

    def _get_total_tokens(self, conversation_id: str) -> int:
        """Get the total number of tokens in a conversation."""
        if conversation_id not in self.conversations:
            return 0  # Conversation not found
        return sum(self._count_message_tokens(msg) for msg in self.conversations[conversation_id]['messages'])

    def get_messages(self, conversation_id: str) -> List[Dict]:
        """Retrieve all messages for a conversation if it's still active."""
        if not self._is_conversation_active(conversation_id):
            logger.info(f"Conversation {conversation_id} has timed out or doesn't exist")
            self.clear_conversation(conversation_id)  # Remove inactive conversation
            return []  # Return empty list
        messages = self.conversations.get(conversation_id, {}).get('messages', [])
        logger.info(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
        return messages

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear all data for a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]  # Delete the conversation 