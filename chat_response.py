import logging
import time
from typing import List, Dict, Optional, Tuple
import re
from plant_operations import get_plant_data, find_plant_by_id_or_name, update_plant_field
from config import openai_client
from field_config import get_canonical_field_name, is_valid_field, get_all_field_names
from climate_config import get_climate_context, get_default_location
import json
from conversation_manager import ConversationManager

logger = logging.getLogger(__name__)

# Initialize the conversation manager for chat responses (lazy initialization)
_conversation_manager = None

def get_conversation_manager():
    """Get the conversation manager instance (lazy initialization)"""
    global _conversation_manager
    if _conversation_manager is None:
        _conversation_manager = ConversationManager()
    return _conversation_manager

# Phase 1: Import query analyzer (new functionality)
try:
    from query_analyzer import analyze_query, QueryType, is_database_only_query, is_ai_response_required
    QUERY_ANALYZER_AVAILABLE = True
    logger.info("Query analyzer module loaded successfully")
except ImportError as e:
    QUERY_ANALYZER_AVAILABLE = False
    logger.warning(f"Query analyzer module not available: {e}. Using legacy functionality.")

# Phase 5: Performance monitoring
class PerformanceMonitor:
    """Monitor performance metrics for query processing"""
    
    def __init__(self):
        self.metrics = {
            'total_queries': 0,
            'ai_analysis_calls': 0,
            'ai_response_calls': 0,
            'database_only_queries': 0,
            'ai_enhanced_queries': 0,
            'average_analysis_time': 0.0,
            'average_response_time': 0.0,
            'total_processing_time': 0.0,
            'errors': 0
        }
    
    def start_timer(self) -> float:
        """Start a performance timer"""
        return time.time()
    
    def record_metric(self, metric_name: str, value: float = 1.0):
        """Record a performance metric"""
        if metric_name in self.metrics:
            if isinstance(self.metrics[metric_name], (int, float)):
                self.metrics[metric_name] += value
            else:
                self.metrics[metric_name] = value
    
    def update_average(self, metric_name: str, new_value: float, count: int):
        """Update an average metric"""
        if metric_name in self.metrics:
            current_avg = self.metrics[metric_name]
            self.metrics[metric_name] = ((current_avg * (count - 1)) + new_value) / count
    
    def get_metrics(self) -> Dict:
        """Get current performance metrics"""
        return self.metrics.copy()
    
    def log_metrics(self):
        """Log current performance metrics"""
        logger.info(f"Performance Metrics: {self.metrics}")

# Global performance monitor
performance_monitor = PerformanceMonitor()

def extract_search_terms(message: str) -> Optional[str]:
    """Extract plant names from the message using basic pattern matching"""
    # Check for general plant list queries
    general_patterns = [
        r'what plants',
        r'list of plants',
        r'all plants',
        r'which plants',
        r'show all plants',
        r'tell me about the plants'
    ]
    
    # Check for location queries
    location_patterns = [
        r'where (?:is|are) (?:the\s+)?([a-zA-Z\s]+)',
        r'location of (?:the\s+)?([a-zA-Z\s]+)',
        r'where can i find (?:the\s+)?([a-zA-Z\s]+)'
    ]
    
    msg_lower = message.lower()
    
    # Return None with a special flag for general plant queries
    if any(pattern in msg_lower for pattern in general_patterns):
        return '*'
    
    # Check location patterns first
    for pattern in location_patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return match.group(1).strip()
        
    # Common patterns for specific plant queries
    patterns = [
        r'about\s+(?:the\s+)?([a-zA-Z\s]+\b)',
        r'how\s+(?:do\s+)?(?:I\s+)?(?:grow|care\s+for|plant|maintain)\s+(?:a\s+)?([a-zA-Z\s]+\b)',
        r'show\s+me\s+(?:the\s+)?([a-zA-Z\s]+\b)',
        r'what\s+does\s+(?:a\s+)?([a-zA-Z\s]+)\s+look\s+like',
        r'picture\s+of\s+(?:a\s+)?([a-zA-Z\s]+\b)',
        r'photo\s+of\s+(?:a\s+)?([a-zA-Z\s]+\b)',
        r'^([a-zA-Z\s]+)$'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, msg_lower)
        if match:
            return match.group(1).strip()
    return None

