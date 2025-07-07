# GardenLLM Four-Mode System Requirements Document

## Executive Summary

This document outlines the requirements for implementing a four-mode system in GardenLLM while preserving all existing functionality, adding interactive bot capabilities with conversation memory, and ensuring Houston-specific climate instructions across all modes.

**CRITICAL IMPLEMENTATION PRINCIPLE: The program remains completely functional throughout all implementation phases. All existing features must remain operational at every step of development. Climate context is mandatory in all AI system prompts (default: Houston, TX, USA).**

## Current State Analysis

### ✅ **Already Implemented Functionality**
- **Enhanced NLP System**: Complete AI-powered query analysis with plant extraction and classification (Phases 1-5)
- **Weather Mode**: Current weather analysis and plant care recommendations with Houston-specific coordinates
- **Database Operations**: Plant CRUD operations via Google Sheets (add/update/query plants) with exact command format preservation
- **Plant Maintenance**: Add plant and update plant functionality with optional fields (location and photo URL only)
- **Image Analysis**: Plant photo analysis with GPT-4 Vision and conversation memory
- **General Gardening**: Basic gardening Q&A with Houston climate context
- **Houston Climate Awareness**: Standardized Houston climate instructions in AI prompts
- **Conversation Memory**: Token-managed conversation system for image analysis
- **Performance Monitoring**: Comprehensive performance metrics and monitoring

### 🔄 **Current System Prompts (7 total) - Enhanced with Houston Climate**
1. Plant Care Guide Generation (detailed, structured) - ✅ Houston climate integrated
2. General Chat Response (simple) - ✅ Houston climate integrated
3. Image Analysis (restrictive, visual-only) - ✅ Houston climate integrated
4. Image Analysis Context Setting - ✅ Houston climate integrated
5. Image Analysis Context Reminder - ✅ Houston climate integrated
6. Comprehensive Garden Management (Houston-specific) - ✅ Houston climate integrated
7. Basic Gardening Assistant (simplest) - ✅ Houston climate integrated

## Core Requirements

### 1. **Four-Mode System Architecture** ❌ **NOT YET IMPLEMENTED**

#### Mode 1: General Gardening Mode 🌱
- **Purpose**: Handle general gardening questions with optional database/weather integration
- **Scope**: Broader gardening knowledge, not limited to user's database
- **Houston Context**: ✅ Already implemented - Houston-specific climate advice
- **Conversation Memory**: ✅ Already implemented - Full conversation history maintained
- **Database Integration**: ✅ Already implemented - Can reference garden database if relevant
- **Weather Integration**: ✅ Already implemented - Can reference weather data when relevant

#### Mode 2: Garden Database Mode 🗂️
- **Purpose**: Focused queries about plants in user's garden database with full CRUD operations
- **Scope**: Limited to plants currently in Google Sheets database, plus add/update operations
- **Houston Context**: ✅ Already implemented - Houston-specific care recommendations
- **Conversation Memory**: ✅ Already implemented - Full conversation history maintained
- **Database Integration**: ✅ Already implemented - All queries relate to database plants
- **Weather Integration**: ✅ Already implemented - Can reference weather data for garden-specific advice
- **Plant Maintenance**: ✅ Already implemented - Full add/update/query functionality for plant database

#### Mode 3: Weather Mode 🌤️
- **Purpose**: Dedicated weather analysis and plant care recommendations
- **Scope**: Weather forecasting and plant care based on weather conditions
- **Houston Context**: ✅ Already implemented - Houston-specific weather patterns and plant care
- **Conversation Memory**: ✅ Already implemented - Full conversation history maintained
- **Database Integration**: ✅ Already implemented - Can reference specific plants for weather advice
- **Weather Integration**: ✅ Already implemented - Primary focus - detailed weather analysis

#### Mode 4: Image Analysis Mode 📷
- **Purpose**: Analyze uploaded plant photos and answer questions about specific plants
- **Scope**: Analysis of specific plant shown in uploaded photos
- **Houston Context**: ✅ Already implemented - Houston-specific care recommendations for identified plants
- **Conversation Memory**: ✅ Already implemented - Full conversation history maintained
- **Database Integration**: ✅ Already implemented - Can suggest adding analyzed plants to database
- **Weather Integration**: None - focused on visual analysis only

