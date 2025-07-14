# Weather Context Integration Plan

## Objective
Enable the AI assistant to answer user questions with awareness of both current weather and short-term forecast data, by injecting concise weather context into the conversation history or prompt. This will allow the AI to provide more accurate, context-aware gardening advice (e.g., watering, frost, rain, etc.).

---

## Key Requirements
- **Current weather** and **short-term forecast** must be available to the AI for every user question.
- **Data passed to the AI must be concise** to avoid prompt bloat and excessive token usage.
- **Weather context should be updated** for each user query, reflecting the latest available data.

---

## Implementation Steps

### 1. Data Collection
- Use existing backend functions:
  - `get_current_weather()` for current conditions (temperature, humidity, description, wind, etc.)
  - `get_hourly_forecast()` or similar for the next 12–24 hours (temperature, rain chance, etc.)

### 2. Data Summarization
- **Current Weather:**
  - Format as a single sentence, e.g.:
    - `"Current weather in Houston: 78°F, partly cloudy, humidity 60%, wind 10 mph."`
- **Forecast:**
  - Summarize only the most relevant details:
    - Next 12–24 hours, or until the end of the next day
    - Focus on rain probability, temperature extremes, and notable events (e.g., frost, storms)
  - Example:
    - `"Forecast: 40% chance of rain this afternoon (2–5pm), high 82°F, low 68°F. Tomorrow: mostly sunny, high 80°F."`
  - If possible, highlight only significant changes (e.g., "Rain expected after 3pm.")

### 3. Context Injection
- **Before sending a user question to the AI:**
  - Insert the weather summary as one or more `system` or `context` messages at the start of the conversation history for that turn.
  - Example:
    ```json
    [
      {"role": "system", "content": "Current weather in Houston: 78°F, partly cloudy, humidity 60%, wind 10 mph."},
      {"role": "system", "content": "Forecast: 40% chance of rain this afternoon, high 82°F, low 68°F."},
      {"role": "user", "content": "Should I water my tomatoes today?"}
    ]
    ```
- **If the user is not asking about weather:**
  - Still include the weather context, as it may be relevant to many gardening questions.

### 4. Data Size Management
- **Limit the forecast to the next 24 hours or until the end of the next day.**
- **Avoid sending raw hourly data.** Instead, summarize into a few key sentences.
- **If the forecast is uneventful (e.g., "No rain expected, mild temperatures"), keep it brief.**
- **If the forecast is long, truncate or summarize further.**

### 5. Fallbacks
- If weather data is unavailable, insert a message like:
  - `"Weather data is currently unavailable. Answer based on general Houston climate."`

---

## Example Conversation Context
```
[
  {"role": "system", "content": "Current weather in Houston: 78°F, partly cloudy, humidity 60%, wind 10 mph."},
  {"role": "system", "content": "Forecast: 40% chance of rain after 3pm, high 82°F, low 68°F."},
  {"role": "user", "content": "Should I water my tomatoes today?"}
]
```

---

## Summary
- Always provide the AI with a concise summary of current weather and forecast.
- Keep the context short and relevant—avoid raw data dumps.
- Update the weather context for every user query.
- This approach will allow the AI to give more accurate, context-aware gardening advice without excessive prompt size. 