def parse_update_command(message: str) -> Optional[Dict]:
    """Parse update plant commands - supports multiple field updates"""
    msg_lower = message.lower()
    
    # Check if this is an update command
    if not msg_lower.startswith('update plant '):
        return None
    
    try:
        # Extract the command parts after "update plant"
        command_parts = message[len('update plant '):].strip()
        
        # Find the plant identifier (first part before any field keyword)
        # Use field_config to get all possible field keywords
        from field_config import FIELD_ALIASES
        field_keywords = list(FIELD_ALIASES.keys())
        
        # Find the first field keyword to identify plant identifier
        first_field_index = -1
        first_field = None
        
        for field in field_keywords:
            index = command_parts.lower().find(field)
            if index != -1 and (first_field_index == -1 or index < first_field_index):
                first_field_index = index
                first_field = field
        
        if first_field_index == -1:
            return None
        
        # Extract plant identifier (everything before the first field)
        plant_identifier = command_parts[:first_field_index].strip()
        
        if not plant_identifier:
            return None
        
        # Parse all field updates in the command
        updates = []
        remaining_command = command_parts[first_field_index:].strip()
        
        while remaining_command:
            # Find the next field keyword
            next_field_index = -1
            next_field = None
            
            for field in field_keywords:
                index = remaining_command.lower().find(field)
                if index != -1 and (next_field_index == -1 or index < next_field_index):
                    next_field_index = index
                    next_field = field
            
            if next_field_index == -1:
                break
            
            # Find the end of this field's value (start of next field or end of command)
            field_start = next_field_index
            field_end = field_start + len(next_field) if next_field else field_start
            
            # Find the next field to determine where this field's value ends
            next_field_start = -1
            for field in field_keywords:
                if field != next_field:  # Don't match the same field
                    index = remaining_command.lower().find(field, field_end)
                    if index != -1 and (next_field_start == -1 or index < next_field_start):
                        next_field_start = index
            
            # Extract the value for this field
            if next_field_start != -1:
                field_value = remaining_command[field_end:next_field_start].strip()
                remaining_command = remaining_command[next_field_start:].strip()
            else:
                field_value = remaining_command[field_end:].strip()
                remaining_command = ""
            
            if field_value:
                updates.append({
                    'field': next_field,
                    'value': field_value
                })
        
        if not updates:
            return None
        
        # Convert updates to use actual field names using field_config
        actual_updates = []
        for update in updates:
            # Use field_config to get canonical field name
            actual_field_name = get_canonical_field_name(update['field'])
            if actual_field_name:
                actual_updates.append({
                    'field_name': actual_field_name,
                    'new_value': update['value']
                })
            else:
                logger.warning(f"Unknown field alias: {update['field']}")
        
        return {
            'plant_identifier': plant_identifier,
            'updates': actual_updates
        }
        
    except Exception as e:
        logger.error(f"Error parsing update command: {e}")
        return None

def get_chat_response(message: str, conversation_id: Optional[str] = None) -> str:
    """Generate a chat response using the unified processing pipeline (Phase 5) with conversation history support"""
    # Phase 5: Use the unified pipeline with performance monitoring and error handling
    # Phase 2: Add conversation history support
    if conversation_id:
        return get_chat_response_with_analyzer_optimized(message, conversation_id)
    else:
        return process_query_with_pipeline(message)

def handle_ai_enhanced_query(query_type: str, plant_references: List[str], original_message: str) -> str:
    """
    Handle AI-enhanced queries (CARE, DIAGNOSIS, ADVICE, GENERAL) with database context.
    
    Args:
        query_type (str): The type of query (CARE, DIAGNOSIS, ADVICE, GENERAL)
        plant_references (List[str]): List of plant names referenced in the query
        original_message (str): The original user message
    
    Returns:
        str: AI-generated response with database context
    """
    logger.info(f"Handling AI-enhanced query: {query_type} for plants: {plant_references}")
    
    try:
        # Get relevant plant data from database
        plant_data = []
        if plant_references:
            for plant_name in plant_references:
                plant_info = get_plant_data([plant_name])
                if isinstance(plant_info, list) and plant_info:
                    plant_data.extend(plant_info)
        
        # Build context for AI
        context = _build_ai_context(query_type, plant_data, original_message)
        
        # Generate AI response
        response = _generate_ai_response(query_type, context, original_message)
        
        # Add photo URLs if available
        response = _add_photo_urls_to_response(response, plant_data)
        
        return response
        
    except Exception as e:
        logger.error(f"Error handling AI-enhanced query: {e}")
        return get_chat_response_legacy(original_message)

def _build_ai_context(query_type: str, plant_data: List[Dict], original_message: str) -> str:
    """
    Build context for AI response based on query type and plant data.
    
    Args:
        query_type (str): The type of query
        plant_data (List[Dict]): Plant data from database
        original_message (str): Original user message
    
    Returns:
        str: Formatted context for AI
    """
    context_parts = []
    
    # Add climate context using climate_config (Houston, TX, USA as default)
    climate_context = get_climate_context()
    context_parts.append(climate_context)
    
    # Add plant-specific context if available
    if plant_data:
        context_parts.append("\nRelevant plants in your garden:")
        for plant in plant_data:
            # Use field_config to get canonical field names
            plant_name_field = get_canonical_field_name('Plant Name')
            plant_name = plant.get(plant_name_field, 'Unknown')
            plant_info = []
            
            # Add relevant plant details based on query type
            if query_type == QueryType.CARE:
                care_fields = [
                    get_canonical_field_name('Light Requirements'),
                    get_canonical_field_name('Watering Needs'),
                    get_canonical_field_name('Soil Preferences'),
                    get_canonical_field_name('Fertilizing Schedule'),
                    get_canonical_field_name('Pruning Instructions'),
                    get_canonical_field_name('Care Notes')
                ]
                for field in care_fields:
                    if field and plant.get(field):
                        plant_info.append(f"{field}: {plant.get(field)}")
            
            elif query_type == QueryType.DIAGNOSIS:
                # Include care info for diagnosis context
                care_fields = [
                    get_canonical_field_name('Light Requirements'),
                    get_canonical_field_name('Watering Needs'),
                    get_canonical_field_name('Soil Preferences'),
                    get_canonical_field_name('Care Notes')
                ]
                for field in care_fields:
                    if field and plant.get(field):
                        plant_info.append(f"{field}: {plant.get(field)}")
            
            elif query_type == QueryType.ADVICE:
                # Include general plant info for advice
                advice_fields = [
                    get_canonical_field_name('Light Requirements'),
                    get_canonical_field_name('Watering Needs'),
                    get_canonical_field_name('Soil Preferences'),
                    get_canonical_field_name('Pruning Instructions'),
                    get_canonical_field_name('Mulching Needs'),
                    get_canonical_field_name('Spacing Requirements')
                ]
                for field in advice_fields:
                    if field and plant.get(field):
                        plant_info.append(f"{field}: {plant.get(field)}")
            
            else:  # GENERAL
                # Include all relevant plant info
                for key, value in plant.items():
                    # Exclude photo URL fields from general info
                    photo_url_field = get_canonical_field_name('Photo URL')
                    raw_photo_url_field = get_canonical_field_name('Raw Photo URL')
                    if value and key not in [photo_url_field, raw_photo_url_field]:
                        plant_info.append(f"{key}: {value}")
            
            if plant_info:
                context_parts.append(f"\n{plant_name}:")
                context_parts.extend([f"  {info}" for info in plant_info])
    
    return "\n".join(context_parts)

