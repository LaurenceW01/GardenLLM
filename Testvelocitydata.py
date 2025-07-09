from baron_weather_velocity_api import BaronWeatherVelocityAPI
from config import BARON_API_KEY, BARON_API_SECRET

api = BaronWeatherVelocityAPI(BARON_API_KEY, BARON_API_SECRET)
hourly = api.get_hourly_forecast(hours=8)
print(f"{'Time':<8} {'Temp':<6} {'Rain':<6} {'Wind':<6} {'Description'}")
print("-" * 50)
for h in hourly:
    print(f"{h['time']:<8} {h['temperature']}°F   {h['rain_probability']}%    {h['wind_speed']} mph  {h['description']}")