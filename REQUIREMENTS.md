# GardenLLM Four-Mode System Requirements Document

## Executive Summary

This document outlines the requirements for implementing a four-mode system in GardenLLM while preserving all existing functionality, adding interactive bot capabilities with conversation memory, and ensuring Houston-specific climate instructions across all modes.

**CRITICAL IMPLEMENTATION PRINCIPLE: The program remains completely functional throughout all implementation phases. All existing features must remain operational at every step of development. Climate context is mandatory in all AI system prompts (default: Houston, TX, USA).**

## Current State Analysis

### Existing Functionality to Preserve
- **Weather Mode**: Current weather analysis and plant care recommendations
- **Database Operations**: Plant CRUD operations via Google Sheets (add/update/query plants)
- **Plant Maintenance**: Add plant and update plant functionality with optional fields
- **Image Analysis**: Plant photo analysis with GPT-4 Vision
- **General Gardening**: Basic gardening Q&A
- **Houston Climate Awareness**: Currently exists in some prompts but needs standardization

### Current System Prompts (7 total)
1. Plant Care Guide Generation (detailed, structured)
2. General Chat Response (simple)
3. Image Analysis (restrictive, visual-only)
4. Image Analysis Context Setting
5. Image Analysis Context Reminder
6. Comprehensive Garden Management (Houston-specific)
7. Basic Gardening Assistant (simplest)

## Core Requirements

### 1. **Four-Mode System Architecture**

#### Mode 1: General Gardening Mode 🌱
- **Purpose**: Handle general gardening questions with optional database/weather integration
- **Scope**: Broader gardening knowledge, not limited to user's database
- **Houston Context**: Must include Houston-specific climate advice
- **Conversation Memory**: Full conversation history maintained
- **Database Integration**: Optional - can reference garden database if relevant
- **Weather Integration**: Can reference weather data when relevant

#### Mode 2: Garden Database Mode 🗂️
- **Purpose**: Focused queries about plants in user's garden database with full CRUD operations
- **Scope**: Limited to plants currently in Google Sheets database, plus add/update operations
- **Houston Context**: Must include Houston-specific care recommendations
- **Conversation Memory**: Full conversation history maintained
- **Database Integration**: Required - all queries must relate to database plants
- **Weather Integration**: Can reference weather data for garden-specific advice
- **Plant Maintenance**: Full add/update/query functionality for plant database

#### Mode 3: Weather Mode 🌤️
- **Purpose**: Dedicated weather analysis and plant care recommendations
- **Scope**: Weather forecasting and plant care based on weather conditions
- **Houston Context**: Must include Houston-specific weather patterns and plant care
- **Conversation Memory**: Full conversation history maintained
- **Database Integration**: Optional - can reference specific plants for weather advice
- **Weather Integration**: Primary focus - detailed weather analysis

#### Mode 4: Image Analysis Mode 📷
- **Purpose**: Analyze uploaded plant photos and answer questions about specific plants
- **Scope**: Analysis of specific plant shown in uploaded photos
- **Houston Context**: Must include Houston-specific care recommendations for identified plants
- **Conversation Memory**: Full conversation history maintained
- **Database Integration**: None - analysis based purely on visual assessment
- **Weather Integration**: None - focused on visual analysis only

### 2. **Interactive Bot Functionality**

#### Conversation Memory Requirements
- **Cross-Mode Persistence**: Conversation history must persist when switching between modes
- **Context Awareness**: AI must understand which mode is active and respond appropriately
- **Mode-Specific Context**: Each mode should have appropriate system prompts while maintaining conversation flow
- **Memory Management**: Implement token management to prevent context overflow
- **Conversation ID**: Unique conversation IDs for tracking and debugging

#### Interactive Features
- **Real-time Chat**: Seamless chat interface with typing indicators
- **Message History**: Display full conversation history with mode indicators
- **Mode Switching**: Smooth transitions between modes without losing context
- **Error Recovery**: Graceful handling of API failures and network issues
- **Save Conversations**: Ability to export conversation history

### 3. **Climate-Specific Instructions System**

**CRITICAL: Climate context is MANDATORY in ALL AI system prompts and responses**

#### System Configuration
- **Climate Parameter**: Configurable system setting with Houston, TX, USA as default
- **Configuration File**: `climate_config.py` for centralized climate management
- **Default Location**: Houston, TX, USA (preserves current functionality)
- **User Override**: Ability to change climate location while maintaining all functionality
- **Climate Data**: Centralized climate information for any configured location

