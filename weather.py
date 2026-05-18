"""OpenWeatherMap forecast for the next ~14 hours (hourly)."""
import datetime
import requests
import pytz

OWM_URL = "https://api.openweathermap.org/data/2.5/forecast"

# Weather condition codes: https://openweathermap.org/weather-conditions
RAIN_CODES = {200, 201, 202, 210, 211, 212, 221, 230, 231, 232,  # thunderstorm
              300, 301, 302, 310, 311, 312, 313, 314, 321,          # drizzle
              500, 501, 502, 503, 504, 511, 520, 521, 522, 531}     # rain


def _weather_icon(weather_id: int, rain: bool) -> str:
    if rain or weather_id in RAIN_CODES:
        return "🌧"
    if weather_id >= 600:
        return "❄️"
    if weather_id >= 800:
        return "☀️" if weather_id == 800 else "⛅"
    if weather_id >= 700:
        return "🌫"
    return "☁️"


def fetch_hourly_forecast(api_key: str, city: str, timezone: str) -> dict[str, dict]:
    """
    Returns dict keyed by "HH:MM" (today's hours) with:
      { temp, feels_like, rain, icon }
    """
    r = requests.get(
        OWM_URL,
        params={"q": city, "appid": api_key, "units": "metric", "cnt": 14},
        timeout=15,
    )
    r.raise_for_status()

    tz = pytz.timezone(timezone)
    today = datetime.datetime.now(tz).date()
    result = {}

    for item in r.json()["list"]:
        dt = datetime.datetime.fromtimestamp(item["dt"], tz=tz)
        if dt.date() != today:
            continue
        time_key = dt.strftime("%H:%M")
        rain_mm = item.get("rain", {}).get("3h", 0.0)
        weather_id = item["weather"][0]["id"]
        result[time_key] = {
            "temp": round(item["main"]["temp"]),
            "feels_like": round(item["main"]["feels_like"]),
            "rain_mm": rain_mm,
            "rain": rain_mm > 0 or weather_id in RAIN_CODES,
            "icon": _weather_icon(weather_id, rain_mm > 0),
            "description": item["weather"][0]["description"],
        }

    return result


def get_weather_for_slot(slot_time: str, forecast: dict[str, dict]) -> dict | None:
    """
    Match a slot time (e.g. "10:00") to the nearest forecast entry (3h buckets).
    """
    if not forecast:
        return None

    slot_h, slot_m = map(int, slot_time.split(":"))
    slot_minutes = slot_h * 60 + slot_m

    best_key = None
    best_diff = float("inf")
    for key in forecast:
        h, m = map(int, key.split(":"))
        diff = abs(h * 60 + m - slot_minutes)
        if diff < best_diff:
            best_diff = diff
            best_key = key

    # Use forecast entry if it's within 2 hours
    if best_diff <= 120:
        return forecast[best_key]
    return None