def _generate_ai_response(query_type: str, context: str, original_message: str) -> str:
    """
    Generate AI response based on query type and context.
    
    Args:
        query_type (str): The type of query
        context (str): Context information
        original_message (str): Original user message
    
    Returns:
        str: AI-generated response
    """
    # Get climate context for the system prompt
    climate_context = get_climate_context()
    
    # Build system prompt based on query type
    if query_type == QueryType.CARE:
        system_prompt = f"""You are a knowledgeable gardening assistant specializing in plant care. 
        Provide specific, actionable care advice based on the plant information provided. 
        Consider the {get_default_location()} climate and growing conditions. Be encouraging and practical.
        
        Climate Context:
        {climate_context}"""
        
    elif query_type == QueryType.DIAGNOSIS:
        system_prompt = f"""You are a plant health expert. Help diagnose plant problems based on symptoms described. 
        Consider the plant's care requirements and {get_default_location()} climate. Provide both diagnosis and treatment recommendations.
        
        Climate Context:
        {climate_context}"""
        
    elif query_type == QueryType.ADVICE:
        system_prompt = f"""You are an experienced gardener providing practical advice. 
        Give specific, actionable recommendations based on the plant information and {get_default_location()} growing conditions. 
        Focus on best practices and proven techniques.
        
        Climate Context:
        {climate_context}"""
        
    else:  # GENERAL
        system_prompt = f"""You are a helpful gardening assistant with expertise in {get_default_location()} gardening. 
        Provide informative, practical answers to gardening questions. 
        Consider the local climate and growing conditions in your responses.
        
        Climate Context:
        {climate_context}"""
    
    # Build user prompt
    user_prompt = f"""Context: {context}

User question: {original_message}

Please provide a helpful, informative response that addresses the user's question."""
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content or "I'm sorry, I couldn't generate a response at this time."
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        return "I'm sorry, I encountered an error while processing your request. Please try again."

def _add_photo_urls_to_response(response: str, plant_data: List[Dict]) -> str:
    """
    Add photo URLs to the AI response if available.
    
    Args:
        response (str): The AI-generated response
        plant_data (List[Dict]): Plant data from database
    
    Returns:
        str: Response with photo URLs added
    """
    if not plant_data:
        return response
    
    # Use field_config to get canonical field names
    raw_photo_url_field = get_canonical_field_name('Raw Photo URL')
    
    photo_urls = []
    for plant in plant_data:
        # Use field_config to get canonical field names
        plant_name_field = get_canonical_field_name('Plant Name')
        plant_name = plant.get(plant_name_field, 'Unknown Plant')
        raw_photo_url = plant.get(raw_photo_url_field, '')
        
        if raw_photo_url:
            photo_urls.append(f"{plant_name}: {raw_photo_url}")
    
    if photo_urls:
        response += "\n\nPhoto URLs:\n" + "\n".join(photo_urls)
    
    return response

def handle_database_only_query(query_type: str, plant_references: List[str], original_message: str) -> str:
    """
    Handle database-only queries (LOCATION, PHOTO, LIST) directly from database.
    
    Args:
        query_type (str): The type of query (LOCATION, PHOTO, LIST)
        plant_references (List[str]): List of plant names referenced in the query
        original_message (str): The original user message
    
    Returns:
        str: Formatted response from database data
    """
    logger.info(f"Handling database-only query: {query_type} for plants: {plant_references}")
    
    try:
        if query_type == QueryType.LIST:
            return handle_list_query()
        elif query_type == QueryType.LOCATION:
            return handle_location_query(plant_references)
        elif query_type == QueryType.PHOTO:
            return handle_photo_query(plant_references)
        # LOCATION_PLANTS queries are now handled by AI-driven approach in main chat handler
        else:
            logger.warning(f"Unknown database-only query type: {query_type}")
            return get_chat_response_legacy(original_message)
            
    except Exception as e:
        logger.error(f"Error handling database-only query: {e}")
        return get_chat_response_legacy(original_message)

def handle_list_query() -> str:
    """
    Handle queries asking for a list of all plants.
    
    Returns:
        str: Formatted list of all plants in the database
    """
    logger.info("Handling list query")
    
    try:
        # Get all plants from database
        plant_data = get_plant_data([])  # Empty list returns all plants
        
        if not isinstance(plant_data, list):
            return "I encountered an error while retrieving the plant list. Please try again."
        
        if not plant_data:
            return "There are currently no plants in the database."
        
        # Extract plant names
        plant_names = [plant.get('Plant Name', '') for plant in plant_data if plant.get('Plant Name')]
        
        if not plant_names:
            return "There are currently no plants in the database."
        
        # Format response
        response = f"You have {len(plant_names)} plants in your garden:\n\n"
        response += "\n".join(f"• {name}" for name in plant_names)
        
        logger.info(f"List query response: {len(plant_names)} plants listed")
        return response
        
    except Exception as e:
        logger.error(f"Error handling list query: {e}")
        return "I encountered an error while retrieving your plant list. Please try again."

