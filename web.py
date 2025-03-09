from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from test_openai import gardenbot_response, get_weather_forecast, analyze_forecast_for_plants
import logging
import os
from typing import Optional, List, Dict
import traceback

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(title="GardenBot API")

# Update CORS settings
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

class WeatherResponse(BaseModel):
    forecast: List[Dict]
    plant_care_advice: List[str]

def handle_weather_query(message: str) -> str:
    """Handle weather-related queries and return formatted response"""
    try:
        logger.info("Getting weather forecast...")
        forecast = get_weather_forecast()
        if not forecast:
            return "I'm sorry, I couldn't retrieve the weather forecast at this time."

        advice = analyze_forecast_for_plants(forecast)
        
        # Format the response
        response = "🌿 Weather Forecast and Plant Care Advice 🌿\n\n"
        
        # Add forecast summary
        response += "Weather Forecast:\n"
        for day in forecast[:5]:  # Show next 5 days
            response += f"\n📅 {day['date']}:\n"
            response += f"• Temperature: {day['temp_min']}°F to {day['temp_max']}°F\n"
            response += f"• Conditions: {day['description']}\n"
            response += f"• Rain: {day['rain']} inches\n"
            response += f"• Humidity: {day['humidity']}%\n"
            response += f"• Wind: {day['wind_speed']} mph\n"
        
        # Add plant care advice
        response += "\n🌱 Plant Care Recommendations:\n"
        response += advice
        
        return response
    except Exception as e:
        logger.error(f"Error handling weather query: {e}")
        logger.error(traceback.format_exc())
        return "I'm sorry, I encountered an error while processing the weather information."

@app.post("/chat")
async def chat(request: ChatRequest):
    logger.info(f"Chat endpoint accessed with message: {request.message}")
    try:
        # Check if this is a weather-related query
        message_lower = request.message.lower()
        weather_keywords = ['weather', 'forecast', 'temperature', 'rain', 'humidity', 'wind']
        
        if any(keyword in message_lower for keyword in weather_keywords):
            logger.info("Processing weather-related query")
            response = handle_weather_query(request.message)
        else:
            logger.info("Calling gardenbot_response")
            response = gardenbot_response(request.message)
        
        # Log full response with clear markers and length
        logger.info("=== START OF RESPONSE ===")
        logger.info(response)
        logger.info(f"Response length: {len(response)}")
        logger.info("=== END OF RESPONSE ===")
        
        # Return full response with metadata
        return {
            "response": response,
            "length": len(response),
            "sections": response.count('###')
        }
    except Exception as e:
        logger.error(f"Error in chat endpoint: {str(e)}", exc_info=True)
        return {"response": "An error occurred while processing your request. Please try again."}

