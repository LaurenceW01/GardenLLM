from openai import OpenAI  # Import the OpenAI library for API interaction
import os  # Import the os module for environment variable access
import logging  # Import logging for logging messages
import base64  # Import base64 for encoding images
from typing import Optional, Tuple, List, Dict, Any  # Import typing for type annotations
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

# Initialize OpenAI client - use the one from config.py if available
try:
    from config import openai_client
    client = openai_client  # Use the client from config.py
except ImportError:
    client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))  # Fallback to creating a new client

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
    Analyze a plant image using GPT-4 Turbo with vision capabilities for comprehensive plant identification and health assessment
    
    This function implements Phase 1 of the Plant Image Analysis Enhancement Plan:
    - Plant identification with common and scientific names
    - Health assessment and condition analysis
    - Treatment recommendations and care advice
    - Database integration for existing plant checks
    - Structured data extraction for plant information
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
            # Add system message with comprehensive plant analysis instructions
            conversation_manager.add_message(conversation_id, {
                "role": "system",
                "content": """You are an expert plant identification and health assessment specialist. Your role is to:

1. **PLANT IDENTIFICATION**: Identify plants with both common and scientific names, providing confidence levels
2. **HEALTH ASSESSMENT**: Analyze plant condition, identify visible issues, diseases, pests, or stress factors
3. **CARE RECOMMENDATIONS**: Provide specific treatment plans and care advice for the identified issues
4. **STRUCTURED ANALYSIS**: Extract comprehensive plant data including:
   - Plant name (common and scientific)
   - Current health status
   - Visible issues or concerns
   - Treatment recommendations
   - Care requirements
   - Growing tips

IMPORTANT RULES:
- Analyze the specific plant(s) in the provided image with extreme attention to detail
- Look carefully at leaf shape, arrangement, color, texture, and any flowers or buds
- Pay attention to the overall growth habit, stem structure, and plant architecture
- If you see distinctive features (like specific leaf patterns, flower colors, growth habits), mention them specifically
- Store all details about this specific plant in your analysis
- For follow-up questions, use ONLY information from your analysis
- NEVER ask to check databases or plant lists
- NEVER ask for plant names - you already analyzed the plant
- If unsure about something, refer back to what you observed in the image
- Format responses in markdown with clear sections
- Provide actionable care recommendations
- Include confidence levels for identifications (high/medium/low)
- If you're uncertain, mention similar plants that could be confused with this one"""
            })

            # Add context-setting message
            conversation_manager.add_message(conversation_id, {
                "role": "system",
                "content": "The following conversation will be about specific plant(s) shown in an image. All questions should be answered in relation to these specific plants only."
            })

        # Prepare the comprehensive analysis query
        if user_message:  # Check if user message is provided
            query = f"""Please analyze this specific plant image comprehensively. User's comment: {user_message}

Please provide:
1. **Plant Identification**: Common name and scientific name with confidence level
2. **Health Assessment**: Current condition and any visible issues
3. **Treatment Plan**: Specific recommendations for any identified problems
4. **Care Advice**: Growing tips and maintenance recommendations

Remember: Your analysis and any follow-up questions will be specifically about this plant."""
        else:
            query = """Please analyze this specific plant image and provide a comprehensive assessment:

## Plant Identification
- Common name and scientific name (be very specific about the exact species/variety)
- Confidence level in identification (high/medium/low)
- Key distinguishing characteristics you observe (leaf shape, color, texture, flowers, growth habit, etc.)
- If you're uncertain, mention similar plants that could be confused with this one

## Health Assessment
- Current condition of the plant
- Any visible issues, diseases, or pests
- Signs of stress or environmental problems
- Overall health rating (excellent/good/fair/poor)

## Treatment Recommendations
- Specific actions to address any issues
- Preventive care measures
- Timeline for treatment

## Care Requirements
- Watering needs
- Light requirements
- Soil preferences
- Temperature tolerance
- Seasonal care considerations

## Growing Tips
- Best practices for this specific plant
- Common mistakes to avoid
- Propagation methods if applicable

IMPORTANT: Look very carefully at the leaf shape, arrangement, color, and any flowers or buds. Pay attention to the overall growth habit and structure. If you see any distinctive features, mention them specifically."""

        # Add user message with image
        conversation_manager.add_message(conversation_id, {
            "role": "user",
            "content": [
                {"type": "text", "text": query},  # Add text query
                {
                    "type": "image_url",
                    "image_url": {
                        "url": f"data:image/{image_format};base64,{base64_image}",  # Add base64 image URL
                        "detail": "high"  # Set image detail level for detailed analysis
                    }
                }
            ]
        })

        # Get conversation history
        messages = conversation_manager.get_messages(conversation_id)  # Retrieve messages for conversation

        # Call GPT-4 Turbo API with conversation history
        response = client.chat.completions.create(
            model=MODEL_NAME,  # Specify model name
            messages=messages,  # type: ignore  # Provide conversation messages
            max_tokens=1500,  # Increased tokens for comprehensive analysis
            temperature=0.7,  # Set response randomness
            seed=123,  # Added for consistency
            response_format={ "type": "text" }  # Specify response format
        )

        # Extract the comprehensive plant analysis from the response
        ai_response = response.choices[0].message.content or ""  # Get content from response with fallback
        
        # Enhance analysis with database integration
        enhanced_response = enhance_analysis_with_database_check(ai_response)  # Enhance with database info
        
        # Add assistant's response to conversation history
        conversation_manager.add_message(conversation_id, {
            "role": "assistant",
            "content": enhanced_response  # Add enhanced response to conversation
        })
        
        # Add a context reminder message for follow-up questions
        conversation_manager.add_message(conversation_id, {
            "role": "system",
            "content": "Remember: The following questions will be about the specific plant(s) that were just analyzed in the image. Do not reference any other plants or garden databases."
        })

        return enhanced_response  # Return enhanced AI response with database integration

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