### 2. **Interactive Bot Functionality** ✅ **MOSTLY IMPLEMENTED**

#### Conversation Memory Requirements ✅ **IMPLEMENTED**
- **Cross-Mode Persistence**: ✅ Already implemented - Conversation history persists across interactions
- **Context Awareness**: ✅ Already implemented - AI understands context and responds appropriately
- **Mode-Specific Context**: ❌ **NOT YET IMPLEMENTED** - Need mode-specific system prompts
- **Memory Management**: ✅ Already implemented - Token management to prevent context overflow
- **Conversation ID**: ✅ Already implemented - Unique conversation IDs for tracking and debugging

#### Interactive Features ✅ **MOSTLY IMPLEMENTED**
- **Real-time Chat**: ✅ Already implemented - Seamless chat interface with typing indicators
- **Message History**: ✅ Already implemented - Display full conversation history
- **Mode Switching**: ❌ **NOT YET IMPLEMENTED** - Need mode selection interface
- **Error Recovery**: ✅ Already implemented - Graceful handling of API failures and network issues
- **Save Conversations**: ❌ **NOT YET IMPLEMENTED** - Need conversation export functionality

### 3. **Climate-Specific Instructions System** ✅ **IMPLEMENTED**

**CRITICAL: Climate context is MANDATORY in ALL AI system prompts and responses** ✅ **IMPLEMENTED**

#### System Configuration ❌ **NOT YET IMPLEMENTED**
- **Climate Parameter**: ❌ Need configurable system setting with Houston, TX, USA as default
- **Configuration File**: ❌ Need `climate_config.py` for centralized climate management
- **Default Location**: ✅ Already implemented - Houston, TX, USA (preserves current functionality)
- **User Override**: ❌ Need ability to change climate location while maintaining all functionality
- **Climate Data**: ✅ Already implemented - Centralized climate information for Houston location

#### Houston Climate Context (Default) ✅ **IMPLEMENTED**
- **Hardiness Zone**: ✅ Zone 9a/9b specific advice implemented
- **Temperature Ranges**: ✅ Summer highs: 90-100°F (32-38°C) implemented
- **Humidity**: ✅ High humidity (60-80%) considerations implemented
- **Rainfall**: ✅ 50+ inches annually, heavy spring/fall rains implemented
- **Soil Conditions**: ✅ Clay soil, alkaline pH (7.0-8.0) implemented
- **Growing Seasons**: ✅ Spring: February-May, Fall: September-November implemented

#### Required Climate Instructions for All Modes ✅ **IMPLEMENTED**
- **Plant Selection**: ✅ Recommend climate-appropriate varieties for Houston location
- **Watering Schedules**: ✅ Account for local humidity and soil conditions
- **Frost Protection**: ✅ Specific advice based on local frost dates and patterns
- **Disease Prevention**: ✅ Focus on diseases common in local climate conditions
- **Soil Amendments**: ✅ Recommendations for local soil type improvement
- **Timing**: ✅ All planting and care advice considers local growing seasons
- **Default Behavior**: ✅ Houston-specific recommendations when no other location is configured

### 4. **Database Field Consolidation** ❌ **NOT YET IMPLEMENTED**

#### Field Management Requirements ❌ **NOT YET IMPLEMENTED**
- **Centralized Configuration**: ❌ Need `field_config.py` for all field mappings
- **User-Friendly Aliases**: ✅ Already implemented - Support natural language field references
- **Backward Compatibility**: ✅ Already implemented - No changes to existing database structure
- **Validation**: ✅ Already implemented - Ensure all field operations use correct database field names
- **Mapping Functions**: ✅ Already implemented - Standardize field name processing across all modes

#### Required Field Configuration ❌ **NOT YET IMPLEMENTED**
- **Database Fields**: ✅ Already implemented - 17 exact column headers (including 'Raw Photo URL')
- **User Aliases**: ✅ Already implemented - Natural language variations for all fields
- **Section Mappings**: ✅ Already implemented - For care guide parsing
- **Field Categories**: ✅ Already implemented - Basic info, care requirements, media, metadata
- **Validation Functions**: ✅ Already implemented - Ensure field names exist before operations

### 5. **Plant Database Maintenance Functionality** ✅ **FULLY IMPLEMENTED**