def handle_location_query(plant_references: List[str]) -> str:
    """
    Handle queries asking for plant locations.
    
    Args:
        plant_references (List[str]): List of plant names to look up
    
    Returns:
        str: Formatted location information
    """
    logger.info(f"Handling location query for plants: {plant_references}")
    
    if not plant_references:
        return "I couldn't identify which plants you're asking about. Could you please specify the plant names?"
    
    try:
        response_parts = []
        
        for plant_name in plant_references:
            # Get plant data from database
            plant_data = get_plant_data([plant_name])
            
            if isinstance(plant_data, str):  # Error message
                response_parts.append(f"Error looking up {plant_name}: {plant_data}")
                continue
            
            if not plant_data:
                response_parts.append(f"I couldn't find any plants matching '{plant_name}' in the database.")
                continue
            
            # Process each matching plant
            for plant in plant_data:
                plant_name_actual = plant.get('Plant Name', plant_name)
                location = plant.get('Location', '')
                
                if location:
                    response_parts.append(f"The {plant_name_actual} is located in the {location}.")
                else:
                    response_parts.append(f"I found {plant_name_actual}, but its location is not specified.")
                
                # Add photo if available
                raw_photo_url = plant.get('Raw Photo URL', '')
                if raw_photo_url:
                    if 'photos.google.com' in raw_photo_url:
                        raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                    response_parts.append(f"You can see a photo of the {plant_name_actual} here: {raw_photo_url}")
        
        if not response_parts:
            return "I couldn't find location information for the plants you mentioned."
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error handling location query: {e}")
        return "I encountered an error while looking up plant locations. Please try again."

def handle_photo_query(plant_references: List[str]) -> str:
    """
    Handle photo queries for specific plants.
    
    Args:
        plant_references (List[str]): List of plant names to get photos for
    
    Returns:
        str: Formatted response with photo URLs
    """
    try:
        # Get plant data for the referenced plants
        plant_data = []
        for plant_name in plant_references:
            plant_info = get_plant_data([plant_name])
            if isinstance(plant_info, list) and plant_info:
                plant_data.extend(plant_info)
        
        if not plant_data:
            return "I couldn't find any plants matching your request in your garden database."
        
        # Use field_config to get canonical field names
        raw_photo_url_field = get_canonical_field_name('Raw Photo URL')
        
        response_parts = []
        for plant in plant_data:
            # Use field_config to get canonical field names
            plant_name_field = get_canonical_field_name('Plant Name')
            plant_name = plant.get(plant_name_field, 'Unknown Plant')
            raw_photo_url = plant.get(raw_photo_url_field, '')
            
            if raw_photo_url:
                response_parts.append(f"**{plant_name}**: {raw_photo_url}")
            else:
                response_parts.append(f"**{plant_name}**: No photo available")
        
        if response_parts:
            return "Here are the photos for your plants:\n\n" + "\n".join(response_parts)
        else:
            return "I found the plants but no photos are available for them."
        
    except Exception as e:
        logger.error(f"Error handling photo query: {e}")
        return "I encountered an error while retrieving the photos."

def handle_location_plants_query(location_references: List[str]) -> str:
    """
    Handle queries asking for plants in specific locations.
    
    Args:
        location_references (List[str]): List of location names to search for
    
    Returns:
        str: Formatted response with plants found in the specified locations
    """
    logger.info(f"Handling location plants query for locations: {location_references}")
    
    if not location_references:
        return "I couldn't identify which locations you're asking about. Could you please specify the location names?"
    
    try:
        # Get plants by location from database
        from plant_operations import get_plants_by_location
        plant_data = get_plants_by_location(location_references)
        
        if isinstance(plant_data, str):  # Error message
            return f"Error looking up plants in locations {location_references}: {plant_data}"
        
        if not plant_data:
            locations_str = ", ".join(location_references)
            return f"I couldn't find any plants in the following locations: {locations_str}."
        
        # Format the response
        response_parts = []
        locations_str = ", ".join(location_references)
        response_parts.append(f"Here are the plants I found in {locations_str}:")
        
        # Group plants by location for better organization
        plants_by_location = {}
        for plant in plant_data:
            plant_name = plant.get('Plant Name', 'Unknown Plant')
            location = plant.get('Location', 'Unknown Location')
            
            if location not in plants_by_location:
                plants_by_location[location] = []
            plants_by_location[location].append(plant_name)
        
        # Add plants grouped by location
        for location, plants in plants_by_location.items():
            if len(plants) == 1:
                response_parts.append(f"• {location}: {plants[0]}")
            else:
                plants_list = ", ".join(plants)
                response_parts.append(f"• {location}: {plants_list}")
        
        # Add photo URLs if available
        photo_plants = []
        for plant in plant_data:
            plant_name = plant.get('Plant Name', 'Unknown Plant')
            raw_photo_url = plant.get('Raw Photo URL', '')
            if raw_photo_url:
                if 'photos.google.com' in raw_photo_url:
                    raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                photo_plants.append(f"{plant_name}: {raw_photo_url}")
        
        if photo_plants:
            response_parts.append("\nPhotos available for:")
            response_parts.extend([f"• {photo}" for photo in photo_plants])
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error handling location plants query: {e}")
        return "I encountered an error while looking up plants in those locations. Please try again."