def check_plant_in_database(plant_name: str) -> Dict[str, Any]:
    """
    Check if an identified plant exists in the user's garden database
    
    This function integrates with existing plant operations to check if a plant
    identified through image analysis already exists in the user's garden.
    
    Args:
        plant_name (str): The plant name to check in the database
        
    Returns:
        Dict[str, Any]: Dictionary containing:
            - exists (bool): Whether the plant exists in the database
            - plant_data (Dict): Plant data if found, empty dict if not
            - message (str): Human-readable message about the plant's status
    """
    try:
        # Import here to avoid circular imports
        from plant_operations import search_plants, get_plant_names_from_database
        
        # Normalize the plant name for better matching
        normalized_name = plant_name.lower().strip()
        
        # Get all plant names from database for comparison
        database_plants = get_plant_names_from_database()
        
        # Check for exact matches first
        exact_matches = [name for name in database_plants if name.lower().strip() == normalized_name]
        
        if exact_matches:
            # Plant exists - get full data
            plant_data = search_plants(exact_matches[0])
            if plant_data:
                return {
                    "exists": True,
                    "plant_data": plant_data[0] if plant_data else {},
                    "message": f"✅ {exact_matches[0]} is already in your garden!",
                    "plant_name": exact_matches[0]
                }
        
        # Check for partial matches
        partial_matches = [name for name in database_plants if normalized_name in name.lower() or name.lower() in normalized_name]
        
        if partial_matches:
            return {
                "exists": False,
                "plant_data": {},
                "message": f"❓ Similar plants found in your garden: {', '.join(partial_matches[:3])}. The identified plant '{plant_name}' is not in your garden yet.",
                "similar_plants": partial_matches[:3]
            }
        
        # No matches found
        return {
            "exists": False,
            "plant_data": {},
            "message": f"🌱 '{plant_name}' is not in your garden yet. Would you like to add it?",
            "plant_name": plant_name
        }
        
    except Exception as e:
        logger.error(f"Error checking plant in database: {e}")  # Log error
        return {
            "exists": False,
            "plant_data": {},
            "message": f"Unable to check if '{plant_name}' exists in your garden due to a database error.",
            "error": str(e)
        }

