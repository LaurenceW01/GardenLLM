# GardenLLM Server

A FastAPI server for managing garden plants with AI assistance and weather monitoring.

## Environment Variables Required

```
OPENAI_API_KEY=your_openai_api_key
OPENWEATHER_API_KEY=your_openweather_api_key
```

## Local Development

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API keys

3. Run the server:
```bash
python run_server.py
```

## Deployment Instructions

### Deploying to Render.com

1. Create a new account on [Render.com](https://render.com)

2. Click "New +" and select "Web Service"

3. Connect your GitHub repository

4. Configure the service:
   - Name: gardenllm-server
   - Environment: Python 3
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `uvicorn web:app --host 0.0.0.0 --port $PORT`

5. Add environment variables:
   - OPENAI_API_KEY
   - OPENWEATHER_API_KEY
   - Add your Google Sheets credentials as GOOGLE_CREDENTIALS (JSON content)

6. Click "Create Web Service"

## API Endpoints

- `/chat` (POST): Send garden-related queries
- `/weather` (GET): Get weather forecast and plant care advice
- `/health` (GET): Check server status

## Security Notes

- Keep your API keys secure
- Never commit .env files or credentials
- Use environment variables for all sensitive data 