**CRITICAL PRESERVATION REQUIREMENT:**
The add/update plant functionality has been preserved EXACTLY as specified. The command format "Add/Update plant [plant name]" or "Add/Update [plant name]" and the AI-generated care information parsing has been maintained unchanged.

#### Add Plant Operations ✅ **FULLY IMPLEMENTED**
**CRITICAL: Preserved EXACT current functionality**

- **Command Format**: ✅ EXACTLY "Add/Update plant [plant name]" or "Add/Update [plant name]"
- **Required Fields**: ✅ Only Plant Name is mandatory
- **Optional Fields**: ✅ ONLY location and photo URL (as in current version)
- **AI Care Information**: ✅ AI automatically provides comprehensive care information that gets parsed and loaded/updated in garden database
- **Field Validation**: ✅ Validate field names and data types before database insertion
- **Houston Climate Integration**: ✅ Automatically suggest Houston-appropriate care requirements
- **Photo URL Support**: ✅ Accept both Photo URL and Raw Photo URL fields
- **Location Flexibility**: ✅ Support various location formats (garden bed, container, etc.)
- **Confirmation Process**: ✅ Show summary of plant data before adding to database
- **Error Handling**: ✅ Graceful handling of duplicate plants and invalid data

#### Update Plant Operations ✅ **FULLY IMPLEMENTED**
**CRITICAL: Preserved EXACT current functionality**

- **Command Format**: ✅ EXACTLY "Add/Update plant [plant name]" or "Add/Update [plant name]" (same as add)
- **Plant Identification**: ✅ Support updating by Plant Name (same command as add)
- **AI Care Information**: ✅ AI automatically provides updated comprehensive care information that gets parsed and loaded/updated in garden database
- **Optional Fields**: ✅ ONLY location and photo URL can be manually specified (as in current version)
- **Field Validation**: ✅ Ensure updated fields use correct database field names
- **Photo URL Updates**: ✅ Support updating both Photo URL and Raw Photo URL
- **Location Updates**: ✅ Allow changing plant location within garden
- **Care Requirement Updates**: ✅ All care fields updated via AI-generated care information
- **Houston Climate Suggestions**: ✅ Provide Houston-specific care updates
- **Change Tracking**: ✅ Maintain Last Updated timestamp
- **Confirmation Process**: ✅ Show before/after comparison for updates
- **Error Handling**: ✅ Handle cases where plant doesn't exist or field is invalid

#### Database Maintenance Commands ✅ **FULLY IMPLEMENTED**
**CRITICAL: These commands preserve EXACT current functionality**

- **Add/Update Plant Commands** (EXACT current format):
  - ✅ "Add/Update plant [plant name]"
  - ✅ "Add/Update [plant name]"
- **Query Plant Commands**:
  - ✅ "Show me my [plant name]"
  - ✅ "What's the care for [plant name]?"
  - ✅ "Where is my [plant name] located?"
  - ✅ "List all my plants"

#### Field-Specific Requirements ✅ **FULLY IMPLEMENTED**
**CRITICAL: Preserved EXACT current functionality**

- **Plant Name**: ✅ Required field, case-insensitive matching
- **Location**: ✅ Optional field (as in current version)
- **Photo URL**: ✅ Optional field, supports both Photo URL and Raw Photo URL fields (as in current version)
- **Care Fields**: ✅ All care-related fields populated automatically by AI-generated care information (as in current version)
- **Metadata Fields**: ✅ ID and Last Updated are system-managed
- **Field Aliases**: ✅ Support natural language field references (e.g., "watering" for "Watering Needs")

#### Integration with Existing Modes ✅ **FULLY IMPLEMENTED**
- **Garden Database Mode**: ✅ Primary mode for add/update operations
- **Image Analysis Mode**: ✅ Can suggest adding analyzed plants to database
- **General Gardening Mode**: ✅ Can reference database but not modify it
- **Weather Mode**: ✅ Can reference database for weather-specific care updates

#### User Experience Requirements ✅ **FULLY IMPLEMENTED**
**CRITICAL: Preserved EXACT current functionality**

