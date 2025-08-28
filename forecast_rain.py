#!/usr/bin/env python3
"""
5 napos csapadék előrejelzés szkript
"""

import json
import requests
from datetime import datetime, timedelta

# Load configuration options from a JSON file
with open("./data/options.json") as f:
    options = json.load(f)

api_key = options["api_key"]
lat = options["lat"]
lon = options["lon"]
units = options["units"]


def get_5day_forecast():
    """Fetch 5-day weather forecast from OpenWeatherMap API."""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Hiba az előrejelzés lekérdezésekor: {e}")
        return None


def extract_daily_rain_forecast():
    """
    Extract daily rain amounts from 5-day forecast.
    Returns: list of dictionaries with daily rain data
    """
    forecast_data = get_5day_forecast()
    
    if not forecast_data:
        return None
    
    # Napi csapadék adatok gyűjtése
    daily_rain = {}
    
    for item in forecast_data.get('list', []):
        # Dátum kinyerése (YYYY-MM-DD formátum)
        dt_txt = item.get('dt_txt', '')
        if not dt_txt:
            continue
            
        date = dt_txt.split(' ')[0]  # "2025-08-24 15:00:00" -> "2025-08-24"
        
        # Csapadék adatok
        rain_3h = 0
        if 'rain' in item:
            rain_3h = item['rain'].get('3h', 0)
        
        # Hó is csapadék
        if 'snow' in item:
            rain_3h += item['snow'].get('3h', 0)
        
        # Napi összegzés
        if date not in daily_rain:
            daily_rain[date] = {
                'date': date,
                'total_rain_mm': 0,
                'rain_periods': 0,
                'max_temp': float('-inf'),
                'min_temp': float('inf'),
                'descriptions': set(),
                'city': forecast_data.get('city', {}).get('name', 'N/A')
            }
        
        # Csapadék hozzáadása
        daily_rain[date]['total_rain_mm'] += rain_3h
        
        if rain_3h > 0:
            daily_rain[date]['rain_periods'] += 1
        
        # Hőmérséklet min/max
        temp = item.get('main', {}).get('temp', 0)
        daily_rain[date]['max_temp'] = max(daily_rain[date]['max_temp'], temp)
        daily_rain[date]['min_temp'] = min(daily_rain[date]['min_temp'], temp)
        
        # Időjárás leírások
        for weather in item.get('weather', []):
            daily_rain[date]['descriptions'].add(weather.get('description', ''))
    
    # Rendezés dátum szerint és lista formátumra konvertálás
    sorted_days = []
    for date in sorted(daily_rain.keys()):
        day_data = daily_rain[date]
        
        # Descriptions set -> string
        day_data['descriptions'] = ', '.join(day_data['descriptions'])
        
        # Handle infinite values
        if day_data['max_temp'] == float('-inf'):
            day_data['max_temp'] = 'N/A'
        if day_data['min_temp'] == float('inf'):
            day_data['min_temp'] = 'N/A'
        
        sorted_days.append(day_data)
    
    return sorted_days


def get_rainy_days_only():
    """Get only the rainy days from the 5-day forecast."""
    daily_forecast = extract_daily_rain_forecast()
    
    if not daily_forecast:
        return None
    
    rainy_days = [day for day in daily_forecast if day['total_rain_mm'] > 0]
    return rainy_days


def get_rain_amounts_by_day():
    """
    Simple function to get rain amounts for each day.
    Returns: dict with date -> rain_mm mapping
    """
    daily_forecast = extract_daily_rain_forecast()
    
    if not daily_forecast:
        return None
    
    rain_by_day = {}
    for day in daily_forecast:
        rain_by_day[day['date']] = day['total_rain_mm']
    
    return rain_by_day


def main():
    """Main function - demonstrate rain forecast functionality"""
    
    print("🌦️" * 20)
    print("5 NAPOS CSAPADÉK ELŐREJELZÉS")
    print("🌦️" * 20)
    
    # 1. Alapvető adatok
    daily_forecast = extract_daily_rain_forecast()
    
    if not daily_forecast:
        print("❌ Nem sikerült lekérdezni az előrejelzést!")
        return
    
    city = daily_forecast[0]['city']
    print(f"📍 Helyszín: {city}")
    print(f"📅 Mai dátum: {datetime.now().strftime('%Y-%m-%d')}")
    print()
    
    # 2. Napi bontás
    print("📊 NAPI CSAPADÉK ELŐREJELZÉS:")
    print("-" * 35)
    
    for day in daily_forecast:
        date = day['date']
        rain_mm = day['total_rain_mm']
        
        if rain_mm > 0:
            if rain_mm > 10:
                icon = "🌧️"
                intensity = "erős eső"
            elif rain_mm > 2:
                icon = "🌦️"
                intensity = "mérsékelt eső"
            else:
                icon = "🌦️"
                intensity = "gyenge eső"
            
            print(f"{icon} {date}: {rain_mm:.1f} mm ({intensity})")
        else:
            print(f"☀️ {date}: 0.0 mm (száraz)")
    
    print()
    
    # 3. Csak az esős napok
    rainy_days = get_rainy_days_only()
    
    if rainy_days:
        print("☔ ESŐS NAPOK RÉSZLETESEN:")
        print("-" * 30)
        
        for day in rainy_days:
            print(f"📅 {day['date']}")
            print(f"   💧 Csapadék: {day['total_rain_mm']:.1f} mm")
            print(f"   🌡️  Hőmérséklet: {day['min_temp']:.1f}°C - {day['max_temp']:.1f}°C")
            print(f"   ⏰ Esős periódusok: {day['rain_periods']} db (3h-ás)")
            print(f"   🌤️  Időjárás: {day['descriptions']}")
            print()
    else:
        print("☀️ NINCS ESŐS NAP AZ ELŐREJELZÉSBEN!")
        print("-" * 40)
        print("🌞 Jó idő várható az elkövetkező napokban!")
        print()
    
    # 4. Gyors összefoglaló
    rain_amounts = get_rain_amounts_by_day()
    total_rain = sum(rain_amounts.values())
    rainy_days_count = sum(1 for rain in rain_amounts.values() if rain > 0)
    
    print("📋 ÖSSZEFOGLALÓ:")
    print("-" * 15)
    print(f"🌧️ Összes várható eső: {total_rain:.1f} mm")
    print(f"☔ Esős napok: {rainy_days_count} / {len(daily_forecast)}")
    
    if rainy_days_count > 0:
        heaviest_rain = max(rain_amounts.values())
        heaviest_day = [day for day, rain in rain_amounts.items() if rain == heaviest_rain][0]
        print(f"⛈️  Legcsapadékosabb: {heaviest_day} ({heaviest_rain:.1f} mm)")
    
    print()
    print("🌦️" * 20)


if __name__ == "__main__":
    main()