#### Houston Climate Context (Default)
- **Hardiness Zone**: Zone 9a/9b specific advice
- **Temperature Ranges**: 
  - Summer highs: 90-100°F (32-38°C)
  - Winter lows: 30-40°F (-1-4°C)
  - Frost dates: Late November to early March
- **Humidity**: High humidity (60-80%) considerations
- **Rainfall**: 50+ inches annually, heavy spring/fall rains
- **Soil Conditions**: Clay soil, alkaline pH (7.0-8.0)
- **Growing Seasons**: 
  - Spring: February-May
  - Fall: September-November
  - Summer: June-August (hot, humid)
  - Winter: December-January (mild with occasional freezes)

#### Required Climate Instructions for All Modes
- **Plant Selection**: Recommend climate-appropriate varieties for configured location
- **Watering Schedules**: Account for local humidity and soil conditions
- **Frost Protection**: Specific advice based on local frost dates and patterns
- **Disease Prevention**: Focus on diseases common in local climate conditions
- **Soil Amendments**: Recommendations for local soil type improvement
- **Timing**: All planting and care advice must consider local growing seasons
- **Default Behavior**: Houston-specific recommendations when no other location is configured

### 4. **Database Field Consolidation**

#### Field Management Requirements
- **Centralized Configuration**: Create `field_config.py` for all field mappings
- **User-Friendly Aliases**: Support natural language field references
- **Backward Compatibility**: No changes to existing database structure
- **Validation**: Ensure all field operations use correct database field names
- **Mapping Functions**: Standardize field name processing across all modes

#### Required Field Configuration
- **Database Fields**: 17 exact column headers (including 'Raw Photo URL')
- **User Aliases**: Natural language variations for all fields
- **Section Mappings**: For care guide parsing
- **Field Categories**: Basic info, care requirements, media, metadata
- **Validation Functions**: Ensure field names exist before operations

### 5. **Plant Database Maintenance Functionality**

**CRITICAL PRESERVATION REQUIREMENT:**
The add/update plant functionality must preserve EXACTLY the current implementation. The command format "Add/Update plant [plant name]" or "Add/Update [plant name]" and the AI-generated care information parsing must remain unchanged. Any modifications to this functionality require explicit user approval before implementation.

#### Add Plant Operations
**CRITICAL: Must preserve EXACT current functionality - NO CHANGES without explicit user approval**

- **Command Format**: EXACTLY "Add/Update plant [plant name]" or "Add/Update [plant name]"
- **Required Fields**: Only Plant Name is mandatory
- **Optional Fields**: ONLY location and photo URL (as in current version)
- **AI Care Information**: AI automatically provides comprehensive care information that gets parsed and loaded/updated in garden database
- **Field Validation**: Validate field names and data types before database insertion
- **Houston Climate Integration**: Automatically suggest Houston-appropriate care requirements
- **Photo URL Support**: Accept both Photo URL and Raw Photo URL fields
- **Location Flexibility**: Support various location formats (garden bed, container, etc.)
- **Confirmation Process**: Show summary of plant data before adding to database
- **Error Handling**: Graceful handling of duplicate plants and invalid data

#### Update Plant Operations
**CRITICAL: Must preserve EXACT current functionality - NO CHANGES without explicit user approval**

- **Command Format**: EXACTLY "Add/Update plant [plant name]" or "Add/Update [plant name]" (same as add)
- **Plant Identification**: Support updating by Plant Name (same command as add)
- **AI Care Information**: AI automatically provides updated comprehensive care information that gets parsed and loaded/updated in garden database
- **Optional Fields**: ONLY location and photo URL can be manually specified (as in current version)
- **Field Validation**: Ensure updated fields use correct database field names
- **Photo URL Updates**: Support updating both Photo URL and Raw Photo URL
- **Location Updates**: Allow changing plant location within garden
- **Care Requirement Updates**: All care fields updated via AI-generated care information
- **Houston Climate Suggestions**: Provide Houston-specific care updates
- **Change Tracking**: Maintain Last Updated timestamp
- **Confirmation Process**: Show before/after comparison for updates
- **Error Handling**: Handle cases where plant doesn't exist or field is invalid

#### Database Maintenance Commands
**CRITICAL: These commands must preserve EXACT current functionality - NO CHANGES without explicit user approval**

- **Add/Update Plant Commands** (EXACT current format):
  - "Add/Update plant [plant name]"
  - "Add/Update [plant name]"
- **Query Plant Commands**:
  - "Show me my [plant name]"
  - "What's the care for [plant name]?"
  - "Where is my [plant name] located?"
  - "List all my plants"

