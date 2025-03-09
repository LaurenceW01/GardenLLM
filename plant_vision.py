from openai import OpenAI
import os
import logging
import base64
from typing import Optional, Tuple
from datetime import datetime
import imghdr
import traceback
try:
    from PIL import Image
except ImportError:
    raise ImportError("Please install Pillow with: pip install Pillow")
import io

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

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

def analyze_plant_image(image_data: bytes, user_message: Optional[str] = None) -> str:
    """
    Analyze a plant image using GPT-4 Vision API
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

        # Prepare the messages for the API
        messages = [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": query
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": f"data:image/{image_format};base64,{base64_image}"
                        }
                    }
                ]
            }
        ]

        # Call GPT-4 Vision API
        response = client.chat.completions.create(
            model="gpt-4-vision-preview",
            messages=messages,
            max_tokens=500
        )

        return response.choices[0].message.content

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