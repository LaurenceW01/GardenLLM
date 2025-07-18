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
from conversation_manager import ConversationManager  # Import the centralized ConversationManager

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

# Use the global conversation manager from chat_response
def get_conversation_manager():
    """Get the global conversation manager instance"""
    from chat_response import get_conversation_manager as get_global_manager
    return get_global_manager()

conversation_manager = get_conversation_manager()  # Get the global conversation manager instance

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
- **Common name**: [Provide the common name of the plant]
- **Scientific name**: [Provide the scientific name if known]
- **Confidence level**: [high/medium/low]
- **Key distinguishing characteristics**: [Describe leaf shape, color, texture, flowers, growth habit, etc.]
- **Similar plants**: [If uncertain, mention similar plants that could be confused with this one]

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

IMPORTANT: 
- Look very carefully at the leaf shape, arrangement, color, and any flowers or buds
- Pay attention to the overall growth habit and structure
- If you see any distinctive features, mention them specifically
- In the Plant Identification section, clearly state the plant name using the format "Common name: [Plant Name]" and "Scientific name: [Scientific Name]" if known"""

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
        
        # Very restrictive patterns - only look for clear plant identification
        patterns = [
            # Look for "Common name:" specifically
            r'common name[:\s]+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Look for "Scientific name:" specifically  
            r'scientific name[:\s]+([A-Z][a-z]+\s+[a-z]+)',
            # Look for "This is a [Plant Name]" pattern
            r'this is a\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
            # Look for "Identified as [Plant Name]" pattern
            r'identified as\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)*)',
        ]
        
        # First, try to find the Plant Identification section
        identification_section = re.search(r'##\s*Plant\s*Identification.*?(?=##|$)', analysis_text, re.IGNORECASE | re.DOTALL)
        
        if identification_section:
            # Extract from the identification section only
            section_text = identification_section.group(0)
            logger.info(f"Found Plant Identification section: {section_text[:200]}...")
            
            for pattern in patterns:
                matches = re.findall(pattern, section_text, re.IGNORECASE)
                for match in matches:
                    if match and len(match.strip()) > 2 and len(match.strip()) < 30:  # Shorter max length
                        # Filter out common non-plant words and phrases
                        non_plant_words = ['the', 'this', 'that', 'these', 'those', 'plant', 'specimen', 'variety', 'species', 'genus', 'family', 'one', 'large', 'flower', 'is', 'actually']
                        if match.strip().lower() not in non_plant_words:
                            # Additional check: make sure it doesn't contain common sentence fragments
                            if not any(fragment in match.lower() for fragment in ['one large', 'flower is', 'is actually', 'this specific', 'best practices']):
                                plant_names.append(match.strip())
        else:
            logger.info("No Plant Identification section found, skipping database integration")
            return []
        
        # Remove duplicates while preserving order
        unique_names = []
        for name in plant_names:
            if name not in unique_names:
                unique_names.append(name)
        
        # Additional filtering: only keep names that look like actual plant names
        filtered_names = []
        for name in unique_names:
            # Check if it contains at least one word that could be a plant name
            words = name.split()
            if any(len(word) >= 3 for word in words):  # At least one word with 3+ characters
                # Final check: make sure it's not a sentence fragment
                if not name.lower().startswith(('one ', 'this ', 'that ', 'the ', 'best ', 'common ')):
                    filtered_names.append(name)
        
        logger.info(f"Extracted plant names from analysis: {filtered_names}")
        return filtered_names
        
    except Exception as e:
        logger.error(f"Error extracting plant names from analysis: {e}")
        return []

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
            return analysis_text  # Return original analysis without database integration
        
        # Filter out any names that are too short or look like fragments
        valid_plant_names = []
        for name in plant_names:
            # Only include names that look like actual plant names
            if len(name.strip()) >= 3 and len(name.strip()) <= 30:
                # Check if it contains at least one word that could be a plant name
                words = name.split()
                if any(len(word) >= 3 for word in words):
                    valid_plant_names.append(name.strip())
        
        if not valid_plant_names:  # Check if no valid plant names found
            return analysis_text  # Return original analysis without database integration
        
        # Check each plant in the database
        database_info = []  # Initialize database info list
        
        for plant_name in valid_plant_names:  # Iterate through valid plant names
            check_result = check_plant_in_database(plant_name)  # Check plant in database
            database_info.append(check_result)  # Add result to list
        
        # Create enhanced analysis
        enhanced_analysis = analysis_text  # Start with original analysis
        
        # Add database integration section only if we have valid results
        if database_info:
            # Additional safety check: only proceed if we have reasonable plant names
            valid_plant_names = []
            for info in database_info:
                plant_name = info.get('plant_name', '')
                # Only include names that look like actual plant names
                if (len(plant_name) >= 3 and len(plant_name) <= 30 and 
                    not plant_name.lower().startswith(('one ', 'this ', 'that ', 'the ', 'best ', 'common ')) and
                    not any(fragment in plant_name.lower() for fragment in ['one large', 'flower is', 'is actually', 'this specific', 'best practices'])):
                    valid_plant_names.append(info)
            
            if valid_plant_names:
                enhanced_analysis += "\n\n## Garden Database Integration\n\n"
                
                for info in valid_plant_names:  # Iterate through valid database info
                    enhanced_analysis += f"**{info.get('plant_name', 'Unknown Plant')}**: {info['message']}\n\n"
                
                # Add action suggestions
                new_plants = [info for info in valid_plant_names if not info['exists']]  # Get new plants
                existing_plants = [info for info in valid_plant_names if info['exists']]  # Get existing plants
                
                if new_plants:  # Check if there are new plants
                    enhanced_analysis += "**💡 Action Items:**\n"
                    enhanced_analysis += "- Consider tracking these plants in your garden database\n\n"
                
                if existing_plants:  # Check if there are existing plants
                    enhanced_analysis += "**📋 Garden Management:**\n"
                    enhanced_analysis += "- Review care information for existing plants\n"
                    enhanced_analysis += "- Update plant records with new observations\n\n"
            else:
                logger.info("No valid plant names found, skipping database integration")
        else:
            logger.info("No database info found, skipping database integration")
        
        return enhanced_analysis  # Return enhanced analysis
        
    except Exception as e:
        logger.error(f"Error enhancing analysis with database check: {e}")  # Log error
        return analysis_text  # Return original analysis on error 