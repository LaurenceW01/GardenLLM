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

    def get_mode_specific_system_prompt(self, mode: str, conversation_context: Dict = {}) -> str:
        """Generate mode-specific system prompts with conversation context."""
        base_prompts = {
            "image_analysis": """You are an expert plant identification specialist with deep knowledge of horticulture, plant health, and gardening practices. You can identify plants from images and provide detailed care information.

Your expertise includes:
- Plant identification from photos
- Health assessment and disease diagnosis
- Care recommendations for Houston, TX climate
- Soil, water, light, and temperature requirements
- Pruning, fertilizing, and maintenance advice

Previous conversation context: {context}

Always provide accurate, helpful information and ask for clarification if needed.""",
            
            "database": """You are a knowledgeable gardening assistant with access to the user's garden database. You can help with plant care, garden management, and provide personalized advice based on their specific plants and garden setup.

Your capabilities include:
- Accessing and querying the user's garden database
- Providing care information for specific plants
- Garden planning and plant recommendations
- Seasonal care advice for Houston, TX climate
- Troubleshooting plant issues

Previous conversation context: {context}

Always reference the user's actual garden data when possible and provide practical, actionable advice.""",
            
            "general": """You are a helpful gardening assistant that can work in multiple modes. You can help with plant identification, garden database queries, and general gardening advice.

Previous conversation context: {context}

Please provide helpful, accurate information and ask for clarification if needed."""
        }
        
        # Get the appropriate base prompt for the mode
        base_prompt = base_prompts.get(mode, base_prompts["general"])
        
        # Extract context information if provided
        context_info = ""
        if conversation_context and conversation_context.get('exists'):
            messages = conversation_context.get('messages', [])
            if messages:
                # Create a summary of recent conversation context
                recent_messages = messages[-3:]  # Last 3 messages for context
                context_parts = []
                for msg in recent_messages:
                    role = msg.get('role', 'unknown')
                    content = msg.get('content', '')
                    if role == 'user' and content:
                        context_parts.append(f"User: {content[:100]}...")
                    elif role == 'assistant' and content:
                        context_parts.append(f"Assistant: {content[:100]}...")
                
                if context_parts:
                    context_info = " ".join(context_parts)
        
        # Format the prompt with context
        return base_prompt.format(context=context_info if context_info else "No previous context")

    def get_conversation_context_summary(self, conversation_id: str, max_length: int = 200) -> str:
        """Generate a concise summary of conversation context for cross-mode transitions."""
        context = self.get_conversation_context(conversation_id)
        if not context['exists']:
            return "No conversation context available"
        
        messages = context['messages']
        if not messages:
            return "No messages in conversation"
        
        # Extract key information from recent messages
        summary_parts = []
        
        # Get the current mode
        mode = context['metadata'].get('mode', 'unknown')
        summary_parts.append(f"Mode: {mode}")
        
        # Get recent user messages for context
        user_messages = [msg for msg in messages[-5:] if msg.get('role') == 'user']
        if user_messages:
            recent_topics = []
            for msg in user_messages:
                content = msg.get('content', '')
                if content:
                    # Extract key topics (improved approach)
                    content_lower = content.lower()
                    plant_keywords = ['tomato', 'pepper', 'herb', 'flower', 'tree', 'shrub', 'plant', 'garden', 'care', 'water', 'sun', 'soil', 'prune', 'fertilize']
                    found_keywords = [word for word in plant_keywords if word in content_lower]
                    if found_keywords:
                        recent_topics.extend(found_keywords[:2])  # Limit to 2 keywords per message
            
            if recent_topics:
                unique_topics = list(set(recent_topics))[:3]  # Limit to 3 unique topics
                summary_parts.append(f"Recent topics: {', '.join(unique_topics)}")
        
        # Get message count
        summary_parts.append(f"Messages: {len(messages)}")
        
        summary = " | ".join(summary_parts)
        
        # Truncate if too long
        if len(summary) > max_length:
            summary = summary[:max_length-3] + "..."
        
        return summary

    def get_conversation_preview(self, conversation_id: str) -> Dict:
        """Generate a detailed preview of conversation content for history display."""
        context = self.get_conversation_context(conversation_id)
        if not context['exists']:
            return {
                'title': 'No conversation',
                'summary': 'Conversation not found',
                'plants_mentioned': [],
                'key_topics': [],
                'actions': [],
                'last_activity': None,
                'message_count': 0
            }
        
        messages = context['messages']
        if not messages:
            return {
                'title': 'Empty conversation',
                'summary': 'No messages in conversation',
                'plants_mentioned': [],
                'key_topics': [],
                'actions': [],
                'last_activity': context.get('last_activity'),
                'message_count': 0,
                'mode': context['metadata'].get('mode', 'unknown')
            }
        
        # Extract plants mentioned
        plants_mentioned = []
        plant_keywords = ['tomato', 'pepper', 'herb', 'flower', 'tree', 'shrub', 'rose', 'lily', 'daisy', 'mint', 'basil', 'oregano', 'sage', 'thyme', 'rosemary', 'lavender', 'succulent', 'cactus', 'fern', 'palm', 'oak', 'maple', 'birch', 'willow', 'cherry', 'apple', 'peach', 'plum', 'lemon', 'lime', 'orange', 'grape', 'strawberry', 'blueberry', 'raspberry', 'blackberry', 'cucumber', 'carrot', 'lettuce', 'spinach', 'kale', 'broccoli', 'cauliflower', 'onion', 'garlic', 'potato', 'sweet potato', 'corn', 'bean', 'pea', 'zucchini', 'squash', 'pumpkin', 'melon', 'watermelon']
        
        # Extract key topics and actions
        key_topics = []
        actions = []
        last_user_message = ""
        last_ai_response = ""
        
        for msg in messages:
            content = msg.get('content', '')
            role = msg.get('role', '')
            
            if content:
                content_lower = content.lower()
                
                # Extract plants mentioned
                for plant in plant_keywords:
                    if plant in content_lower and plant not in plants_mentioned:
                        plants_mentioned.append(plant)
                
                # Extract key topics (improved detection)
                topic_keywords = ['care', 'water', 'sun', 'soil', 'prune', 'fertilize', 'fertilizing', 'plant', 'grow', 'harvest', 'disease', 'pest', 'location', 'photo', 'picture', 'identify', 'diagnose', 'advice', 'tip', 'season', 'weather', 'climate', 'temperature', 'humidity', 'light', 'shade', 'full sun', 'partial shade', 'drought', 'flood', 'maintenance', 'repot', 'transplant', 'seed', 'seedling', 'mature', 'bloom', 'flower', 'fruit', 'vegetable', 'herb', 'annual', 'perennial']
                
                for topic in topic_keywords:
                    if topic in content_lower and topic not in key_topics:
                        key_topics.append(topic)
                
                # Extract actions
                if 'add plant' in content_lower:
                    actions.append('Plant added')
                elif 'update' in content_lower:
                    actions.append('Plant updated')
                elif 'identify' in content_lower or 'what is this' in content_lower:
                    actions.append('Plant identification')
                elif 'care' in content_lower or 'how to' in content_lower:
                    actions.append('Care advice')
                elif 'location' in content_lower or 'where' in content_lower:
                    actions.append('Location query')
                elif 'photo' in content_lower or 'picture' in content_lower:
                    actions.append('Photo request')
                
                # Store last messages for summary
                if role == 'user':
                    last_user_message = content[:100] + "..." if len(content) > 100 else content
                elif role == 'assistant':
                    last_ai_response = content[:100] + "..." if len(content) > 100 else content
        
        # Generate title and summary
        title = "Garden conversation"
        if plants_mentioned:
            title = f"About {', '.join(plants_mentioned[:2])}"
            if len(plants_mentioned) > 2:
                title += f" and {len(plants_mentioned) - 2} more"
        
        summary = ""
        if last_user_message:
            summary = f"Q: {last_user_message}"
        if last_ai_response:
            summary += f" | A: {last_ai_response}"
        
        if not summary:
            summary = f"Conversation about {', '.join(key_topics[:3]) if key_topics else 'gardening'}"
        
        return {
            'title': title,
            'summary': summary,
            'plants_mentioned': plants_mentioned[:5],  # Limit to 5 plants
            'key_topics': key_topics[:5],  # Limit to 5 topics
            'actions': list(set(actions))[:3],  # Limit to 3 unique actions
            'last_activity': context.get('last_activity'),
            'message_count': len(messages),
            'mode': context['metadata'].get('mode', 'unknown')
        }

    def get_conversation_history_summary(self, conversation_id: str) -> Dict:
        """Generate a user-friendly summary for conversation history display."""
        preview = self.get_conversation_preview(conversation_id)
        
        # Create a more user-friendly summary
        summary_parts = []
        
        if preview['plants_mentioned']:
            summary_parts.append(f"Plants: {', '.join(preview['plants_mentioned'])}")
        
        if preview['key_topics']:
            summary_parts.append(f"Topics: {', '.join(preview['key_topics'])}")
        
        if preview['actions']:
            summary_parts.append(f"Actions: {', '.join(preview['actions'])}")
        
        summary = " | ".join(summary_parts) if summary_parts else preview['summary']
        
        return {
            'title': preview['title'],
            'summary': summary,
            'plants_mentioned': preview['plants_mentioned'],
            'key_topics': preview['key_topics'],
            'actions': preview['actions'],
            'last_activity': preview['last_activity'],
            'message_count': preview['message_count'],
            'mode': preview.get('mode', 'unknown'),
            'conversation_id': conversation_id
        }

    def add_conversation_metadata(self, conversation_id: str, metadata: Dict) -> bool:
        """Add or update conversation metadata."""
        if conversation_id not in self.conversations:
            logger.warning(f"Cannot add metadata to non-existent conversation {conversation_id}")
            return False
        
        if 'metadata' not in self.conversations[conversation_id]:
            self.conversations[conversation_id]['metadata'] = {}
        
        # Update metadata
        self.conversations[conversation_id]['metadata'].update(metadata)
        self.conversations[conversation_id]['last_activity'] = datetime.now()
        
        logger.info(f"Updated metadata for conversation {conversation_id}")
        return True

    def create_conversation_with_metadata(self, conversation_id: str, initial_metadata: Dict = {}) -> bool:
        """Create a new conversation with initial metadata."""
        if conversation_id in self.conversations:
            logger.warning(f"Conversation {conversation_id} already exists")
            return False
        
        self.conversations[conversation_id] = {
            'messages': [],
            'last_activity': datetime.now(),
            'metadata': initial_metadata or {
                'created_at': datetime.now(),
                'mode': 'general',
                'total_messages': 0
            }
        }
        
        logger.info(f"Created conversation {conversation_id} with metadata")
        return True

    def get_cross_mode_context(self, conversation_id: str) -> Dict:
        """Get context information suitable for cross-mode transitions."""
        context = self.get_conversation_context(conversation_id)
        if not context['exists']:
            return {
                'available': False,
                'mode': 'unknown',
                'summary': 'No conversation context available',
                'recent_topics': [],
                'user_preferences': {}
            }
        
        # Extract recent topics and user preferences
        messages = context['messages']
        recent_topics = []
        user_preferences = {}
        
        # Analyze recent messages for topics and preferences
        for msg in messages[-10:]:  # Last 10 messages
            if msg.get('role') == 'user':
                content = msg.get('content', '').lower()
                
                # Extract plant-related topics
                plant_keywords = ['tomato', 'pepper', 'herb', 'flower', 'tree', 'shrub', 'vegetable']
                for keyword in plant_keywords:
                    if keyword in content:
                        recent_topics.append(keyword)
                
                # Extract preferences (simple pattern matching)
                if 'prefer' in content or 'like' in content or 'want' in content:
                    # Simple preference extraction
                    if 'sun' in content and ('full' in content or 'partial' in content):
                        user_preferences['light'] = 'full sun' if 'full' in content else 'partial shade'
                    if 'water' in content and ('frequent' in content or 'drought' in content):
                        user_preferences['water'] = 'frequent' if 'frequent' in content else 'drought tolerant'
        
        return {
            'available': True,
            'mode': context['metadata'].get('mode', 'unknown'),
            'summary': self.get_conversation_context_summary(conversation_id),
            'recent_topics': list(set(recent_topics))[:5],  # Unique topics, limit to 5
            'user_preferences': user_preferences,
            'message_count': len(messages),
            'total_tokens': context['total_tokens']
        }

    def create_mode_transition_context(self, conversation_id: str, new_mode: str) -> Dict:
        """Create context for seamless mode transitions."""
        cross_context = self.get_cross_mode_context(conversation_id)
        
        # Generate mode-specific system prompt
        system_prompt = self.get_mode_specific_system_prompt(new_mode, cross_context)
        
        # Create transition context
        transition_context = {
            'conversation_id': conversation_id,
            'previous_mode': cross_context.get('mode', 'unknown'),
            'new_mode': new_mode,
            'system_prompt': system_prompt,
            'context_summary': cross_context.get('summary', ''),
            'recent_topics': cross_context.get('recent_topics', []),
            'user_preferences': cross_context.get('user_preferences', {}),
            'transition_timestamp': datetime.now().isoformat()
        }
        
        # Update conversation metadata with mode transition
        self.add_conversation_metadata(conversation_id, {
            'mode': new_mode,
            'last_mode_transition': datetime.now(),
            'mode_transition_count': cross_context.get('mode_transition_count', 0) + 1
        })
        
        logger.info(f"Created mode transition context for conversation {conversation_id}: {cross_context.get('mode', 'unknown')} -> {new_mode}")
        return transition_context 