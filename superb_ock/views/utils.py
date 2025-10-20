"""
Utility functions for views.
"""
import json
from django.core.serializers.json import DjangoJSONEncoder
from requests import request


def jsonify(query):
    """Convert query to JSON."""
    return json.dumps(list(query), cls=DjangoJSONEncoder)


def getWeather(lat, long):
    """
    Get weather information for given coordinates.

    Args:
        lat: Latitude
        long: Longitude

    Returns:
        Tuple of (weather_data, weather_description)
    """
    weather_codes = {
        "0": "Clear sky ☀️",
        "1": "Mainly Clear ☀️",
        "2": "Partly Cloudy",
        "3": "Overcast",
        "45": "Fog",
        "48": "Depositing Rime Fog",
        "51": "Light Drizzle",
        "53": "Moderate Drizzle",
        "55": "Dense Drizzle",
        "56": "Light Freezing Dizzle",
        "57": "Dense Freezing Drizzle",
        "61": "Slight Rain",
        "63": "Moderate Rain",
        "65": "Heavy Rain",
        "66": "Light Freezing Rain",
        "67": "Heavy Freezing Rain",
        "71": "Slight Snowfall",
        "73": "Moderate Snowfall",
        "75": "Heavy Snowfall",
        "77": "Snow Grains",
        "80": "Slight Rain Showers",
        "81": "Moderate Rain Showers",
        "82": "Violent Rain Showers",
        "85": "Sight Snow Showers",
        "95": "Slight Thunderstorms",
        "96": "Moderate Thunderstorms",
        "99": "Thunderstorms with hail",
    }

    weather = request(
        "GET",
        f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={long}&current=temperature_2m,weather_code",
    ).json()
    return [weather, weather_codes[f"{weather['current']['weather_code']}"]]