def ai_match_locations(user_query: str, valid_locations: List[str]) -> List[str]:
    """
    Use AI to match user query to valid locations from the database.
    
    Args:
        user_query (str): The user's query (e.g., "what plants are in the arboretum")
        valid_locations (List[str]): List of valid locations from the database
    
    Returns:
        List[str]: List of matched location names
    """
    logger.info(f"AI matching locations for query: {user_query}")
    logger.info(f"Valid locations: {valid_locations}")
    
    try:
        # Build the prompt for AI location matching
        locations_text = ", ".join(valid_locations)
        prompt = f"""
You are a gardening assistant that matches user queries to valid garden locations.

Available locations in the garden database: {locations_text}

User query: "{user_query}"

Analyze the user query and return ONLY a JSON array of location names that match what the user is asking about. 

IMPORTANT MATCHING RULES:
1. Be flexible with partial matches - "rear middle" should match "Rear middle bed" or "rear middle bed"
2. "arboretum" should match "Arboretum", "Basket arboretum", "Right Arboretum", "arboretum"
3. "kitchen bed" should match "Kitchen Bed", "kitchen bed", "Basket kitchen bed"
4. "office bed" should match "Office Bed", "office bed", "basket office bed"
5. "rear left" should match "Rear Left Bed", "rear left bed", "Rear left"
6. "rear right" should match "Rear Right path", "rear right bed", "Rear right"
7. "middle bed" should match "Middle Bed", "middle bed"
8. "bocce" should match "Bocce Bed", "Bocce Path", "bocce bed", "bocce path"
9. "patio" should match "Patio"
10. "pool path" should match "Pool Path", "pool path"

Examples:
- "what plants are in the arboretum" → ["Arboretum", "Basket arboretum", "Right Arboretum", "arboretum"]
- "how many plants in the rear left bed" → ["Rear Left Bed", "rear left bed", "Rear left"]
- "show me plants in the kitchen bed and office bed" → ["Kitchen Bed", "kitchen bed", "Basket kitchen bed", "Office Bed", "office bed", "basket office bed"]
- "what plants are in the rear middle" → ["Rear middle bed", "rear middle bed", "Rear Middle Bed"]
- "what's in the garden" → [] (too vague)

Return ONLY the JSON array, no other text:
"""
        
        # Call OpenAI for location matching
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a gardening assistant that matches user queries to valid garden locations. Be flexible with partial matches and return only JSON arrays."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content
        if not ai_response:
            logger.warning("Empty AI response for location matching")
            return []
        
        # Parse the JSON response
        try:
            # Clean up the response
            cleaned_response = ai_response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            matched_locations = json.loads(cleaned_response.strip())
            
            if not isinstance(matched_locations, list):
                logger.warning(f"AI returned non-list response: {matched_locations}")
                return []
            
            # Validate that all matched locations exist in the valid locations list
            valid_matches = [loc for loc in matched_locations if loc in valid_locations]
            
            logger.info(f"AI matched locations: {matched_locations}")
            logger.info(f"Valid matches: {valid_matches}")
            
            # If AI didn't find matches, try fallback matching
            if not valid_matches:
                logger.info("No AI matches found, trying fallback matching")
                valid_matches = fallback_location_matching(user_query, valid_locations)
            
            return valid_matches
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse AI location response: {e}")
            logger.error(f"Raw response: {ai_response}")
            # Try fallback matching if JSON parsing fails
            logger.info("JSON parsing failed, trying fallback matching")
            return fallback_location_matching(user_query, valid_locations)
            
    except Exception as e:
        logger.error(f"Error in AI location matching: {e}")
        # Try fallback matching if AI call fails
        logger.info("AI call failed, trying fallback matching")
        return fallback_location_matching(user_query, valid_locations)

def fallback_location_matching(user_query: str, valid_locations: List[str]) -> List[str]:
    """
    Fallback location matching using simple text matching when AI fails.
    
    Args:
        user_query (str): The user's query
        valid_locations (List[str]): List of valid locations
    
    Returns:
        List[str]: List of matched location names
    """
    logger.info(f"Using fallback location matching for query: {user_query}")
    
    query_lower = user_query.lower()
    matches = []
    
    # Common location patterns and their variations
    location_patterns = {
        'arboretum': ['arboretum', 'basket arboretum', 'right arboretum'],
        'rear middle': ['rear middle bed', 'rear middle', 'rear middle bed photo'],
        'rear left': ['rear left bed', 'rear left'],
        'rear right': ['rear right bed', 'rear right', 'rear right path'],
        'middle bed': ['middle bed'],
        'kitchen bed': ['kitchen bed', 'basket kitchen bed'],
        'office bed': ['office bed', 'basket office bed'],
        'bocce': ['bocce bed', 'bocce path'],
        'patio': ['patio'],
        'pool path': ['pool path'],
        'ivy wave wall': ['ivy wave wall', 'basket ivy wave wall'],
        'kitchen wall': ['kitchen wall', 'basket kitchen wall']
    }
    
    # Check for pattern matches
    for pattern, variations in location_patterns.items():
        if pattern in query_lower:
            for variation in variations:
                # Find exact matches in valid locations (case-insensitive)
                for valid_loc in valid_locations:
                    if valid_loc.lower() == variation.lower():
                        if valid_loc not in matches:
                            matches.append(valid_loc)
    
    logger.info(f"Fallback matches found: {matches}")
    return matches