- **Command Interface**: ✅ EXACT current command format "Add/Update plant [plant name]" or "Add/Update [plant name]"
- **AI Care Generation**: ✅ AI automatically generates comprehensive care information (as in current version)
- **Care Information Parsing**: ✅ AI-generated care information gets parsed and loaded/updated in garden database (as in current version)
- **Optional Fields**: ✅ Only location and photo URL can be manually specified (as in current version)
- **Confirmation Dialogs**: ✅ Show data before committing changes
- **Error Messages**: ✅ Clear, helpful error messages for validation failures
- **Success Feedback**: ✅ Confirm successful operations with summary
- **Houston Context**: ✅ Always provide Houston-specific care suggestions

## Technical Requirements

### 1. **Frontend Changes** ❌ **NOT YET IMPLEMENTED**

#### Mode Selection Interface ❌ **NOT YET IMPLEMENTED**
- **Four-Way Selector**: ❌ Need radio buttons or dropdown for mode selection
- **Visual Indicators**: ❌ Need icons and descriptions for each mode
- **Dynamic Placeholders**: ❌ Need mode-specific input placeholders
- **Mode-Specific UI**: ❌ Need show/hide elements based on selected mode
- **Conversation Display**: ❌ Need mode indicators in message history

#### User Experience Requirements ❌ **NOT YET IMPLEMENTED**
- **Smooth Transitions**: ❌ Need no jarring changes when switching modes
- **Context Preservation**: ❌ Need clear indication that conversation history is maintained
- **Error Handling**: ✅ Already implemented - User-friendly error messages
- **Loading States**: ✅ Already implemented - Appropriate loading indicators for each mode
- **Responsive Design**: ✅ Already implemented - Work on mobile and desktop

### 2. **Backend Changes** ❌ **NOT YET IMPLEMENTED**

#### API Endpoint Structure ❌ **NOT YET IMPLEMENTED**
- **Mode-Aware Routing**: ❌ Need `/chat/{mode}` endpoints
- **Conversation Management**: ✅ Already implemented - Centralized conversation storage
- **Field Processing**: ✅ Already implemented - Unified field validation and mapping
- **Error Handling**: ✅ Already implemented - Comprehensive error handling and logging
- **Rate Limiting**: ✅ Already implemented - Maintain existing rate limiting for all modes

#### System Prompt Management ❌ **NOT YET IMPLEMENTED**
- **Mode-Specific Prompts**: ❌ Need different system prompts for each mode
- **Houston Context**: ✅ Already implemented - Standardized Houston climate instructions
- **Conversation Context**: ✅ Already implemented - Maintain conversation history across mode switches
- **Dynamic Prompting**: ✅ Already implemented - Adjust prompts based on conversation context

### 3. **Database Requirements** ✅ **IMPLEMENTED**

#### Schema Preservation ✅ **IMPLEMENTED**
- **No Schema Changes**: ✅ Maintain existing 17-column structure
- **Field Mapping**: ✅ Use centralized field configuration
- **Data Integrity**: ✅ Ensure all operations maintain data consistency
- **Performance**: ✅ Optimize queries for conversation context

#### Conversation Storage ✅ **IMPLEMENTED**
- **Conversation History**: ✅ Store conversation data with metadata
- **Token Management**: ✅ Implement conversation length limits
- **Cleanup**: ✅ Automatic cleanup of old conversations
- **Export**: ❌ **NOT YET IMPLEMENTED** - Need support for conversation export

## Implementation Phases (UPDATED)

**CRITICAL: Each phase maintains complete program functionality. All existing features remain operational throughout implementation.**

### ✅ **Phase 1: Enhanced NLP Foundation (COMPLETED)**
1. **Query Analyzer Implementation** ✅ **COMPLETED**
   - ✅ Implemented `query_analyzer.py`
   - ✅ Created AI-powered query analysis
   - ✅ Added plant extraction and classification
   - ✅ Maintained all existing functionality during implementation

2. **Database Integration** ✅ **COMPLETED**
   - ✅ Integrated database plant list with query analysis
   - ✅ Added caching mechanism for plant list
   - ✅ Enhanced error handling and fallback mechanisms
   - ✅ Ensured existing chat functionality remained operational

3. **Performance Monitoring** ✅ **COMPLETED**
   - ✅ Implemented performance monitoring system
   - ✅ Added metrics tracking for query processing
   - ✅ Created conversation memory management
   - ✅ Ensured performance doesn't degrade existing functionality

### ✅ **Phase 2: Database and AI Processing (COMPLETED)**
1. **Database-Only Query Processing** ✅ **COMPLETED**
   - ✅ Implemented direct database responses for location, photo, and list queries
   - ✅ Added response formatting functions
   - ✅ Enhanced database functions for multiple plant lookup
   - ✅ Maintained existing functionality for backward compatibility

