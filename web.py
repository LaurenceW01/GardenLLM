"""
Web interface for GardenLLM.
Provides a Flask web application for interacting with the garden assistant.
"""

import os
import logging
import traceback
from datetime import datetime
from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from werkzeug.utils import secure_filename
import base64
from io import BytesIO
from PIL import Image
import requests

from config import openai_client
from plant_operations import add_plant, get_plants, update_plant, delete_plant, search_plants, find_plant_by_id_or_name
from sheets_client import initialize_sheet
from enhanced_weather_service import get_current_weather, get_hourly_forecast
from field_config import get_all_field_names, get_field_alias, get_canonical_field_name
from climate_config import get_climate_context, get_default_location
from chat_response import get_chat_response_with_analyzer_optimized
from conversation_manager import ConversationManager

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = os.getenv('FLASK_SECRET_KEY', 'dev-secret-key')

# Configuration
UPLOAD_FOLDER = 'static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# Ensure upload directory exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    """Check if file extension is allowed"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def save_image_from_url(image_url):
    """Save image from URL to local storage"""
    try:
        response = requests.get(image_url, timeout=10)
        response.raise_for_status()
        
        # Generate filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"plant_{timestamp}.jpg"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        # Save image
        with open(filepath, 'wb') as f:
            f.write(response.content)
        
        return f"/static/uploads/{filename}"
        
    except Exception as e:
        logger.error(f"Error saving image from URL: {e}")
        return None

def process_image_upload(file):
    """Process uploaded image file"""
    try:
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"plant_{timestamp}_{filename}"
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            return f"/static/uploads/{filename}"
    except Exception as e:
        logger.error(f"Error processing image upload: {e}")
    return None

@app.route('/')
def index():
    """Main page with weather and plant list"""
    try:
        # Get weather data using new enhanced service
        current_weather = get_current_weather()
        
        # Build weather summary for display
        weather_summary = ""
        if current_weather:
            weather_summary = f"Current weather: {current_weather.get('temperature', 'Unknown')}°F, {current_weather.get('description', 'Unknown')}"
        
        # Get all plants
        plants = get_plants()
        
        # Get climate context for display
        climate_context = get_climate_context()
        default_location = get_default_location()
        
        return render_template('index.html', 
                             plants=plants, 
                             weather_summary=weather_summary,
                             climate_context=climate_context,
                             default_location=default_location)
    except Exception as e:
        logger.error(f"Error loading index page: {e}")
        flash(f"Error loading page: {str(e)}", 'error')
        return render_template('index.html', plants=[], weather_summary="", climate_context="", default_location="")

@app.route('/add-plant', methods=['GET', 'POST'])
def add_plant_route_hyphen():
    """Add a new plant - hyphenated route for menu compatibility"""
    return add_plant_route()

@app.route('/add_plant', methods=['GET', 'POST'])
def add_plant_route():
    """Add a new plant"""
    if request.method == 'POST':
        try:
            # Get form data from the template format
            plant_name = request.form.get('plantName', '').strip()
            locations = request.form.getlist('location')  # Get all location inputs
            photo_url = request.form.get('photoUrl', '').strip()
            
            # Validate required fields
            if not plant_name:
                flash('Plant name is required', 'error')
                return render_template('add_plant.html')
            
            if not locations or not any(loc.strip() for loc in locations):
                flash('At least one location is required', 'error')
                return render_template('add_plant.html')
            
            # Convert locations to comma-separated string
            location_string = ', '.join([loc.strip() for loc in locations if loc.strip()])
            
            # Process image upload if provided
            if 'photo' in request.files:
                file = request.files['photo']
                if file.filename:
                    photo_url = process_image_upload(file)
            
            # Add plant using centralized field configuration
            result = add_plant(plant_name, "", location_string, photo_url or "")
            
            if result.get('success'):
                flash(f"Successfully added {plant_name} to your garden!", 'success')
                return redirect(url_for('index'))
            else:
                flash(f"Error adding plant: {result.get('error', 'Unknown error')}", 'error')
                
        except Exception as e:
            logger.error(f"Error adding plant: {e}")
            flash(f"Error adding plant: {str(e)}", 'error')
    
    # Get field names for form
    field_names = get_all_field_names()
    return render_template('add_plant.html', field_names=field_names)