def handle_location_plants_query_with_ai(user_query: str) -> str:
    """
    Handle location-based plant queries using AI for location matching.
    
    Args:
        user_query (str): The user's query (e.g., "what plants are in the arboretum")
    
    Returns:
        str: Formatted response with plants found in the matched locations
    """
    logger.info(f"Handling location plants query with AI: {user_query}")
    
    try:
        # Get all unique locations from the database
        from plant_operations import get_location_names_from_database
        valid_locations = get_location_names_from_database()
        
        if not valid_locations:
            return "I couldn't find any location information in the database."
        
        # Use AI to match the user query to valid locations
        matched_locations = ai_match_locations(user_query, valid_locations)
        
        if not matched_locations:
            return f"I couldn't identify which locations you're asking about in your query: '{user_query}'. Please try being more specific about the location."
        
        # Get plants for the matched locations
        from plant_operations import get_plants_by_location
        plant_data = get_plants_by_location(matched_locations)
        
        if isinstance(plant_data, str):  # Error message
            return f"Error looking up plants in locations {matched_locations}: {plant_data}"
        
        if not plant_data:
            locations_str = ", ".join(matched_locations)
            return f"I couldn't find any plants in the following locations: {locations_str}."
        
        # Format the response - collect all unique plant names
        response_parts = []
        locations_str = ", ".join(matched_locations)
        response_parts.append(f"Here are the plants I found in {locations_str}:")
        
        # Collect all unique plant names
        unique_plants = set()
        for plant in plant_data:
            plant_name = plant.get('Plant Name', 'Unknown Plant')
            if plant_name and plant_name != 'Unknown Plant':
                unique_plants.add(plant_name)
        
        # Sort plant names alphabetically for better presentation
        sorted_plants = sorted(list(unique_plants))
        
        if len(sorted_plants) == 1:
            response_parts.append(f"• {sorted_plants[0]}")
        else:
            # Format as a simple list
            for plant_name in sorted_plants:
                response_parts.append(f"• {plant_name}")
        
        # Add photo URLs for each unique plant
        for plant_name in sorted_plants:
            # Find the first plant with this name to get the photo
            for plant in plant_data:
                if plant.get('Plant Name') == plant_name:
                    raw_photo_url = plant.get('Raw Photo URL', '')
                    if raw_photo_url:
                        # Format Google Photos URL if needed
                        if 'photos.google.com' in raw_photo_url:
                            raw_photo_url = raw_photo_url.split('?')[0] + '?authuser=0'
                        response_parts.append(f"\nYou can see a photo of the {plant_name} here: {raw_photo_url}")
                    break  # Found the first occurrence, move to next plant
        
        return "\n".join(response_parts)
        
    except Exception as e:
        logger.error(f"Error handling location plants query with AI: {e}")
        return "I encountered an error while looking up plants by location. Please try again."

def get_chat_response_with_analyzer(message: str) -> str:
    """Generate a chat response using the new query analyzer (Phase 4)"""
    logger.info(f"Processing message with analyzer: {message}")
    
    try:
        # Check for location-based plant queries first (AI-driven approach)
        msg_lower = message.lower()
        location_patterns = [
            'what plants are in', 'how many plants in', 'show me plants in',
            'plants in the', 'plants in', 'what\'s in the', 'whats in the',
            'how many different plants in', 'list plants in', 'plants located in'
        ]
        
        is_location_plants_query = any(pattern in msg_lower for pattern in location_patterns)
        
        if is_location_plants_query:
            logger.info(f"Detected location-based plant query: {message}")
            return handle_location_plants_query_with_ai(message)
        
        # Analyze the query using AI
        analysis_result = analyze_query(message)
        logger.info(f"Query analysis result: {analysis_result}")
        
        query_type = analysis_result['query_type']
        plant_references = analysis_result['plant_references']
        requires_ai_response = analysis_result['requires_ai_response']
        
        logger.info(f"Phase 4: Query classified as {query_type} with confidence {analysis_result['confidence']}")
        logger.info(f"Phase 4: Plant references found: {plant_references}")
        logger.info(f"Phase 4: Requires AI response: {requires_ai_response}")
        
        # Phase 4: Handle database-only queries directly
        if not requires_ai_response:
            logger.info(f"Phase 4: Processing database-only query type: {query_type}")
            return handle_database_only_query(query_type, plant_references, message)
        
        # Phase 4: Handle AI-enhanced queries with database context
        logger.info(f"Phase 4: Processing AI-enhanced query type: {query_type}")
        return handle_ai_enhanced_query(query_type, plant_references, message)
        
    except Exception as e:
        logger.error(f"Error in query analyzer: {e}")
        # Fall back to legacy method
        return get_chat_response_legacy(message)

def get_chat_response_legacy(message: str) -> str:
    """Legacy chat response function for fallback"""
    try:
        # Get climate context for the system prompt
        climate_context = get_climate_context()
        
        system_prompt = f"""You are a knowledgeable gardening expert with access to the user's garden database. 
        You can answer general gardening questions and provide advice on any plant species. 
        You may reference the user's garden database if relevant, but you're not limited to plants in their database. 
        You can also provide weather-aware gardening advice when appropriate. 
        Focus on providing practical, actionable gardening advice.

        Climate Context:
        {climate_context}

        When referencing the garden database, use these field names: {', '.join(get_all_field_names())}.

        ADD/UPDATE PLANT OPERATIONS (EXACT CURRENT FUNCTIONALITY):
        - Command format: "Add/Update plant [plant name]" or "Add/Update [plant name]"
        - Only Plant Name is required; optional fields are ONLY location and photo URL
        - AI automatically generates comprehensive care information that gets parsed and loaded/updated in garden database
        - Automatically suggest climate-appropriate care requirements (default: {get_default_location()})
        - Support both Photo URL and Raw Photo URL fields
        - Show confirmation summary before adding/updating to database"""

        # Get weather context if available
        try:
            from weather_context_integration import get_weather_context_messages
            weather_context = get_weather_context_messages()
            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(weather_context)
            messages.append({"role": "user", "content": message})
            logger.info("Added weather context to legacy chat response")
        except ImportError:
            # Fallback to original behavior if weather context not available
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": message}
            ]
            logger.debug("Weather context not available for legacy chat response")

        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content or "I'm sorry, I couldn't generate a response at this time."
        
    except Exception as e:
        logger.error(f"Error in legacy chat response: {e}")
        return "I'm sorry, I encountered an error while processing your request."