#### Field-Specific Requirements
**CRITICAL: Must preserve EXACT current functionality - NO CHANGES without explicit user approval**

- **Plant Name**: Required field, case-insensitive matching
- **Location**: Optional field (as in current version)
- **Photo URL**: Optional field, supports both Photo URL and Raw Photo URL fields (as in current version)
- **Care Fields**: All care-related fields populated automatically by AI-generated care information (as in current version)
- **Metadata Fields**: ID and Last Updated are system-managed
- **Field Aliases**: Support natural language field references (e.g., "watering" for "Watering Needs")

#### Integration with Existing Modes
- **Garden Database Mode**: Primary mode for add/update operations
- **Image Analysis Mode**: Can suggest adding analyzed plants to database
- **General Gardening Mode**: Can reference database but not modify it
- **Weather Mode**: Can reference database for weather-specific care updates

#### User Experience Requirements
**CRITICAL: Must preserve EXACT current functionality - NO CHANGES without explicit user approval**

- **Command Interface**: EXACT current command format "Add/Update plant [plant name]" or "Add/Update [plant name]"
- **AI Care Generation**: AI automatically generates comprehensive care information (as in current version)
- **Care Information Parsing**: AI-generated care information gets parsed and loaded/updated in garden database (as in current version)
- **Optional Fields**: Only location and photo URL can be manually specified (as in current version)
- **Confirmation Dialogs**: Show data before committing changes
- **Error Messages**: Clear, helpful error messages for validation failures
- **Success Feedback**: Confirm successful operations with summary
- **Houston Context**: Always provide Houston-specific care suggestions

## Technical Requirements

### 1. **Frontend Changes**

#### Mode Selection Interface
- **Four-Way Selector**: Radio buttons or dropdown for mode selection
- **Visual Indicators**: Icons and descriptions for each mode
- **Dynamic Placeholders**: Mode-specific input placeholders
- **Mode-Specific UI**: Show/hide elements based on selected mode
- **Conversation Display**: Show mode indicators in message history

#### User Experience Requirements
- **Smooth Transitions**: No jarring changes when switching modes
- **Context Preservation**: Clear indication that conversation history is maintained
- **Error Handling**: User-friendly error messages
- **Loading States**: Appropriate loading indicators for each mode
- **Responsive Design**: Work on mobile and desktop

### 2. **Backend Changes**

#### API Endpoint Structure
- **Mode-Aware Routing**: `/chat/{mode}` endpoints
- **Conversation Management**: Centralized conversation storage
- **Field Processing**: Unified field validation and mapping
- **Error Handling**: Comprehensive error handling and logging
- **Rate Limiting**: Maintain existing rate limiting for all modes

#### System Prompt Management
- **Mode-Specific Prompts**: Different system prompts for each mode
- **Houston Context**: Standardized Houston climate instructions
- **Conversation Context**: Maintain conversation history across mode switches
- **Dynamic Prompting**: Adjust prompts based on conversation context

### 3. **Database Requirements**

#### Schema Preservation
- **No Schema Changes**: Maintain existing 17-column structure
- **Field Mapping**: Use centralized field configuration
- **Data Integrity**: Ensure all operations maintain data consistency
- **Performance**: Optimize queries for conversation context

#### Conversation Storage
- **Conversation History**: Store conversation data with mode information
- **Token Management**: Implement conversation length limits
- **Cleanup**: Automatic cleanup of old conversations
- **Export**: Support for conversation export

## Implementation Phases

**CRITICAL: Each phase maintains complete program functionality. All existing features remain operational throughout implementation.**

### Phase 1: Foundation (Week 1-2)
1. **Create Field Configuration**
   - Implement `field_config.py`
   - Create `field_processor.py`
   - Update existing field operations
   - **Maintain all existing functionality during implementation**

2. **Conversation Management**
   - Implement conversation storage
   - Add conversation ID tracking
   - Create conversation cleanup utilities
   - **Ensure existing chat functionality remains operational**

3. **Climate System Configuration**
   - Create `climate_config.py` for centralized climate management
   - Set Houston, TX, USA as default climate location
   - Update all system prompts with configurable climate context
   - Test climate-specific responses
   - **Climate context is MANDATORY in all AI system prompts**

### Phase 2: Mode System (Week 3-4)
1. **Backend Mode Routing**
   - Implement mode-aware chat endpoints
   - Create mode-specific system prompts with MANDATORY climate context (default: Houston)
   - Add mode validation and error handling
   - **Maintain all existing functionality during implementation**