@app.route('/weather')
def weather():
    """Weather information page"""
    try:
        # Get weather data using new enhanced service
        current_weather = get_current_weather()
        hourly_forecast = get_hourly_forecast(hours=24)
        
        # Build weather summary from current weather
        weather_summary = ""
        if current_weather:
            weather_summary = f"""
            <h3 class='text-lg font-semibold text-blue-900 mb-3'>Current Weather for Houston</h3>
            <div class='grid grid-cols-1 md:grid-cols-2 gap-4 mb-4'>
                <div class='bg-blue-100 p-3 rounded-lg'><strong>Temperature:</strong> {current_weather.get('temperature', 'Unknown')}°F</div>
                <div class='bg-blue-100 p-3 rounded-lg'><strong>Conditions:</strong> {current_weather.get('description', 'Unknown').title()}</div>
                <div class='bg-blue-100 p-3 rounded-lg'><strong>Humidity:</strong> {current_weather.get('humidity', 'Unknown')}%</div>
                <div class='bg-blue-100 p-3 rounded-lg'><strong>Wind Speed:</strong> {current_weather.get('wind_speed', 'Unknown')} mph</div>
                <div class='bg-blue-100 p-3 rounded-lg'><strong>Pressure:</strong> {current_weather.get('pressure', 'Unknown')} hPa</div>
                <div class='bg-blue-100 p-3 rounded-lg'><strong>Data Source:</strong> Baron Weather API</div>
            </div>
            """
        else:
            weather_summary = """
            <div class='bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4'>
                <h3 class='text-lg font-semibold mb-2'>Weather Service Temporarily Unavailable</h3>
                <p>The Baron Weather API is currently not responding. Please try again later for current weather information.</p>
            </div>
            """
        
        # Generate plant care recommendations based on current weather
        if current_weather:
            temp = current_weather.get('temperature', 75)
            humidity = current_weather.get('humidity', 60)
            description = current_weather.get('description', 'Partly cloudy').lower()
            
            recommendations = []
            if temp < 50:
                recommendations.append("Protect sensitive plants from cold temperatures")
            elif temp > 90:
                recommendations.append("Provide extra water and shade for plants")
            
            if humidity < 40:
                recommendations.append("Consider misting plants or using a humidifier")
            elif humidity > 80:
                recommendations.append("Ensure good air circulation to prevent fungal issues")
            
            if 'rain' in description or 'storm' in description:
                recommendations.append("Reduce watering frequency due to natural precipitation")
            
            if recommendations:
                plant_care_recommendations = f"""
                <h4 class="text-lg font-semibold text-green-800 mb-2">Current Recommendations:</h4>
                <ul class="list-disc list-inside space-y-1 mb-4">
                    {''.join(f'<li class="text-gray-700">{rec}</li>' for rec in recommendations)}
                </ul>
                """
            else:
                plant_care_recommendations = "No specific plant care recommendations for current weather conditions."
        else:
            plant_care_recommendations = """
            <div class='bg-yellow-100 border-l-4 border-yellow-500 text-yellow-700 p-4 mb-4'>
                <h4 class="text-lg font-semibold mb-2">Plant Care Recommendations Unavailable</h4>
                <p>Weather data is currently unavailable. Please check back later for plant care recommendations based on current conditions.</p>
            </div>
            """
        
        climate_context = get_climate_context()
        default_location = get_default_location()
        
        return render_template('weather.html', 
                             weather_summary=weather_summary,
                             plant_care_recommendations=plant_care_recommendations,
                             climate_context=climate_context,
                             default_location=default_location,
                             hourly_rain=hourly_forecast)
    except Exception as e:
        logger.error(f"Error loading weather page: {e}")
        flash(f"Error loading weather information: {str(e)}", 'error')
        return render_template('weather.html', 
                             weather_summary="",
                             plant_care_recommendations="",
                             climate_context="",
                             default_location="",
                             hourly_rain=None)