@app.get("/", response_class=HTMLResponse)
async def root():
    html_content = """<!DOCTYPE html>
    <html>
    <head>
        <title>GardenBot Chat</title>
        <style>
            body {
                font-family: Arial, sans-serif;
                margin: 0;
                padding: 20px;
                display: flex;
                flex-direction: column;
                min-height: 100vh;
            }
            
            #chat-container {
                flex: 1;
                overflow-y: auto;
                margin-bottom: 20px;
                padding: 20px;
                border: 1px solid #e2e8f0;
                border-radius: 8px;
                background: white;
            }
            
            .message {
                margin-bottom: 20px;
                white-space: pre-wrap;
                word-wrap: break-word;
                line-height: 1.6;
            }
            
            .user-message {
                color: #2c5282;
            }
            
            .bot-message {
                color: #2d3748;
            }
            
            .message h3 {
                color: #2c5282;
                margin: 20px 0 10px 0;
                font-size: 1.2em;
                border-bottom: 1px solid #e2e8f0;
                padding-bottom: 5px;
            }
            
            .message h4 {
                color: #4a5568;
                margin: 15px 0 10px 0;
                font-size: 1.1em;
                font-weight: bold;
            }
            
            .message ul {
                margin: 5px 0 15px 20px;
                padding-left: 20px;
                list-style-type: disc;
            }
            
            .message li {
                margin: 5px 0;
                line-height: 1.4;
            }
            
            .info-table {
                width: 100%;
                margin: 10px 0;
                border-collapse: collapse;
            }
            
            .info-table th,
            .info-table td {
                padding: 8px;
                text-align: left;
                border: 1px solid #e2e8f0;
            }
            
            .info-table th {
                background-color: #f7fafc;
                font-weight: bold;
            }
            
            .info-table tr:nth-child(even) {
                background-color: #f9fafb;
            }
            
            #input-container {
                display: flex;
                gap: 10px;
                padding: 10px;
                background: white;
            }
            
            #user-input {
                flex: 1;
                padding: 10px;
                border: 1px solid #e2e8f0;
                border-radius: 4px;
                font-size: 16px;
            }
            
            #send-button {
                padding: 10px 20px;
                background-color: #4299e1;
                color: white;
                border: none;
                border-radius: 4px;
                cursor: pointer;
                font-size: 16px;
            }
            
            #send-button:hover {
                background-color: #3182ce;
            }
            
            .message p {
                margin: 10px 0;
                line-height: 1.5;
            }
            
            .frost-list {
                margin: 10px 0;
                padding-left: 20px;
                list-style-type: none;
            }
            
            .frost-list li {
                margin: 8px 0;
                padding-left: 20px;
                position: relative;
                line-height: 1.6;
            }
            
            .frost-list li::before {
                content: "•";
                position: absolute;
                left: 0;
                color: #4a5568;
            }
            
            .plant-info {
                display: block;
                padding: 4px 0;
            }
            
            .plant-name {
                font-weight: 500;
                color: #2d3748;
            }
            
            .temp-info {
                color: #4a5568;
                margin-left: 5px;
            }
            
            .not-in-garden {
                color: #718096;
                font-style: italic;
            }
        </style>
        <script>
            const apiUrl = window.location.origin;
            
            function formatResponse(text) {
                // Split text into sections by double newline
                const sections = text.split('\\n\\n');
                let formattedText = '';
                
                for (const section of sections) {
                    if (!section.trim()) continue;
                    
                    const lines = section.trim().split('\\n');
                    
                    // Handle bullet points
                    if (lines[0].startsWith('-')) {
                        formattedText += '<ul class="frost-list">';
                        lines.forEach(line => {
                            if (line.startsWith('-')) {
                                const content = line.substring(1).trim();
                                if (content.includes('Not currently in')) {
                                    formattedText += `<li class="not-in-garden">${content}</li>`;
                                } else {
                                    const [plant, temp] = content.split(':');
                                    formattedText += `
                                        <li>
                                            <div class="plant-info">
                                                <span class="plant-name">${plant.trim()}</span>
                                                <span class="temp-info">${temp.trim()}</span>
                                            </div>
                                        </li>`;
                                }
                            }
                        });
                        formattedText += '</ul>';
                        continue;
                    }
                    
                    // Handle location headers (###)
                    if (lines[0].startsWith('###')) {
                        const locationName = lines[0].substring(3).trim();
                        formattedText += `<h3>${locationName}</h3>`;
                        
                        if (lines.length > 1) {
                            formattedText += '<ul>';
                            for (let i = 1; i < lines.length; i++) {
                                const line = lines[i].trim();
                                if (line.startsWith('-')) {
                                    const plantName = line.substring(1).trim();
                                    formattedText += `<li>${plantName}</li>`;
                                }
                            }
                            formattedText += '</ul>';
                        }
                        continue;
                    }
                    
                    // Handle regular text
                    if (lines.join('').trim()) {
                        formattedText += `<p>${lines.join(' ')}</p>`;
                    }
                }
                
                return formattedText;
            }

            function addMessage(sender, text, isUser) {
                const container = document.getElementById('chat-container');
                const messageDiv = document.createElement('div');
                messageDiv.className = `message ${isUser ? 'user-message' : 'bot-message'}`;
                
                if (isUser) {
                    messageDiv.innerHTML = `<strong>${sender}:</strong> ${text}`;
                } else {
                    const formattedText = formatResponse(text);
                    messageDiv.innerHTML = `<strong>${sender}:</strong> ${formattedText}`;
                }
                
                container.appendChild(messageDiv);
                container.scrollTop = container.scrollHeight;
            }

            async function sendMessage() {
                const input = document.getElementById('user-input');
                const message = input.value.trim();
                if (!message) return;

                addMessage('You', message, true);
                input.value = '';

                try {
                    const response = await fetch('/chat', {
                        method: 'POST',
                        headers: { 
                            'Content-Type': 'application/json',
                            'Accept': 'application/json'
                        },
                        body: JSON.stringify({ message: message })
                    });
                    
                    if (!response.ok) {
                        throw new Error(`HTTP error! status: ${response.status}`);
                    }
                    
                    const data = await response.json();
                    console.log('Response data:', data);
                    
                    if (data && data.response) {
                        addMessage('GardenBot', data.response, false);
                        const formattedContent = document.querySelector('.message:last-child');
                        console.log('Formatted content:', formattedContent.innerHTML);
                    } else {
                        throw new Error('Invalid response format');
                    }
                } catch (error) {
                    console.error('Error details:', error);
                    addMessage('Error', 'The service is temporarily unavailable. Please try again later.', false);
                }
            }

            document.addEventListener('DOMContentLoaded', function() {
                const sendButton = document.getElementById('send-button');
                const userInput = document.getElementById('user-input');
                
                sendButton.addEventListener('click', sendMessage);
                userInput.addEventListener('keypress', function(e) {
                    if (e.key === 'Enter') {
                        sendMessage();
                    }
                });
            });
        </script>
    </head>
    <body>
        <div id="chat-container"></div>
        <div id="input-container">
            <input type="text" id="user-input" placeholder="Type your message...">
            <button id="send-button">Send</button>
        </div>
    </body>
    </html>"""
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/terminal", response_class=HTMLResponse)
async def terminal():
    html_content = """<!DOCTYPE html>
    <html>
    <head>
        <title>GardenBot Terminal</title>
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <style>
            body {
                background: #1a1a1a;
                color: #33ff33;
                font-family: monospace;
                margin: 0;
                padding: 10px;
                font-size: 16px;
            }
            
            #terminal {
                height: calc(100vh - 100px);
                overflow-y: auto;
                white-space: pre-wrap;
                word-wrap: break-word;
                margin-bottom: 10px;
            }
            
            #input-line {
                display: flex;
                gap: 5px;
                position: fixed;
                bottom: 0;
                left: 0;
                right: 0;
                padding: 10px;
                background: #1a1a1a;
            }
            
            #prompt {
                color: #33ff33;
            }
            
            #cmd-input {
                flex: 1;
                background: transparent;
                border: none;
                color: #33ff33;
                font-family: monospace;
                font-size: 16px;
                outline: none;
            }
            
            .user-input {
                color: #33ff33;
            }
            
            .response {
                color: #ffffff;
                margin-bottom: 10px;
            }
        </style>
        <script>
            let history = [];
            let historyIndex = -1;
            
            function addToTerminal(text, isUser = false) {
                const terminal = document.getElementById('terminal');
                const div = document.createElement('div');
                div.className = isUser ? 'user-input' : 'response';
                div.textContent = isUser ? '> ' + text : text;
                terminal.appendChild(div);
                terminal.scrollTop = terminal.scrollHeight;
            }
            
            async function sendCommand(e) {
                if (e.key === 'Enter') {
                    const input = document.getElementById('cmd-input');
                    const cmd = input.value.trim();
                    
                    if (cmd) {
                        history.push(cmd);
                        historyIndex = history.length;
                        addToTerminal(cmd, true);
                        input.value = '';
                        
                        try {
                            const response = await fetch('/chat', {
                                method: 'POST',
                                headers: {
                                    'Content-Type': 'application/json'
                                },
                                body: JSON.stringify({ message: cmd })
                            });
                            
                            const data = await response.json();
                            if (data.response) {
                                addToTerminal(data.response);
                            }
                        } catch (error) {
                            addToTerminal('Error: ' + error.message);
                        }
                    }
                } else if (e.key === 'ArrowUp') {
                    e.preventDefault();
                    if (historyIndex > 0) {
                        historyIndex--;
                        document.getElementById('cmd-input').value = history[historyIndex];
                    }
                } else if (e.key === 'ArrowDown') {
                    e.preventDefault();
                    if (historyIndex < history.length - 1) {
                        historyIndex++;
                        document.getElementById('cmd-input').value = history[historyIndex];
                    } else {
                        historyIndex = history.length;
                        document.getElementById('cmd-input').value = '';
                    }
                }
            }
        </script>
    </head>
    <body>
        <div id="terminal"></div>
        <div id="input-line">
            <span id="prompt">></span>
            <input type="text" id="cmd-input" autocomplete="off" autocapitalize="off" spellcheck="false" onkeydown="sendCommand(event)">
        </div>
    </body>
    </html>"""
    return HTMLResponse(content=html_content, status_code=200)

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "GardenBot server is running"}

@app.get("/weather")
async def weather():
    """Weather endpoint for retrieving forecast and plant care advice"""
    try:
        forecast = get_weather_forecast()
        if not forecast:
            raise HTTPException(
                status_code=500,
                detail="Unable to retrieve weather forecast"
            )
        
        advice = analyze_forecast_for_plants(forecast)
        return WeatherResponse(
            forecast=forecast,
            plant_care_advice=advice
        )
    except Exception as e:
        logger.error(f"Error in weather endpoint: {e}")
        logger.error(traceback.format_exc())
        raise HTTPException(status_code=500, detail=str(e))