2. **Frontend Mode Selection**
   - Create four-way mode selector
   - Implement mode-specific UI elements
   - Add mode indicators in conversation
   - **Ensure existing UI remains functional throughout changes**

3. **Cross-Mode Conversation**
   - Implement conversation persistence across modes
   - Add mode context to conversation history
   - Test mode switching functionality
   - **Preserve existing conversation functionality**

### Phase 3: Integration (Week 5-6)
1. **Weather Mode Enhancement**
   - Integrate weather functionality into mode system
   - Add climate-specific weather advice with MANDATORY climate context (default: Houston)
   - Test weather mode with conversation memory
   - **Preserve existing weather functionality completely**

2. **Database Mode Enhancement**
   - Integrate database operations into mode system
   - Implement add/update plant functionality with natural language commands
   - Add climate-specific plant recommendations with MANDATORY climate context (default: Houston)
   - Test database operations with conversation memory
   - Test plant maintenance operations (add/update/query)
   - **Preserve EXACT current add/update plant functionality**

3. **Image Analysis Mode Enhancement**
   - Integrate image analysis into mode system
   - Add climate-specific care recommendations with MANDATORY climate context (default: Houston)
   - Test image analysis with conversation memory
   - **Preserve existing image analysis functionality completely**

### Phase 4: Testing & Polish (Week 7-8)
1. **Comprehensive Testing**
   - Test all modes with conversation memory
   - Verify climate instructions are MANDATORY in all responses (default: Houston)
   - Test mode switching scenarios
   - **Verify all existing functionality remains operational**

2. **Performance Optimization**
   - Optimize conversation memory usage
   - Implement efficient token management
   - Test with large conversation histories
   - **Ensure performance doesn't degrade existing functionality**

3. **User Experience Polish**
   - Refine UI/UX based on testing
   - Add helpful error messages
   - Implement conversation export features
   - **Maintain existing user experience while adding new features**

## Success Criteria

### Functional Requirements
- [ ] All four modes work with full conversation memory
- [ ] Climate instructions are MANDATORY in all responses (default: Houston, TX, USA)
- [ ] Smooth mode switching without context loss
- [ ] All existing functionality preserved and operational throughout implementation
- [ ] Database operations work correctly with field consolidation
- [ ] Add/Update plant functionality works with EXACT current command format
- [ ] AI-generated care information parsing works exactly as in current version
- [ ] Only location and photo URL are optional fields (as in current version)
- [ ] Plant maintenance operations maintain conversation context
- [ ] Program remains completely functional during all implementation phases

### Performance Requirements
- [ ] Conversation memory doesn't exceed token limits
- [ ] Mode switching response time < 1 second
- [ ] API response times remain under 5 seconds
- [ ] No memory leaks in conversation storage

### User Experience Requirements
- [ ] Clear mode indicators and descriptions
- [ ] Intuitive mode switching
- [ ] Helpful error messages
- [ ] Conversation export functionality
- [ ] Responsive design on all devices

## Risk Mitigation

### Technical Risks
- **Token Limit Exceeded**: Implement conversation truncation
- **Mode Context Confusion**: Clear mode indicators and validation
- **Database Field Mismatch**: Comprehensive field validation
- **API Rate Limits**: Maintain existing rate limiting

### User Experience Risks
- **Mode Confusion**: Clear visual indicators and help text
- **Context Loss**: Robust conversation persistence
- **Performance Degradation**: Efficient memory management

## Dependencies

### External Dependencies
- OpenAI API (GPT-4, GPT-4 Vision)
- Google Sheets API
- OpenWeather API
- Existing environment variables

### Internal Dependencies
- Current database structure (17 columns)
- Existing rate limiting system
- Current authentication setup
- Existing error handling patterns

## System Prompts by Mode

### **General Gardening Mode**:
```
You are a knowledgeable gardening expert. You can answer general gardening questions and provide advice on any plant species. You may reference the user's garden database if relevant, but you're not limited to plants in their database. You can also provide weather-aware gardening advice when appropriate. Focus on providing practical, actionable gardening advice.

IMPORTANT: All advice must be specific to the configured climate location (default: Houston, Texas):
- Hardiness Zone: 9a/9b (Houston default)
- Summer highs: 90-100°F (32-38°C) with high humidity (Houston default)
- Winter lows: 30-40°F (-1-4°C) with occasional freezes (Houston default)
- Soil: Clay soil, alkaline pH (7.0-8.0) (Houston default)
- Rainfall: 50+ inches annually, heavy spring/fall rains (Houston default)
- Growing seasons: Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat (Houston default)

When referencing the garden database, use these field names: Plant Name, Description, Location, Light Requirements, Frost Tolerance, Watering Needs, Soil Preferences, Pruning Instructions, Mulching Needs, Fertilizing Schedule, Winterizing Instructions, Spacing Requirements, Care Notes, Photo URL, Raw Photo URL.
```