2. **AI-Enhanced Query Processing** ✅ **COMPLETED**
   - ✅ Implemented second AI call for care, diagnosis, advice, and general questions
   - ✅ Created specialized prompts for different query types
   - ✅ Integrated weather data when relevant
   - ✅ Added response enhancement functions

3. **Integration and Optimization** ✅ **COMPLETED**
   - ✅ Completed integration of two-AI-call workflow
   - ✅ Optimized performance and accuracy
   - ✅ Added comprehensive testing
   - ✅ Preserved all existing functionality

### ❌ **Phase 3: Four-Mode System (NOT YET IMPLEMENTED)**
1. **Mode System Architecture** ❌ **NOT YET IMPLEMENTED**
   - ❌ Create mode selection interface
   - ❌ Implement mode-specific routing
   - ❌ Add mode indicators in conversation
   - ❌ Ensure existing UI remains functional throughout changes

2. **Field Configuration System** ❌ **NOT YET IMPLEMENTED**
   - ❌ Implement `field_config.py`
   - ❌ Create `field_processor.py`
   - ❌ Update existing field operations
   - ❌ Maintain all existing functionality during implementation

3. **Climate Configuration System** ❌ **NOT YET IMPLEMENTED**
   - ❌ Create `climate_config.py` for centralized climate management
   - ❌ Set Houston, TX, USA as default climate location
   - ❌ Update all system prompts with configurable climate context
   - ❌ Test climate-specific responses

### ❌ **Phase 4: Mode Integration (NOT YET IMPLEMENTED)**
1. **Backend Mode Routing** ❌ **NOT YET IMPLEMENTED**
   - ❌ Implement mode-aware chat endpoints
   - ❌ Create mode-specific system prompts with MANDATORY climate context (default: Houston)
   - ❌ Add mode validation and error handling
   - ❌ Maintain all existing functionality during implementation

2. **Frontend Mode Selection** ❌ **NOT YET IMPLEMENTED**
   - ❌ Create four-way mode selector
   - ❌ Implement mode-specific UI elements
   - ❌ Add mode indicators in conversation
   - ❌ Ensure existing UI remains functional throughout changes

3. **Cross-Mode Conversation** ❌ **NOT YET IMPLEMENTED**
   - ❌ Implement conversation persistence across modes
   - ❌ Add mode context to conversation history
   - ❌ Test mode switching functionality
   - ❌ Preserve existing conversation functionality

### ❌ **Phase 5: Testing & Polish (NOT YET IMPLEMENTED)**
1. **Comprehensive Testing** ❌ **NOT YET IMPLEMENTED**
   - ❌ Test all modes with conversation memory
   - ❌ Verify climate instructions are MANDATORY in all responses (default: Houston)
   - ❌ Test mode switching scenarios
   - ❌ Verify all existing functionality remains operational

2. **Performance Optimization** ❌ **NOT YET IMPLEMENTED**
   - ❌ Optimize conversation memory usage
   - ❌ Implement efficient token management
   - ❌ Test with large conversation histories
   - ❌ Ensure performance doesn't degrade existing functionality

3. **User Experience Polish** ❌ **NOT YET IMPLEMENTED**
   - ❌ Refine UI/UX based on testing
   - ❌ Add helpful error messages
   - ❌ Implement conversation export features
   - ❌ Maintain existing user experience while adding new features

## Success Criteria

### Functional Requirements
- [x] Enhanced NLP system works with full conversation memory ✅ **COMPLETED**
- [x] Climate instructions are MANDATORY in all responses (default: Houston, TX, USA) ✅ **COMPLETED**
- [x] Database operations work correctly with field consolidation ✅ **COMPLETED**
- [x] Add/Update plant functionality works with EXACT current command format ✅ **COMPLETED**
- [x] AI-generated care information parsing works exactly as in current version ✅ **COMPLETED**
- [x] Only location and photo URL are optional fields (as in current version) ✅ **COMPLETED**
- [x] Plant maintenance operations maintain conversation context ✅ **COMPLETED**
- [x] Program remains completely functional during all implementation phases ✅ **COMPLETED**
- [ ] All four modes work with full conversation memory ❌ **NOT YET IMPLEMENTED**
- [ ] Smooth mode switching without context loss ❌ **NOT YET IMPLEMENTED**