@app.route('/api/plants', methods=['GET', 'POST'])
def api_plants():
    """API endpoint to get all plants or add a new plant"""
    if request.method == 'GET':
        try:
            plants = get_plants()
            return jsonify({'success': True, 'plants': plants})
        except Exception as e:
            logger.error(f"Error getting plants via API: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500
    
    elif request.method == 'POST':
        try:
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            # Extract data from frontend format
            plant_name = data.get('name', '').strip()
            locations = data.get('locations', [])
            photo_url = data.get('photo_url')
            
            # Validate required fields
            if not plant_name:
                return jsonify({'success': False, 'error': 'Plant name is required'}), 400
            
            # Locations are now optional
            if not locations:
                locations = []
            
            # Convert locations array to comma-separated string
            location_string = ', '.join(locations)
            
            # Use CLI-style add plant functionality with AI care generation
            try:
                # Create detailed plant care guide prompt for OpenAI
                prompt = (
                    f"Create a detailed plant care guide for {plant_name} in Houston, TX. "
                    "Include care requirements, growing conditions, and maintenance tips. "
                    "Focus on practical advice for the specified locations: " + 
                    location_string + "\n\n" +
                    "IMPORTANT: Use EXACTLY the section format shown below with double asterisks and colons:\n" +
                    "**Description:**\n" +
                    "**Light:**\n" +
                    "**Soil:**\n" +
                    "**Watering:**\n" +
                    "**Temperature:**\n" +
                    "**Pruning:**\n" +
                    "**Mulching:**\n" +
                    "**Fertilizing:**\n" +
                    "**Winter Care:**\n" +
                    "**Spacing:**"
                )
                
                # Get plant care information from OpenAI directly using GPT-4 Turbo
                from config import openai_client
                response = openai_client.chat.completions.create(
                    model="gpt-4-turbo-preview",
                    messages=[
                        {"role": "system", "content": "You are a gardening expert assistant. Provide detailed, practical plant care guides with specific instructions. CRITICAL: Use the EXACT section format provided with double asterisks (**Section:**) - do not use markdown headers (###)."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=1000
                )
                response = response.choices[0].message.content or ""
                
                # Parse the care guide response to extract structured data for database storage
                from ai_and_sheets_core import parse_care_guide
                care_details = parse_care_guide(response)
                
                # Debug: Log the parsed care details
                logger.info(f"AI Response: {response[:500]}...")
                logger.info(f"Parsed care details: {care_details}")
                
                # Create comprehensive plant data dictionary with all required fields for database
                from field_config import get_canonical_field_name
                
                # Get canonical field names
                plant_name_field = get_canonical_field_name('Plant Name') or 'Plant Name'
                location_field = get_canonical_field_name('Location') or 'Location'
                description_field = get_canonical_field_name('Description') or 'Description'
                light_field = get_canonical_field_name('Light Requirements') or 'Light Requirements'
                soil_field = get_canonical_field_name('Soil Preferences') or 'Soil Preferences'
                watering_field = get_canonical_field_name('Watering Needs') or 'Watering Needs'
                frost_field = get_canonical_field_name('Frost Tolerance') or 'Frost Tolerance'
                pruning_field = get_canonical_field_name('Pruning Instructions') or 'Pruning Instructions'
                mulching_field = get_canonical_field_name('Mulching Needs') or 'Mulching Needs'
                fertilizing_field = get_canonical_field_name('Fertilizing Schedule') or 'Fertilizing Schedule'
                winterizing_field = get_canonical_field_name('Winterizing Instructions') or 'Winterizing Instructions'
                spacing_field = get_canonical_field_name('Spacing Requirements') or 'Spacing Requirements'
                care_notes_field = get_canonical_field_name('Care Notes') or 'Care Notes'
                photo_url_field = get_canonical_field_name('Photo URL') or 'Photo URL'
                
                plant_data = {
                    plant_name_field: plant_name,
                    location_field: location_string,
                    description_field: care_details.get(description_field, ''),
                    light_field: care_details.get(light_field, ''),
                    soil_field: care_details.get(soil_field, ''),
                    watering_field: care_details.get(watering_field, ''),
                    frost_field: care_details.get(frost_field, ''),
                    pruning_field: care_details.get(pruning_field, ''),
                    mulching_field: care_details.get(mulching_field, ''),
                    fertilizing_field: care_details.get(fertilizing_field, ''),
                    winterizing_field: care_details.get(winterizing_field, ''),
                    spacing_field: care_details.get(spacing_field, ''),
                    care_notes_field: response,
                    photo_url_field: photo_url if photo_url else ""
                }
                
                # Debug: Log the field names being used
                logger.info(f"Field names being used: {list(plant_data.keys())}")
                
                # Add the plant to the Google Sheets database using the legacy update function
                from plant_operations import update_plant_legacy
                if update_plant_legacy(plant_data):
                    return jsonify({
                        'success': True,
                        'message': f"Added {plant_name} to garden with comprehensive care information",
                        'care_guide': response
                    })
                else:
                    return jsonify({'success': False, 'error': f"Error adding plant '{plant_name}' to database"}), 400
                    
            except Exception as e:
                logger.error(f"Error generating care information for {plant_name}: {e}")
                # Fallback to simple add plant if care generation fails
                photo_url_str = photo_url if photo_url else ""
                result = add_plant(plant_name, "", location_string, photo_url_str)
                
                if result.get('success'):
                    care_guide = f"Care guide for {plant_name}:\n\n{plant_name} has been added to your garden in {location_string}. Please research specific care requirements for this plant based on your local climate and growing conditions."
                    
                    return jsonify({
                        'success': True,
                        'message': result.get('message', f'Added {plant_name} to garden (care generation failed)'),
                        'care_guide': care_guide
                    })
                else:
                    return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
                
        except Exception as e:
            logger.error(f"Error adding plant via API: {e}")
            return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/plants/search')
def api_search_plants():
    """API endpoint to search plants"""
    try:
        query = request.args.get('q', '').strip()
        if not query:
            return jsonify({'success': False, 'error': 'Search query is required'}), 400
        
        results = search_plants(query)
        return jsonify({'success': True, 'results': results})
    except Exception as e:
        logger.error(f"Error searching plants via API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/plants/<int:plant_id>', methods=['GET', 'PUT', 'DELETE'])
def api_plant(plant_id):
    """API endpoint for individual plant operations"""
    try:
        if request.method == 'GET':
            plants = get_plants()
            plant = next((p for p in plants if p.get('ID') == str(plant_id)), None)
            if plant:
                return jsonify({'success': True, 'plant': plant})
            else:
                return jsonify({'success': False, 'error': 'Plant not found'}), 404
        
        elif request.method == 'PUT':
            data = request.get_json()
            if not data:
                return jsonify({'success': False, 'error': 'No data provided'}), 400
            
            # Use field_config to validate field names
            valid_fields = get_all_field_names()
            update_data = {k: v for k, v in data.items() if k in valid_fields}
            
            result = update_plant(plant_id, update_data)
            if result.get('success'):
                return jsonify({'success': True, 'message': 'Plant updated successfully'})
            else:
                return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
        
        elif request.method == 'DELETE':
            result = delete_plant(plant_id)
            if result.get('success'):
                return jsonify({'success': True, 'message': 'Plant deleted successfully'})
            else:
                return jsonify({'success': False, 'error': result.get('error', 'Unknown error')}), 400
    
    except Exception as e:
        logger.error(f"Error in plant API operation: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/upload-photo', methods=['POST'])
def api_upload_photo():
    """API endpoint to upload plant photos"""
    try:
        if 'photo' not in request.files:
            return jsonify({'success': False, 'error': 'No photo file provided'}), 400
        
        file = request.files['photo']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400
        
        if file and allowed_file(file.filename):
            photo_url = process_image_upload(file)
            if photo_url:
                return jsonify({
                    'success': True,
                    'photo_url': photo_url
                })
            else:
                return jsonify({'success': False, 'error': 'Failed to save photo'}), 500
        else:
            return jsonify({'success': False, 'error': 'Invalid file type'}), 400
            
    except Exception as e:
        logger.error(f"Error uploading photo: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/weather')
def api_weather():
    """API endpoint for weather information"""
    try:
        # Get weather data using new enhanced service
        current_weather = get_current_weather()
        hourly_forecast = get_hourly_forecast(hours=24)
        
        # Build weather summary
        weather_summary = ""
        if current_weather:
            weather_summary = f"Current weather: {current_weather.get('temperature', 'Unknown')}°F, {current_weather.get('description', 'Unknown')}"
        
        # Generate plant care recommendations
        plant_care_recommendations = "Plant care recommendations based on current weather conditions."
        if current_weather:
            temp = current_weather.get('temperature', 75)
            if temp < 50:
                plant_care_recommendations = "Protect sensitive plants from cold temperatures"
            elif temp > 90:
                plant_care_recommendations = "Provide extra water and shade for plants"
        
        climate_context = get_climate_context()
        default_location = get_default_location()
        
        return jsonify({
            'success': True,
            'weather_summary': weather_summary,
            'plant_care_recommendations': plant_care_recommendations,
            'climate_context': climate_context,
            'default_location': default_location,
            'current_weather': current_weather,
            'hourly_forecast': hourly_forecast
        })
    except Exception as e:
        logger.error(f"Error getting weather via API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint for garden assistant queries"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'error': 'No data provided'}), 400
        
        message = data.get('message', '').strip()
        conversation_id = data.get('conversation_id')
        use_database = data.get('use_database', True)
        
        if not message:
            return jsonify({'success': False, 'error': 'Message is required'}), 400
        
        # Use the optimized chat response function with conversation history
        response = get_chat_response_with_analyzer_optimized(message, conversation_id)
        
        return jsonify({
            'success': True,
            'response': response,
            'conversation_id': conversation_id
        })
        
    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/analyze-plant', methods=['POST'])
def analyze_plant():
    """Enhanced image analysis endpoint for comprehensive plant identification and health assessment"""
    try:
        # Check if image file is present in request
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No image file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No image file selected'}), 400
        
        # Get optional user message and conversation ID
        user_message = request.form.get('message', '').strip()
        conversation_id = request.form.get('conversation_id')
        
        # Validate image file
        if not file.filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp')):
            return jsonify({'success': False, 'error': 'Invalid image format. Please upload a valid image file.'}), 400
        
        # Read image data
        image_data = file.read()
        
        # Validate image data size (max 10MB)
        if len(image_data) > 10 * 1024 * 1024:
            return jsonify({'success': False, 'error': 'Image file too large. Please upload an image smaller than 10MB.'}), 400
        
        # Import the enhanced analyze_plant_image function from plant_vision
        from plant_vision import analyze_plant_image, validate_image
        
        # Validate image format
        if not validate_image(image_data):
            return jsonify({'success': False, 'error': 'Invalid or corrupted image file. Please try a different image.'}), 400
        
        # Analyze the plant image with enhanced capabilities
        response = analyze_plant_image(image_data, user_message, conversation_id)
        
        # Prepare response with metadata
        response_data = {
            'success': True,
            'response': response,
            'conversation_id': conversation_id,
            'analysis_type': 'comprehensive_plant_analysis',
            'features': [
                'plant_identification',
                'health_assessment', 
                'care_recommendations',
                'database_integration'
            ],
            'timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Plant analysis completed successfully for conversation {conversation_id}")
        return jsonify(response_data)
        
    except Exception as e:
        logger.error(f"Error in analyze-plant endpoint: {e}")
        logger.error(f"Full error traceback: {traceback.format_exc()}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/fields')
def api_fields():
    """API endpoint to get field configuration"""
    try:
        field_names = get_all_field_names()
        field_info = {}
        
        for field in field_names:
            alias = get_field_alias(field)
            canonical = get_canonical_field_name(field)
            field_info[field] = {
                'alias': alias,
                'canonical_name': canonical
            }
        
        return jsonify({
            'success': True,
            'fields': field_info,
            'climate_location': get_default_location()
        })
    except Exception as e:
        logger.error(f"Error getting field configuration via API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/conversation-history')
def api_conversation_history():
    """Get conversation history summaries for display"""
    try:
        conversation_manager = ConversationManager()
        
        # Get all active conversations
        conversations = conversation_manager.get_all_conversations()
        
        # Generate summaries for each conversation
        history_summaries = []
        for conversation_id in conversations.keys():
            summary = conversation_manager.get_conversation_history_summary(conversation_id)
            history_summaries.append(summary)
        
        # Sort by last activity (most recent first)
        history_summaries.sort(key=lambda x: x.get('last_activity', datetime.min), reverse=True)
        
        return jsonify({
            'success': True,
            'conversations': history_summaries
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.route('/api/conversation/<conversation_id>/summary')
def api_conversation_summary(conversation_id):
    """Get detailed summary for a specific conversation"""
    try:
        conversation_manager = ConversationManager()
        summary = conversation_manager.get_conversation_history_summary(conversation_id)
        
        return jsonify({
            'success': True,
            'summary': summary
        })
        
    except Exception as e:
        logger.error(f"Error getting conversation summary: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return render_template('404.html'), 404

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {error}")
    return render_template('500.html'), 500

if __name__ == '__main__':
    # Initialize the sheet on startup
    try:
        initialize_sheet()
        logger.info("Sheet initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing sheet: {e}")
    
    # Run the Flask app
    app.run(debug=True, host='0.0.0.0', port=5000)