### **Garden Database Mode**:
```
You are a personal garden assistant with access to the user's specific garden database. You can help with database operations like adding, updating, and querying plant information. You can also provide weather-aware care recommendations for their specific plants.

IMPORTANT: All advice must be specific to the configured climate location (default: Houston, Texas):
- Hardiness Zone: 9a/9b (Houston default)
- Summer highs: 90-100°F (32-38°C) with high humidity (Houston default)
- Winter lows: 30-40°F (-1-4°C) with occasional freezes (Houston default)
- Soil: Clay soil, alkaline pH (7.0-8.0) (Houston default)
- Rainfall: 50+ inches annually, heavy spring/fall rains (Houston default)
- Growing seasons: Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat (Houston default)

Database fields available: ID, Plant Name, Description, Location, Light Requirements, Frost Tolerance, Watering Needs, Soil Preferences, Pruning Instructions, Mulching Needs, Fertilizing Schedule, Winterizing Instructions, Spacing Requirements, Care Notes, Photo URL, Raw Photo URL, Last Updated.

ADD/UPDATE PLANT OPERATIONS (EXACT CURRENT FUNCTIONALITY):
- Command format: "Add/Update plant [plant name]" or "Add/Update [plant name]"
- Only Plant Name is required; optional fields are ONLY location and photo URL
- AI automatically generates comprehensive care information that gets parsed and loaded/updated in garden database
- Automatically suggest climate-appropriate care requirements (default: Houston)
- Support both Photo URL and Raw Photo URL fields
- Show confirmation summary before adding/updating to database

When updating plants, use the exact field names listed above. Users can reference fields by common names (e.g., "watering" for "Watering Needs", "light" for "Light Requirements"). Always provide climate-specific care recommendations when adding or updating plants (default: Houston).
```

### **Weather Mode**:
```
You are a weather-aware gardening advisor. You provide detailed weather forecasts and plant care recommendations based on current and forecasted weather conditions. You can reference the user's garden database to provide plant-specific weather advice. Focus on actionable recommendations like watering schedules, frost protection, and weather-related plant care tasks. Always include both weather data and plant care implications.

IMPORTANT: All advice must be specific to the configured climate location (default: Houston, Texas):
- Hardiness Zone: 9a/9b (Houston default)
- Summer highs: 90-100°F (32-38°C) with high humidity (Houston default)
- Winter lows: 30-40°F (-1-4°C) with occasional freezes (Houston default)
- Soil: Clay soil, alkaline pH (7.0-8.0) (Houston default)
- Rainfall: 50+ inches annually, heavy spring/fall rains (Houston default)
- Growing seasons: Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat (Houston default)

When referencing specific plants in the database, you can access their care requirements using these fields: Light Requirements, Frost Tolerance, Watering Needs, Soil Preferences, Pruning Instructions, Mulching Needs, Fertilizing Schedule, Winterizing Instructions, Spacing Requirements, Care Notes.
```

### **Image Analysis Mode**:
```
You are a plant identification and health assessment expert. Analyze the specific plant shown in the uploaded image. Provide detailed information about this particular plant's species, health, and care needs. All follow-up questions should relate to this specific plant in the image. Do not reference databases or weather data - focus purely on visual analysis.

IMPORTANT: All care recommendations must be specific to the configured climate location (default: Houston, Texas):
- Hardiness Zone: 9a/9b (Houston default)
- Summer highs: 90-100°F (32-38°C) with high humidity (Houston default)
- Winter lows: 30-40°F (-1-4°C) with occasional freezes (Houston default)
- Soil: Clay soil, alkaline pH (7.0-8.0) (Houston default)
- Rainfall: 50+ inches annually, heavy spring/fall rains (Houston default)
- Growing seasons: Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat (Houston default)

If the user wants to add the analyzed plant to their database, you can suggest the relevant care information that would be stored in these fields: Plant Name, Description, Light Requirements, Frost Tolerance, Watering Needs, Soil Preferences, Pruning Instructions, Mulching Needs, Fertilizing Schedule, Winterizing Instructions, Spacing Requirements, Care Notes.
```

This requirements document provides a comprehensive roadmap for implementing the four-mode system while preserving all existing functionality and adding the requested interactive bot capabilities with Houston-specific climate instructions. 