### Performance Requirements
- [x] Conversation memory doesn't exceed token limits ✅ **COMPLETED**
- [x] API response times remain under 5 seconds ✅ **COMPLETED**
- [x] No memory leaks in conversation storage ✅ **COMPLETED**
- [ ] Mode switching response time < 1 second ❌ **NOT YET IMPLEMENTED**

### User Experience Requirements
- [x] Helpful error messages ✅ **COMPLETED**
- [x] Responsive design on all devices ✅ **COMPLETED**
- [ ] Clear mode indicators and descriptions ❌ **NOT YET IMPLEMENTED**
- [ ] Intuitive mode switching ❌ **NOT YET IMPLEMENTED**
- [ ] Conversation export functionality ❌ **NOT YET IMPLEMENTED**

## Risk Mitigation

### Technical Risks
- **Token Limit Exceeded**: ✅ Implemented conversation truncation
- **Mode Context Confusion**: ❌ Need clear mode indicators and validation
- **Database Field Mismatch**: ✅ Implemented comprehensive field validation
- **API Rate Limits**: ✅ Maintained existing rate limiting

### User Experience Risks
- **Mode Confusion**: ❌ Need clear visual indicators and help text
- **Context Loss**: ✅ Implemented robust conversation persistence
- **Performance Degradation**: ✅ Implemented efficient memory management

## Dependencies

### External Dependencies
- ✅ OpenAI API (GPT-4, GPT-4 Vision) - **IMPLEMENTED**
- ✅ Google Sheets API - **IMPLEMENTED**
- ✅ OpenWeather API - **IMPLEMENTED**
- ✅ Existing environment variables - **IMPLEMENTED**

### Internal Dependencies
- ✅ Current database structure (17 columns) - **IMPLEMENTED**
- ✅ Existing rate limiting system - **IMPLEMENTED**
- ✅ Current authentication setup - **IMPLEMENTED**
- ✅ Existing error handling patterns - **IMPLEMENTED**

## System Prompts by Mode (CURRENT IMPLEMENTATION)

### **Current Enhanced System Prompt** (Used across all interactions):
```
You are a knowledgeable gardening expert with access to the user's garden database. You can answer general gardening questions and provide advice on any plant species. You may reference the user's garden database if relevant, but you're not limited to plants in their database. You can also provide weather-aware gardening advice when appropriate. Focus on providing practical, actionable gardening advice.

IMPORTANT: All advice must be specific to the configured climate location (default: Houston, Texas):
- Hardiness Zone: 9a/9b (Houston default)
- Summer highs: 90-100°F (32-38°C) with high humidity (Houston default)
- Winter lows: 30-40°F (-1-4°C) with occasional freezes (Houston default)
- Soil: Clay soil, alkaline pH (7.0-8.0) (Houston default)
- Rainfall: 50+ inches annually, heavy spring/fall rains (Houston default)
- Growing seasons: Spring (Feb-May), Fall (Sept-Nov), avoid peak summer heat (Houston default)

When referencing the garden database, use these field names: Plant Name, Description, Location, Light Requirements, Frost Tolerance, Watering Needs, Soil Preferences, Pruning Instructions, Mulching Needs, Fertilizing Schedule, Winterizing Instructions, Spacing Requirements, Care Notes, Photo URL, Raw Photo URL.

ADD/UPDATE PLANT OPERATIONS (EXACT CURRENT FUNCTIONALITY):
- Command format: "Add/Update plant [plant name]" or "Add/Update [plant name]"
- Only Plant Name is required; optional fields are ONLY location and photo URL
- AI automatically generates comprehensive care information that gets parsed and loaded/updated in garden database
- Automatically suggest climate-appropriate care requirements (default: Houston)
- Support both Photo URL and Raw Photo URL fields
- Show confirmation summary before adding/updating to database
```

### **Mode-Specific Prompts** (TO BE IMPLEMENTED):
The four-mode system will require separate system prompts for each mode while maintaining the Houston climate context and existing functionality.

This requirements document has been updated to reflect the current implementation status. The enhanced NLP system (Phases 1-5) has been completed, and the four-mode system architecture remains to be implemented while preserving all existing functionality. 