# Phase 5: Unified query processing pipeline
def process_query_with_pipeline(message: str) -> str:
    """
    Unified query processing pipeline with performance monitoring and error handling.
    
    This is the main entry point for all queries, providing:
    - Performance monitoring
    - Comprehensive error handling
    - Graceful degradation
    - Two-AI-call workflow optimization
    
    Args:
        message (str): User's query message
    
    Returns:
        str: Response to user query
    """
    start_time = performance_monitor.start_timer()
    performance_monitor.record_metric('total_queries')
    
    try:
        logger.info(f"Phase 5: Processing query with unified pipeline: {message}")
        
        # Check if query analyzer is available
        if not QUERY_ANALYZER_AVAILABLE:
            logger.warning("Query analyzer not available, using legacy processing")
            return get_chat_response_legacy(message)
        
        # Phase 5: Use enhanced processing with performance monitoring
        response = get_chat_response_with_analyzer_optimized(message)
        
        # Record successful processing time
        processing_time = time.time() - start_time
        performance_monitor.record_metric('total_processing_time', processing_time)
        
        logger.info(f"Phase 5: Query processed successfully in {processing_time:.2f}s")
        return response
        
    except Exception as e:
        # Record error and attempt graceful degradation
        performance_monitor.record_metric('errors')
        logger.error(f"Phase 5: Error in unified pipeline: {e}")
        
        # Graceful degradation: try legacy method
        try:
            logger.info("Phase 5: Attempting graceful degradation with legacy method")
            return get_chat_response_legacy(message)
        except Exception as legacy_error:
            logger.error(f"Phase 5: Legacy method also failed: {legacy_error}")
            return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."

def get_chat_response_with_analyzer_optimized(message: str, conversation_id: Optional[str] = None) -> str:
    """
    Optimized version of chat response with analyzer, including performance monitoring and conversation history.
    
    Args:
        message (str): User's query message
        conversation_id (str, optional): Conversation ID for maintaining context
    
    Returns:
        str: Response to user query
    """
    analysis_start = performance_monitor.start_timer()
    
    try:
        # Add user message to conversation history if conversation_id provided
        if conversation_id:
            user_message = {"role": "user", "content": message}
            get_conversation_manager().add_message(conversation_id, user_message)
            logger.info(f"Phase 2: Added user message to conversation {conversation_id}")
        
        # Check for location-based plant queries first (AI-driven approach)
        msg_lower = message.lower()
        location_patterns = [
            'what plants are in', 'how many plants in', 'show me plants in',
            'plants in the', 'plants in', 'what\'s in the', 'whats in the',
            'how many different plants in', 'list plants in', 'plants located in'
        ]
        
        is_location_plants_query = any(pattern in msg_lower for pattern in location_patterns)
        
        if is_location_plants_query:
            logger.info(f"Phase 5: Detected location-based plant query: {message}")
            response = handle_location_plants_query_with_ai(message)
            # Add response to conversation history
            if conversation_id:
                ai_message = {"role": "assistant", "content": response}
                get_conversation_manager().add_message(conversation_id, ai_message)
            return response
        
        # Step 1: AI Analysis (First AI call)
        logger.info("Phase 5: Starting AI analysis (first AI call)")
        analysis_result = analyze_query(message)
        analysis_time = time.time() - analysis_start
        
        # Record analysis metrics
        performance_monitor.record_metric('ai_analysis_calls')
        performance_monitor.update_average('average_analysis_time', analysis_time, 
                                         performance_monitor.metrics['ai_analysis_calls'])
        
        logger.info(f"Phase 5: AI analysis completed in {analysis_time:.2f}s")
        logger.info(f"Phase 5: Analysis result: {analysis_result}")
        
        query_type = analysis_result['query_type']
        plant_references = analysis_result['plant_references']
        requires_ai_response = analysis_result['requires_ai_response']
        
        # Step 2: Route to appropriate processor
        if not requires_ai_response:
            # Database-only processing
            performance_monitor.record_metric('database_only_queries')
            logger.info(f"Phase 5: Processing database-only query type: {query_type}")
            response = handle_database_only_query(query_type, plant_references, message)
            # Add response to conversation history
            if conversation_id:
                ai_message = {"role": "assistant", "content": response}
                get_conversation_manager().add_message(conversation_id, ai_message)
            return response
        else:
            # AI-enhanced processing (Second AI call)
            performance_monitor.record_metric('ai_enhanced_queries')
            logger.info(f"Phase 5: Processing AI-enhanced query type: {query_type}")
            response = handle_ai_enhanced_query_optimized(query_type, plant_references, message, conversation_id)
            # Add response to conversation history
            if conversation_id:
                ai_message = {"role": "assistant", "content": response}
                get_conversation_manager().add_message(conversation_id, ai_message)
            return response
            
    except Exception as e:
        logger.error(f"Phase 5: Error in optimized analyzer: {e}")
        raise

