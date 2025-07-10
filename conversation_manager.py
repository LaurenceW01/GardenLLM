import logging
from datetime import datetime, timedelta
from typing import Dict, List
import tiktoken
import uuid

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

    def generate_conversation_id(self, mode: str = "general") -> str:
        """Generate a unique conversation ID with optional mode prefix."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]  # Use first 8 characters of UUID for uniqueness
        mode_prefix = mode[:3] if mode else "gen"  # Use first 3 characters of mode
        return f"{mode_prefix}_{timestamp}_{unique_id}"

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
                'last_activity': datetime.now(),
                'metadata': {
                    'created_at': datetime.now(),
                    'mode': message.get('mode', 'general'),
                    'total_messages': 0
                }
            }
        self.conversations[conversation_id]['last_activity'] = datetime.now()  # Update last activity
        self.conversations[conversation_id]['messages'].append(message)  # Add the message
        self.conversations[conversation_id]['metadata']['total_messages'] += 1  # Update message count
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

    def get_conversation_context(self, conversation_id: str) -> Dict:
        """Get conversation metadata and context information."""
        if conversation_id not in self.conversations:
            return {
                'exists': False,
                'active': False,
                'messages': [],
                'metadata': {}
            }
        
        conversation = self.conversations[conversation_id]
        is_active = self._is_conversation_active(conversation_id)
        
        return {
            'exists': True,
            'active': is_active,
            'messages': conversation.get('messages', []),
            'metadata': conversation.get('metadata', {}),
            'total_tokens': self._get_total_tokens(conversation_id),
            'last_activity': conversation.get('last_activity'),
            'message_count': len(conversation.get('messages', []))
        }

    def switch_conversation_mode(self, conversation_id: str, new_mode: str) -> bool:
        """Switch the mode of an existing conversation while preserving context."""
        if conversation_id not in self.conversations:
            logger.warning(f"Cannot switch mode for non-existent conversation {conversation_id}")
            return False
        
        # Update the mode in metadata
        if 'metadata' not in self.conversations[conversation_id]:
            self.conversations[conversation_id]['metadata'] = {}
        
        old_mode = self.conversations[conversation_id]['metadata'].get('mode', 'unknown')
        self.conversations[conversation_id]['metadata']['mode'] = new_mode
        self.conversations[conversation_id]['last_activity'] = datetime.now()
        
        logger.info(f"Switched conversation {conversation_id} from {old_mode} to {new_mode}")
        return True

    def get_conversation_summary(self, conversation_id: str) -> Dict:
        """Get a summary of the conversation including key statistics."""
        context = self.get_conversation_context(conversation_id)
        if not context['exists']:
            return {'error': 'Conversation not found'}
        
        messages = context['messages']
        user_messages = [msg for msg in messages if msg.get('role') == 'user']
        assistant_messages = [msg for msg in messages if msg.get('role') == 'assistant']
        
        return {
            'conversation_id': conversation_id,
            'total_messages': len(messages),
            'user_messages': len(user_messages),
            'assistant_messages': len(assistant_messages),
            'total_tokens': context['total_tokens'],
            'mode': context['metadata'].get('mode', 'unknown'),
            'created_at': context['metadata'].get('created_at'),
            'last_activity': context['last_activity'],
            'is_active': context['active']
        }

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear all data for a conversation."""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]  # Delete the conversation
            logger.info(f"Cleared conversation {conversation_id}")

    def cleanup_expired_conversations(self) -> int:
        """Remove all expired conversations and return the count of removed conversations."""
        expired_count = 0  # Initialize counter for expired conversations
        current_time = datetime.now()  # Get current time
        
        # Create a list of conversation IDs to remove (to avoid modifying dict during iteration)
        to_remove = []  # List to store conversation IDs to remove
        
        for conversation_id, conversation_data in self.conversations.items():
            last_activity = conversation_data.get('last_activity')  # Get last activity time
            if last_activity and (current_time - last_activity) > self.conversation_timeout:
                to_remove.append(conversation_id)  # Add to removal list
                expired_count += 1  # Increment expired count
        
        # Remove expired conversations
        for conversation_id in to_remove:
            del self.conversations[conversation_id]  # Remove from conversations dict
            logger.info(f"Removed expired conversation {conversation_id}")  # Log removal
        
        if expired_count > 0:
            logger.info(f"Cleaned up {expired_count} expired conversations")  # Log cleanup summary
        
        return expired_count  # Return count of removed conversations

    def get_all_conversations(self) -> Dict[str, Dict]:
        """Get all active conversations with their metadata."""
        active_conversations = {}  # Dictionary to store active conversations
        
        for conversation_id, conversation_data in self.conversations.items():
            if self._is_conversation_active(conversation_id):  # Check if conversation is active
                active_conversations[conversation_id] = {
                    'metadata': conversation_data.get('metadata', {}),
                    'message_count': len(conversation_data.get('messages', [])),
                    'total_tokens': self._get_total_tokens(conversation_id),
                    'last_activity': conversation_data.get('last_activity')
                }
        
        return active_conversations  # Return active conversations

    def get_conversation_stats(self) -> Dict:
        """Get overall statistics for all conversations."""
        total_conversations = len(self.conversations)  # Total number of conversations
        active_conversations = len([cid for cid in self.conversations.keys() if self._is_conversation_active(cid)])  # Count active conversations
        total_messages = sum(len(conv.get('messages', [])) for conv in self.conversations.values())  # Total messages across all conversations
        total_tokens = sum(self._get_total_tokens(cid) for cid in self.conversations.keys())  # Total tokens across all conversations
        
        return {
            'total_conversations': total_conversations,
            'active_conversations': active_conversations,
            'expired_conversations': total_conversations - active_conversations,
            'total_messages': total_messages,
            'total_tokens': total_tokens,
            'average_messages_per_conversation': total_messages / total_conversations if total_conversations > 0 else 0,
            'average_tokens_per_conversation': total_tokens / total_conversations if total_conversations > 0 else 0
        } 