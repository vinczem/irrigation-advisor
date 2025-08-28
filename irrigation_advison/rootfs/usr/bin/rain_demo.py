#!/usr/bin/env python3
"""
Demo szkript - Esőzés ellenőrzés példa
"""

import json
import requests
from datetime import datetime

# Load configuration options
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
        print(f"Hiba: {e}")
        return None


def is_it_raining():
    """
    Check if it's currently raining.
    Returns: (is_raining, rain_amount, description, city, temperature)
    """
    weather_data = get_current_weather()
    
    if not weather_data:
        return None, None, "Nincs adat", "N/A", "N/A"
    
    is_raining = False
    rain_amount = 0
    
    # Check for rain in the data
    if 'rain' in weather_data:
        rain_info = weather_data['rain']
        rain_amount = rain_info.get('1h', rain_info.get('3h', 0))
        if rain_amount > 0:
            is_raining = True
    
    # Check weather codes for rain
    weather_conditions = weather_data.get('weather', [])
    rain_codes = [200, 201, 202, 210, 211, 212, 221, 230, 231, 232,
                  300, 301, 302, 310, 311, 312, 313, 314, 321,
                  500, 501, 502, 503, 504, 511, 520, 521, 522, 531]
    
    description = "nincs leírás"
    for condition in weather_conditions:
        weather_id = condition.get('id', 0)
        description = condition.get('description', 'ismeretlen')
        
        if weather_id in rain_codes:
            is_raining = True
            break
    
    city = weather_data.get('name', 'Ismeretlen')
    temperature = weather_data.get('main', {}).get('temp', 'N/A')
    
    return is_raining, rain_amount, description, city, temperature


def main():
    """Demo - különböző formátumokban mutatja az esőzés állapotát"""
    
    print("🌧️" * 25)
    print("ESŐZÉS ELLENŐRZÉS DEMO")
    print("🌧️" * 25)
    
    now = datetime.now()
    print(f"📅 Időpont: {now.strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    # 1. Alapvető ellenőrzés
    print("1️⃣ ALAPVETŐ ELLENŐRZÉS:")
    print("-" * 25)
    
    result = is_it_raining()
    is_raining, rain_amount, desc, city, temp = result
    
    if is_raining is None:
        print("❌ Nem sikerült lekérdezni az időjárást!")
        return
    
    # Egyszerű válasz
    status = "ESIK" if is_raining else "NEM ESIK"
    emoji = "☔" if is_raining else "☀️"
    
    print(f"{emoji} Az eső jelenleg: {status}")
    print(f"📍 Helyszín: {city}")
    print(f"🌡️ Hőmérséklet: {temp}°C")
    print(f"🌤️ Időjárás: {desc}")
    
    if rain_amount > 0:
        print(f"🌧️ Csapadékmennyiség: {rain_amount} mm")
    
    print()
    
    # 2. Feltételes logika demo
    print("2️⃣ FELTÉTELES LOGIKA DEMO:")
    print("-" * 30)
    
    if is_raining:
        print("🏠 Javaslat: Maradj otthon vagy vigyél esernyőt!")
        if rain_amount > 5:
            print("⚠️ Erős esőzés! Kerüld a kinti tevékenységeket!")
        elif rain_amount > 0:
            print("🌂 Enyhe esőzés, esernyő ajánlott.")
    else:
        print("🚶 Javaslat: Jó idő egy sétához!")
        if temp > 25:
            print("🌡️ Meleg van, gondolj a naptejre!")
        elif temp < 10:
            print("🧥 Hideg van, öltözz fel melegen!")
    
    print()
    
    # 3. JSON formátum (API-like)
    print("3️⃣ JSON FORMÁTUM:")
    print("-" * 20)
    
    json_response = {
        "timestamp": now.isoformat(),
        "location": {
            "city": city,
            "coordinates": {"lat": lat, "lon": lon}
        },
        "weather": {
            "is_raining": is_raining,
            "rain_amount_mm": rain_amount,
            "description": desc,
            "temperature_celsius": temp
        },
        "recommendation": "stay_inside" if is_raining else "good_for_outside"
    }
    
    print(json.dumps(json_response, indent=2, ensure_ascii=False))
    
    print("\n" + "🌧️" * 25)


if __name__ == "__main__":
    main()