def handle_ai_enhanced_query_optimized(query_type: str, plant_references: List[str], message: str, conversation_id: Optional[str] = None) -> str:
    """
    Optimized AI-enhanced query processing with performance monitoring and conversation history.
    
    Args:
        query_type (str): Type of query (CARE, DIAGNOSIS, ADVICE, GENERAL)
        plant_references (List[str]): Plant names referenced in query
        message (str): Original user message
        conversation_id (str, optional): Conversation ID for maintaining context
    
    Returns:
        str: AI-generated response with database context
    """
    response_start = performance_monitor.start_timer()
    
    try:
        # Build enhanced context with plant data
        context = build_ai_context_with_plants(query_type, plant_references, message)
        
        # Generate AI response with context and conversation history
        ai_response = generate_ai_response_with_context(query_type, context, message, conversation_id)
        
        response_time = time.time() - response_start
        
        # Record response metrics
        performance_monitor.record_metric('ai_response_calls')
        performance_monitor.update_average('average_response_time', response_time,
                                         performance_monitor.metrics['ai_response_calls'])
        
        logger.info(f"Phase 5: AI response generated in {response_time:.2f}s")
        return ai_response
        
    except Exception as e:
        logger.error(f"Phase 5: Error in AI-enhanced processing: {e}")
        # Fallback to simple AI response without context
        try:
            logger.info("Phase 5: Attempting fallback AI response")
            return generate_fallback_ai_response(message)
        except Exception as fallback_error:
            logger.error(f"Phase 5: Fallback AI response also failed: {fallback_error}")
            raise

def build_ai_context_with_plants(query_type: str, plant_references: List[str], message: str) -> str:
    """
    Build enhanced AI context with plant database data and Houston climate.
    
    Args:
        query_type (str): Type of query
        plant_references (List[str]): Plant names from analysis
        message (str): Original user message
    
    Returns:
        str: Enhanced context for AI
    """
    try:
        # Get plant data from database
        plant_data = []
        if plant_references:
            plant_data = get_plant_data(plant_references)
        
        # Build context based on query type
        context_parts = []
        
        # Add climate context
        context_parts.append("Location: Houston, Texas (Zone 9a)")
        context_parts.append("Climate: Humid subtropical with hot summers and mild winters")
        context_parts.append("Growing season: Year-round with peak in spring/fall")
        
        # Add plant-specific context
        if plant_data:
            context_parts.append("\nRelevant plants in your garden:")
            for plant in plant_data:
                plant_info = f"- {plant.get('name', 'Unknown')}"
                if plant.get('location'):
                    plant_info += f" (Location: {plant['location']})"
                if plant.get('care_info'):
                    plant_info += f" - Care: {plant['care_info'][:100]}..."
                context_parts.append(plant_info)
        
        # Add query-specific context
        if query_type == QueryType.CARE:
            context_parts.append("\nFocus: Plant care and maintenance advice")
        elif query_type == QueryType.DIAGNOSIS:
            context_parts.append("\nFocus: Plant health diagnosis and problem-solving")
        elif query_type == QueryType.ADVICE:
            context_parts.append("\nFocus: Gardening advice and best practices")
        elif query_type == QueryType.GENERAL:
            context_parts.append("\nFocus: General gardening information")
        
        return "\n".join(context_parts)
        
    except Exception as e:
        logger.error(f"Error building AI context: {e}")
        return "Location: Houston, Texas (Zone 9a)"

def generate_ai_response_with_context(query_type: str, context: str, message: str, conversation_id: Optional[str] = None) -> str:
    """
    Generate AI response with enhanced context and conversation history.
    
    Args:
        query_type (str): Type of query
        context (str): Enhanced context with plant data
        message (str): Original user message
        conversation_id (str, optional): Conversation ID for maintaining context
    
    Returns:
        str: AI-generated response
    """
    try:
        # Get conversation manager for Phase 4 enhancements
        conversation_manager = get_conversation_manager()
        
        # Get conversation context for enhanced system prompt
        conversation_context = None
        if conversation_id:
            conversation_context = conversation_manager.get_conversation_context(conversation_id)
        
        # Use Phase 4 mode-specific system prompt
        system_prompt = conversation_manager.get_mode_specific_system_prompt('database', conversation_context or {})
        
        # Build messages array with conversation history if available
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add conversation history if conversation_id provided
        if conversation_id:
            # Use weather-aware messages for enhanced context
            conversation_messages = conversation_manager.get_weather_aware_messages(conversation_id)
            if conversation_messages:
                # Add conversation history (excluding the current user message)
                for msg in conversation_messages[:-1]:  # Exclude the last message (current user message)
                    # Ensure message has the correct structure
                    if isinstance(msg, dict) and 'role' in msg and 'content' in msg:
                        messages.append({
                            "role": msg["role"],
                            "content": str(msg["content"])
                        })
                logger.info(f"Phase 4: Added {len(conversation_messages)-1} weather-aware conversation history messages")
        
        # Add current user message with context
        user_prompt = f"""Context: {context}

User Question: {message}

Please provide a helpful, accurate response based on the context and user's question."""
        messages.append({"role": "user", "content": user_prompt})
        
        # Make AI call
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        ai_response = response.choices[0].message.content
        if ai_response is None:
            raise ValueError("AI response content is None")
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error generating AI response: {e}")
        raise

def generate_fallback_ai_response(message: str) -> str:
    """
    Generate a fallback AI response when context building fails.
    
    Args:
        message (str): Original user message
    
    Returns:
        str: Simple AI response
    """
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a helpful gardening assistant for Houston, Texas."},
                {"role": "user", "content": message}
            ],
            temperature=0.7,
            max_tokens=300
        )
        
        ai_response = response.choices[0].message.content
        if ai_response is None:
            return "I apologize, but I'm having trouble processing your request. Please try again."
        
        return ai_response
        
    except Exception as e:
        logger.error(f"Error in fallback AI response: {e}")
        return "I apologize, but I'm experiencing technical difficulties. Please try again in a moment."

def get_performance_metrics() -> Dict:
    """
    Get current performance metrics for monitoring.
    
    Returns:
        Dict: Current performance metrics
    """
    return performance_monitor.get_metrics()

def log_performance_summary():
    """
    Log a summary of current performance metrics.
    """
    performance_monitor.log_metrics() 