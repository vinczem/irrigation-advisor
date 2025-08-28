#!/usr/bin/env python3
"""
Egyszerű szkript a jelenlegi esőzés ellenőrzésére.
"""

import json
import requests

# Load configuration options from a JSON file
with open("./data/options.json") as f:
    options = json.load(f)

api_key = options["api_key"]
lat = options["lat"]
lon = options["lon"]
units = options["units"]


def get_current_weather():
    """Fetch current weather data from OpenWeatherMap API."""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Hiba a jelenlegi időjárás lekérdezésekor: {e}")
        return None


def is_it_raining_now():
    """
    Egyszerű függvény: esik-e most az eső?
    Visszatérés: True/False vagy None hiba esetén
    """
    current_weather = get_current_weather()
    
    if not current_weather:
        return None
    
    # Esőzés ellenőrzése
    is_raining = False
    
    # 1. Ellenőrizd a 'rain' mezőt
    if 'rain' in current_weather:
        rain_info = current_weather['rain']
        if rain_info.get('1h', 0) > 0 or rain_info.get('3h', 0) > 0:
            is_raining = True
    
    # 2. Ellenőrizd az időjárás kódokat
    weather_conditions = current_weather.get('weather', [])
    rain_codes = [200, 201, 202, 210, 211, 212, 221, 230, 231, 232,  # vihar esővel
                  300, 301, 302, 310, 311, 312, 313, 314, 321,        # szitálás
                  500, 501, 502, 503, 504, 511, 520, 521, 522, 531]  # eső
    
    for condition in weather_conditions:
        weather_id = condition.get('id', 0)
        if weather_id in rain_codes:
            is_raining = True
            break
    
    return is_raining


def main():
    """Fő függvény - egyszerű esőzés teszt"""
    print("🌧️ ESŐZÉS ELLENŐRZÉS")
    print("=" * 25)
    
    result = is_it_raining_now()
    
    if result is None:
        print("❌ Hiba: Nem sikerült lekérdezni az időjárást!")
    elif result:
        print("☔ IGEN - ESIK AZ ESŐ!")
    else:
        print("☀️ NEM - Nem esik az eső")
    
    # További részletek
    weather_data = get_current_weather()
    if weather_data:
        temp = weather_data.get('main', {}).get('temp', 'N/A')
        desc = weather_data.get('weather', [{}])[0].get('description', 'N/A')
        print(f"📍 {weather_data.get('name', 'N/A')}")
        print(f"🌡️ {temp}°C")
        print(f"🌤️ {desc}")


if __name__ == "__main__":
    main()
