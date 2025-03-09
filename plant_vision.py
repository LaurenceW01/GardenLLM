from openai import OpenAI
import os
import logging
import base64
from typing import Optional, Tuple, List, Dict
from datetime import datetime, timedelta
import imghdr
import traceback
try:
    from PIL import Image
except ImportError:
    raise ImportError("Please install Pillow with: pip install Pillow")
import io
import openai
import tiktoken

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Constants for token management
MAX_TOKENS = 4000  # Maximum tokens for context
TOKEN_BUFFER = 1000  # Buffer for new responses
MODEL_NAME = "gpt-4-turbo"  # Updated to use gpt-4-turbo

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, Dict] = {}  # Changed to store metadata
        self.encoding = tiktoken.encoding_for_model(MODEL_NAME)
        self.conversation_timeout = timedelta(minutes=30)  # Timeout after 30 minutes

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string"""
        return len(self.encoding.encode(text))

    def _count_message_tokens(self, message: Dict) -> int:
        """Count tokens in a message including role and content"""
        total = 0
        # Count tokens in the role
        total += self._count_tokens(message.get("role", ""))
        
        # Count tokens in the content
        content = message.get("content", "")
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict):
                    if item.get("type") == "text":
                        total += self._count_tokens(item.get("text", ""))
                    # Image URLs have a fixed token cost
                    elif item.get("type") == "image_url":
                        total += 100  # Approximate token cost for image
                else:
                    total += self._count_tokens(str(item))
        else:
            total += self._count_tokens(str(content))
        
        return total

    def _is_conversation_active(self, conversation_id: str) -> bool:
        """Check if a conversation is still active"""
        if conversation_id not in self.conversations:
            return False
        
        last_activity = self.conversations[conversation_id].get('last_activity')
        if not last_activity:
            return False
            
        return datetime.now() - last_activity < self.conversation_timeout

    def add_message(self, conversation_id: str, message: Dict) -> None:
        """Add a message to the conversation while managing token limit"""
        # Initialize conversation if it doesn't exist
        if conversation_id not in self.conversations:
            logger.info(f"Creating new conversation {conversation_id}")
            self.conversations[conversation_id] = {
                'messages': [],
                'last_activity': datetime.now()
            }
        
        # Update last activity
        self.conversations[conversation_id]['last_activity'] = datetime.now()
        
        # Add new message
        self.conversations[conversation_id]['messages'].append(message)
        logger.info(f"Added message to conversation {conversation_id}. Total messages: {len(self.conversations[conversation_id]['messages'])}")
        
        # Check total tokens and trim if necessary
        while self._get_total_tokens(conversation_id) > (MAX_TOKENS - TOKEN_BUFFER):
            # Remove oldest message after system message
            if len(self.conversations[conversation_id]['messages']) > 2:
                logger.info(f"Trimming conversation {conversation_id} due to token limit")
                del self.conversations[conversation_id]['messages'][1]
            else:
                break

    def _get_total_tokens(self, conversation_id: str) -> int:
        """Get total tokens in a conversation"""
        if conversation_id not in self.conversations:
            return 0
        
        return sum(self._count_message_tokens(msg) for msg in self.conversations[conversation_id]['messages'])

    def get_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation if it's still active"""
        if not self._is_conversation_active(conversation_id):
            logger.info(f"Conversation {conversation_id} has timed out or doesn't exist")
            self.clear_conversation(conversation_id)
            return []
        
        messages = self.conversations.get(conversation_id, {}).get('messages', [])
        logger.info(f"Retrieved {len(messages)} messages for conversation {conversation_id}")
        return messages

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear a conversation history"""
        if conversation_id in self.conversations:
            del self.conversations[conversation_id]

# Initialize conversation manager
conversation_manager = ConversationManager()

def convert_heic_to_jpeg(image_data: bytes) -> Optional[bytes]:
    """
    Convert HEIC image to JPEG format
    """
    try:
        try:
            from pillow_heif import register_heif_opener
        except ImportError:
            logger.error("pillow_heif not installed. Please install with: pip install pillow-heif")
            return None
            
        register_heif_opener()
        
        # Create a BytesIO object from the image data
        image_io = io.BytesIO(image_data)
        
        # Open and convert the image
        with Image.open(image_io) as img:
            # Create a BytesIO object to save the JPEG
            jpeg_io = io.BytesIO()
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Save as JPEG
            img.save(jpeg_io, format='JPEG', quality=95)
            return jpeg_io.getvalue()
    except Exception as e:
        logger.error(f"Error converting HEIC to JPEG: {e}")
        return None

def process_image(image_data: bytes) -> Tuple[bytes, str]:
    """
    Process and validate the image, converting if necessary
    """
    try:
        # Try to open the image with PIL to validate it
        img = Image.open(io.BytesIO(image_data))
        
        # Handle MPO images (multi-picture format)
        if img.format and img.format.upper() == 'MPO':
            logger.info("Converting MPO image to JPEG")
            # MPO contains multiple images, we'll use the first one
            img.seek(0)  # Ensure we're at the first image
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Save as JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue(), 'jpeg'
        
        # If it's a HEIC/HEIF image, convert it
        if img.format and img.format.upper() in ['HEIC', 'HEIF']:
            logger.info("Converting HEIC/HEIF image to JPEG")
            converted_data = convert_heic_to_jpeg(image_data)
            if converted_data:
                return converted_data, 'jpeg'
            raise ValueError("Failed to convert HEIC/HEIF image")
        
        # For other formats, ensure they're in a web-friendly format
        if img.format and img.format.upper() not in ['JPEG', 'JPG', 'PNG']:
            logger.info(f"Converting {img.format} image to JPEG")
            # Convert to RGB if necessary
            if img.mode != 'RGB':
                img = img.convert('RGB')
            # Save as JPEG
            output = io.BytesIO()
            img.save(output, format='JPEG', quality=95)
            return output.getvalue(), 'jpeg'
        
        return image_data, img.format.lower() if img.format else 'jpeg'
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")
        raise ValueError("Invalid image format or corrupted image file")

def analyze_plant_image(image_data: bytes, user_message: Optional[str] = None, conversation_id: Optional[str] = None) -> str:
    """
    Analyze a plant image using GPT-4 Turbo with vision capabilities
    """
    try:
        # Process and validate the image
        processed_image, image_format = process_image(image_data)
        
        # Convert image to base64
        base64_image = base64.b64encode(processed_image).decode('utf-8')
        
        # Prepare the system message and user query
        if user_message:
            query = f"Please analyze this plant image. User's comment: {user_message}"
        else:
            query = """Please analyze this plant image and provide:
            1. Plant identification (species name and common name)
            2. Assessment of the plant's current condition
            3. Specific care recommendations to improve or maintain its health
            4. Any visible issues or concerns
            Please format the response in markdown."""

        # Create conversation ID if not provided
        if not conversation_id:
            conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get existing conversation or start new one
        if not conversation_manager.get_messages(conversation_id):
            # Add system message
            conversation_manager.add_message(conversation_id, {
                "role": "system",
                "content": """You are a plant expert who analyzes plant images and provides detailed care recommendations. 
                When users ask follow-up questions, refer to the specific plant from the image that was analyzed, not plants from any database.
                If the question is about the plant in the image or your previous analysis, provide detailed responses based on that specific plant.
                Format your responses in markdown."""
            })

        # Add user message with image
        conversation_manager.add_message(conversation_id, {
            "role": "user",
            "content": [
                {"type": "text", "text": query},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_format};base64,{base64_image}",
                        "detail": "high"
                    }
                }
            ]
        })

        # Get conversation history
        messages = conversation_manager.get_messages(conversation_id)

        # Call GPT-4 Turbo API with conversation history
        response = client.chat.completions.create(
            model=MODEL_NAME,
            messages=messages,
            max_tokens=1000,
            temperature=0.7,
            seed=123,  # Added for consistency
            response_format={ "type": "text" }
        )

        # Add assistant's response to conversation history
        conversation_manager.add_message(conversation_id, {
            "role": "assistant",
            "content": response.choices[0].message.content
        })

        return response.choices[0].message.content

    except openai.AuthenticationError as e:
        logger.error(f"Authentication error with OpenAI: {e}")
        return "I apologize, but there seems to be an issue with the OpenAI API authentication. Please contact support."
    except openai.NotFoundError as e:
        logger.error(f"Model not found error: {e}")
        return "I apologize, but the vision analysis service is currently unavailable. Please try again later or contact support."
    except Exception as e:
        logger.error(f"Error analyzing plant image: {e}")
        logger.error(f"Full error: {traceback.format_exc()}")
        return "I apologize, but I encountered an error while analyzing the plant image. Please try again."

def validate_image(image_data: bytes) -> bool:
    """
    Validate that the uploaded file is a valid image
    """
    try:
        # Try to process the image
        process_image(image_data)
        return True
    except Exception:
        return False

def save_image(image_data: bytes, filename: str) -> str:
    """
    Save uploaded image to disk
    """
    try:
        # Process the image before saving
        processed_image, image_format = process_image(image_data)
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join('static', 'uploads')
        os.makedirs(upload_dir, exist_ok=True)

        # Generate unique filename with correct extension
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        base_name = os.path.splitext(filename)[0]
        safe_filename = f"{timestamp}_{base_name}.{image_format}"
        file_path = os.path.join(upload_dir, safe_filename)

        # Save the processed image
        with open(file_path, 'wb') as f:
            f.write(processed_image)

        return file_path
    except Exception as e:
        logger.error(f"Error saving image: {e}")
        raise 