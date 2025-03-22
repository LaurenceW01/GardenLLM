from openai import OpenAI  # Import the OpenAI library for API interaction
import os  # Import the os module for environment variable access
import logging  # Import logging for logging messages
import base64  # Import base64 for encoding images
from typing import Optional, Tuple, List, Dict  # Import typing for type annotations
from datetime import datetime, timedelta  # Import datetime for date and time operations
import imghdr  # Import imghdr for image type checking
import traceback  # Import traceback for error tracing
try:
    from PIL import Image  # Import Image from PIL for image processing
except ImportError:
    raise ImportError("Please install Pillow with: pip install Pillow")  # Raise error if Pillow is not installed
import io  # Import io for handling byte streams
import openai  # Import openai for OpenAI API interaction
import tiktoken  # Import tiktoken for token encoding

# Set up logging
logging.basicConfig(level=logging.INFO)  # Configure logging to display INFO level messages
logger = logging.getLogger(__name__)  # Create a logger for this module

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Create an OpenAI client using the API key from environment variables

# Constants for token management
MAX_TOKENS = 4000  # Maximum tokens allowed for context in a conversation
TOKEN_BUFFER = 1000  # Buffer tokens reserved for new responses
MODEL_NAME = "gpt-4-turbo"  # Specify the model name for OpenAI API

class ConversationManager:
    def __init__(self):
        self.conversations: Dict[str, Dict] = {}  # Initialize a dictionary to store conversations with metadata
        self.encoding = tiktoken.encoding_for_model(MODEL_NAME)  # Get the encoding for the specified model
        self.conversation_timeout = timedelta(minutes=30)  # Set conversation timeout to 30 minutes

    def _count_tokens(self, text: str) -> int:
        """Count the number of tokens in a text string"""
        return len(self.encoding.encode(text))  # Encode the text and return the number of tokens

    def _count_message_tokens(self, message: Dict) -> int:
        """Count tokens in a message including role and content"""
        total = 0  # Initialize total token count
        # Count tokens in the role
        total += self._count_tokens(message.get("role", ""))  # Add tokens from the role field
        
        # Count tokens in the content
        content = message.get("content", "")  # Get the content from the message
        if isinstance(content, list):  # Check if content is a list
            for item in content:  # Iterate over each item in the content list
                if isinstance(item, dict):  # Check if item is a dictionary
                    if item.get("type") == "text":  # Check if item type is text
                        total += self._count_tokens(item.get("text", ""))  # Add tokens from the text field
                    # Image URLs have a fixed token cost
                    elif item.get("type") == "image_url":  # Check if item type is image_url
                        total += 100  # Approximate token cost for image
                else:
                    total += self._count_tokens(str(item))  # Add tokens from the item converted to string
        else:
            total += self._count_tokens(str(content))  # Add tokens from the content converted to string
        
        return total  # Return the total token count

    def _is_conversation_active(self, conversation_id: str) -> bool:
        """Check if a conversation is still active"""
        if conversation_id not in self.conversations:  # Check if conversation ID exists
            return False  # Return False if not found
        
        last_activity = self.conversations[conversation_id].get('last_activity')  # Get the last activity time
        if not last_activity:  # Check if last activity is None
            return False  # Return False if no last activity
            
        return datetime.now() - last_activity < self.conversation_timeout  # Return True if within timeout

    def add_message(self, conversation_id: str, message: Dict) -> None:
        """Add a message to the conversation while managing token limit"""
        # Initialize conversation if it doesn't exist
        if conversation_id not in self.conversations:  # Check if conversation ID exists
            logger.info(f"Creating new conversation {conversation_id}")  # Log creation of new conversation
            self.conversations[conversation_id] = {
                'messages': [],  # Initialize messages list
                'last_activity': datetime.now()  # Set last activity to current time
            }
        
        # Update last activity
        self.conversations[conversation_id]['last_activity'] = datetime.now()  # Update last activity time
        
        # Add new message
        self.conversations[conversation_id]['messages'].append(message)  # Append message to messages list
        logger.info(f"Added message to conversation {conversation_id}. Total messages: {len(self.conversations[conversation_id]['messages'])}")  # Log message addition
        
        # Check total tokens and trim if necessary
        while self._get_total_tokens(conversation_id) > (MAX_TOKENS - TOKEN_BUFFER):  # Check if tokens exceed limit
            # Remove oldest message after system message
            if len(self.conversations[conversation_id]['messages']) > 2:  # Ensure more than two messages exist
                logger.info(f"Trimming conversation {conversation_id} due to token limit")  # Log trimming action
                del self.conversations[conversation_id]['messages'][1]  # Delete the second message
            else:
                break  # Break if only two messages exist

    def _get_total_tokens(self, conversation_id: str) -> int:
        """Get total tokens in a conversation"""
        if conversation_id not in self.conversations:  # Check if conversation ID exists
            return 0  # Return 0 if not found
        
        return sum(self._count_message_tokens(msg) for msg in self.conversations[conversation_id]['messages'])  # Sum tokens for all messages

    def get_messages(self, conversation_id: str) -> List[Dict]:
        """Get all messages for a conversation if it's still active"""
        if not self._is_conversation_active(conversation_id):  # Check if conversation is active
            logger.info(f"Conversation {conversation_id} has timed out or doesn't exist")  # Log timeout or non-existence
            self.clear_conversation(conversation_id)  # Clear conversation if inactive
            return []  # Return empty list
        
        messages = self.conversations.get(conversation_id, {}).get('messages', [])  # Get messages from conversation
        logger.info(f"Retrieved {len(messages)} messages for conversation {conversation_id}")  # Log message retrieval
        return messages  # Return messages list

    def clear_conversation(self, conversation_id: str) -> None:
        """Clear a conversation history"""
        if conversation_id in self.conversations:  # Check if conversation ID exists
            del self.conversations[conversation_id]  # Delete the conversation