def extract_plant_names_from_analysis(analysis_text: str) -> List[str]:
    """
    Extract plant names from AI analysis text for database checking
    
    This function parses the AI analysis response to extract plant names
    that can be checked against the user's garden database.
    
    Args:
        analysis_text (str): The AI analysis response text
        
    Returns:
        List[str]: List of extracted plant names
    """
    try:
        import re  # Import regex for pattern matching
        
        plant_names = []  # Initialize list to store plant names
        
        # Common patterns for plant names in analysis text
        patterns = [
            r'(?:identified as|this is|appears to be|looks like)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "This is a Rose"
            r'(?:common name[:\s]+)([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',  # "Common name: Rose"
            r'(?:scientific name[:\s]+)([A-Z][a-z]+\s+[a-z]+)',  # "Scientific name: Rosa sp."
            r'([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)\s+(?:plant|specimen|variety)',  # "Rose plant"
        ]
        
        for pattern in patterns:  # Iterate through patterns
            matches = re.findall(pattern, analysis_text, re.IGNORECASE)  # Find matches
            for match in matches:  # Iterate through matches
                if match and len(match.strip()) > 2:  # Check if match is valid
                    plant_names.append(match.strip())  # Add to list
        
        # Remove duplicates while preserving order
        unique_names = []  # Initialize unique names list
        for name in plant_names:  # Iterate through plant names
            if name not in unique_names:  # Check if name is unique
                unique_names.append(name)  # Add to unique list
        
        logger.info(f"Extracted plant names from analysis: {unique_names}")  # Log extracted names
        return unique_names  # Return unique plant names
        
    except Exception as e:
        logger.error(f"Error extracting plant names from analysis: {e}")  # Log error
        return []  # Return empty list on error

def enhance_analysis_with_database_check(analysis_text: str) -> str:
    """
    Enhance AI analysis with database integration information
    
    This function takes the AI analysis and adds information about whether
    identified plants exist in the user's garden database.
    
    Args:
        analysis_text (str): The original AI analysis text
        
    Returns:
        str: Enhanced analysis with database information
    """
    try:
        # Extract plant names from the analysis
        plant_names = extract_plant_names_from_analysis(analysis_text)  # Extract plant names
        
        if not plant_names:  # Check if no plant names found
            return analysis_text  # Return original analysis
        
        # Check each plant in the database
        database_info = []  # Initialize database info list
        
        for plant_name in plant_names:  # Iterate through plant names
            check_result = check_plant_in_database(plant_name)  # Check plant in database
            database_info.append(check_result)  # Add result to list
        
        # Create enhanced analysis
        enhanced_analysis = analysis_text  # Start with original analysis
        
        # Add database integration section
        enhanced_analysis += "\n\n## Garden Database Integration\n\n"
        
        for info in database_info:  # Iterate through database info
            enhanced_analysis += f"**{info.get('plant_name', 'Unknown Plant')}**: {info['message']}\n\n"
        
        # Add action suggestions
        new_plants = [info for info in database_info if not info['exists']]  # Get new plants
        existing_plants = [info for info in database_info if info['exists']]  # Get existing plants
        
        if new_plants:  # Check if there are new plants
            enhanced_analysis += "**💡 Action Items:**\n"
            enhanced_analysis += "- Consider adding newly identified plants to your garden database\n"
            enhanced_analysis += "- Use the 'Add Plant' feature to track these plants\n\n"
        
        if existing_plants:  # Check if there are existing plants
            enhanced_analysis += "**📋 Garden Management:**\n"
            enhanced_analysis += "- Review care information for existing plants\n"
            enhanced_analysis += "- Update plant records with new observations\n\n"
        
        return enhanced_analysis  # Return enhanced analysis
        
    except Exception as e:
        logger.error(f"Error enhancing analysis with database check: {e}")  # Log error
        return analysis_text  # Return original analysis on error 