# Initialize conversation manager
conversation_manager = ConversationManager()  # Create an instance of ConversationManager

def convert_heic_to_jpeg(image_data: bytes) -> Optional[bytes]:
    """
    Convert HEIC image to JPEG format
    """
    try:
        try:
            from pillow_heif import register_heif_opener  # Import register_heif_opener for HEIC conversion
        except ImportError:
            logger.error("pillow_heif not installed. Please install with: pip install pillow-heif")  # Log error if not installed
            return None  # Return None if import fails
            
        register_heif_opener()  # Register HEIF opener
        
        # Create a BytesIO object from the image data
        image_io = io.BytesIO(image_data)  # Create a byte stream from image data
        
        # Open and convert the image
        with Image.open(image_io) as img:  # Open image using PIL
            # Create a BytesIO object to save the JPEG
            jpeg_io = io.BytesIO()  # Create a byte stream for JPEG
            # Convert to RGB if necessary
            if img.mode != 'RGB':  # Check if image mode is not RGB
                img = img.convert('RGB')  # Convert image to RGB
            # Save as JPEG
            img.save(jpeg_io, format='JPEG', quality=95)  # Save image as JPEG with quality 95
            return jpeg_io.getvalue()  # Return JPEG byte data
    except Exception as e:
        logger.error(f"Error converting HEIC to JPEG: {e}")  # Log conversion error
        return None  # Return None on error

def process_image(image_data: bytes) -> Tuple[bytes, str]:
    """
    Process and validate the image, converting if necessary
    """
    try:
        # Try to open the image with PIL to validate it
        img = Image.open(io.BytesIO(image_data))  # Open image from byte stream
        
        # Handle MPO images (multi-picture format)
        if img.format and img.format.upper() == 'MPO':  # Check if image format is MPO
            logger.info("Converting MPO image to JPEG")  # Log conversion action
            # MPO contains multiple images, we'll use the first one
            img.seek(0)  # Ensure we're at the first image
            # Convert to RGB if necessary
            if img.mode != 'RGB':  # Check if image mode is not RGB
                img = img.convert('RGB')  # Convert image to RGB
            # Save as JPEG
            output = io.BytesIO()  # Create a byte stream for JPEG
            img.save(output, format='JPEG', quality=95)  # Save image as JPEG with quality 95
            return output.getvalue(), 'jpeg'  # Return JPEG byte data and format
        
        # If it's a HEIC/HEIF image, convert it
        if img.format and img.format.upper() in ['HEIC', 'HEIF']:  # Check if image format is HEIC/HEIF
            logger.info("Converting HEIC/HEIF image to JPEG")  # Log conversion action
            converted_data = convert_heic_to_jpeg(image_data)  # Convert HEIC to JPEG
            if converted_data:
                return converted_data, 'jpeg'  # Return converted data and format
            raise ValueError("Failed to convert HEIC/HEIF image")  # Raise error if conversion fails
        
        # For other formats, ensure they're in a web-friendly format
        if img.format and img.format.upper() not in ['JPEG', 'JPG', 'PNG']:  # Check if format is not web-friendly
            logger.info(f"Converting {img.format} image to JPEG")  # Log conversion action
            # Convert to RGB if necessary
            if img.mode != 'RGB':  # Check if image mode is not RGB
                img = img.convert('RGB')  # Convert image to RGB
            # Save as JPEG
            output = io.BytesIO()  # Create a byte stream for JPEG
            img.save(output, format='JPEG', quality=95)  # Save image as JPEG with quality 95
            return output.getvalue(), 'jpeg'  # Return JPEG byte data and format
        
        return image_data, img.format.lower() if img.format else 'jpeg'  # Return original data and format
        
    except Exception as e:
        logger.error(f"Error processing image: {e}")  # Log processing error
        raise ValueError("Invalid image format or corrupted image file")  # Raise error on invalid image

def analyze_plant_image(image_data: bytes, user_message: Optional[str] = None, conversation_id: Optional[str] = None) -> str:
    """
    Analyze a plant image using GPT-4 Turbo with vision capabilities
    """
    try:
        # Process and validate the image
        processed_image, image_format = process_image(image_data)  # Process image and get format
        
        # Convert image to base64
        base64_image = base64.b64encode(processed_image).decode('utf-8')  # Encode image to base64
        
        # Create conversation ID if not provided
        if not conversation_id:  # Check if conversation ID is not provided
            conversation_id = datetime.now().strftime("%Y%m%d_%H%M%S")  # Generate a new conversation ID

        # Get existing conversation or start new one
        if not conversation_manager.get_messages(conversation_id):  # Check if conversation is new
            # Add system message with explicit instructions
            conversation_manager.add_message(conversation_id, {
                "role": "system",
                "content": """You are a plant expert who analyzes plant images and provides detailed care recommendations. 
                IMPORTANT RULES:
                1. You will analyze the plant in the provided image
                2. Store all details about this specific plant in your analysis
                3. For any follow-up questions, use ONLY the information from your analysis
                4. NEVER ask to check databases or plant lists
                5. NEVER ask for plant names - you already analyzed the plant
                6. If unsure about something, refer back to what you observed in the image
                7. Format your responses in markdown"""
            })

            # Add context-setting message
            conversation_manager.add_message(conversation_id, {
                "role": "system",
                "content": "The following conversation will be about a specific plant shown in an image. All questions should be answered in relation to this specific plant only."
            })

        # Prepare the user query with explicit context
        if user_message:  # Check if user message is provided
            query = f"Please analyze this specific plant image. User's comment: {user_message}"  # Include user comment in query
        else:
            query = """Please analyze this specific plant image and provide:
            1. Plant identification (species name and common name)
            2. Assessment of this plant's current condition
            3. Specific care recommendations for this individual plant
            4. Any visible issues or concerns with this particular plant
            Remember: Your analysis and any follow-up questions will be specifically about this plant.
            Please format the response in markdown."""  # Default query for analysis

        # Add user message with image
        conversation_manager.add_message(conversation_id, {
            "role": "user",
            "content": [
                {"type": "text", "text": query},  # Add text query
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_format};base64,{base64_image}",  # Add base64 image URL
                        "detail": "high"  # Set image detail level
                    }
                }
            ]
        })

        # Get conversation history
        messages = conversation_manager.get_messages(conversation_id)  # Retrieve messages for conversation

        # Call GPT-4 Turbo API with conversation history
        response = client.chat.completions.create(
            model=MODEL_NAME,  # Specify model name
            messages=messages,  # Provide conversation messages
            max_tokens=1000,  # Set maximum tokens for response
            temperature=0.7,  # Set response randomness
            seed=123,  # Added for consistency
            response_format={ "type": "text" }  # Specify response format
        )

        # Extract the plant identification from the response
        ai_response = response.choices[0].message.content  # Get content from response
        
        # Add assistant's response with context reinforcement
        conversation_manager.add_message(conversation_id, {
            "role": "assistant",
            "content": ai_response  # Add AI response to conversation
        })
        
        # Add a context reminder message
        conversation_manager.add_message(conversation_id, {
            "role": "system",
            "content": "Remember: The following questions will be about the specific plant that was just analyzed in the image. Do not reference any other plants or garden databases."
        })

        return ai_response  # Return AI response

    except openai.AuthenticationError as e:
        logger.error(f"Authentication error with OpenAI: {e}")  # Log authentication error
        return "I apologize, but there seems to be an issue with the OpenAI API authentication. Please contact support."  # Return error message
    except openai.NotFoundError as e:
        logger.error(f"Model not found error: {e}")  # Log model not found error
        return "I apologize, but the vision analysis service is currently unavailable. Please try again later or contact support."  # Return error message
    except Exception as e:
        logger.error(f"Error analyzing plant image: {e}")  # Log general error
        logger.error(f"Full error: {traceback.format_exc()}")  # Log full traceback
        return "I apologize, but I encountered an error while analyzing the plant image. Please try again."  # Return error message

def validate_image(image_data: bytes) -> bool:
    """
    Validate that the uploaded file is a valid image
    """
    try:
        # Try to process the image
        process_image(image_data)  # Process image to validate
        return True  # Return True if valid
    except Exception:
        return False  # Return False if invalid

def save_image(image_data: bytes, filename: str) -> str:
    """
    Save uploaded image to disk
    """
    try:
        # Process the image before saving
        processed_image, image_format = process_image(image_data)  # Process image and get format
        
        # Create uploads directory if it doesn't exist
        upload_dir = os.path.join('static', 'uploads')  # Define upload directory path
        os.makedirs(upload_dir, exist_ok=True)  # Create directory if it doesn't exist

        # Generate unique filename with correct extension
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")  # Generate timestamp for filename
        base_name = os.path.splitext(filename)[0]  # Get base name of file
        safe_filename = f"{timestamp}_{base_name}.{image_format}"  # Create safe filename with timestamp
        file_path = os.path.join(upload_dir, safe_filename)  # Define full file path

        # Save the processed image
        with open(file_path, 'wb') as f:  # Open file in write-binary mode
            f.write(processed_image)  # Write processed image to file

        return file_path  # Return file path
    except Exception as e:
        logger.error(f"Error saving image: {e}")  # Log error saving image
        raise  # Raise exception on error 