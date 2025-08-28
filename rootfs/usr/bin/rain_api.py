#!/usr/bin/env python3
"""
Egyszerű csapadék API - JSON kimenet
"""

import json
import requests
from datetime import datetime

# Load configuration
with open("./data/options.json") as f:
    options = json.load(f)

api_key = options["api_key"]
lat = options["lat"]
lon = options["lon"]
units = options["units"]


def get_rain_forecast_simple():
    """
    Get simple rain forecast data.
    Returns: JSON-like dict with rain information
    """
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        forecast_data = response.json()
    except requests.RequestException as e:
        return {"error": f"API hiba: {e}"}
    
    # Napi csapadék összesítés
    daily_rain = {}
    city = forecast_data.get('city', {}).get('name', 'N/A')
    
    for item in forecast_data.get('list', []):
        dt_txt = item.get('dt_txt', '')
        if not dt_txt:
            continue
            
        date = dt_txt.split(' ')[0]
        
        # Csapadék
        rain_3h = 0
        if 'rain' in item:
            rain_3h = item['rain'].get('3h', 0)
        if 'snow' in item:
            rain_3h += item['snow'].get('3h', 0)
        
        if date not in daily_rain:
            daily_rain[date] = 0
        
        daily_rain[date] += rain_3h
    
    # Eredmény formázása
    result = {
        "timestamp": datetime.now().isoformat(),
        "location": {
            "city": city,
            "coordinates": {"lat": lat, "lon": lon}
        },
        "forecast_days": len(daily_rain),
        "daily_rain": daily_rain,
        "rainy_days": [date for date, rain in daily_rain.items() if rain > 0],
        "total_expected_rain": sum(daily_rain.values()),
        "max_daily_rain": {
            "amount": max(daily_rain.values()) if daily_rain else 0,
            "date": max(daily_rain.items(), key=lambda x: x[1])[0] if daily_rain else None
        },
        "summary": {
            "will_rain": any(rain > 0 for rain in daily_rain.values()),
            "rainy_days_count": sum(1 for rain in daily_rain.values() if rain > 0),
            "dry_days_count": sum(1 for rain in daily_rain.values() if rain == 0)
        }
    }
    
    return result


def main():
    """Main function - output JSON format"""
    
    # Get the forecast
    forecast = get_rain_forecast_simple()
    
    # Pretty print JSON
    print(json.dumps(forecast, indent=2, ensure_ascii=False))
    
    # Also print a human-readable summary
    if 'error' not in forecast:
        print("\n" + "="*40)
        print("EMBERI ÖSSZEFOGLALÓ")
        print("="*40)
        
        summary = forecast['summary']
        location = forecast['location']['city']
        
        if summary['will_rain']:
            print(f"☔ {location}-ban/ben várható eső!")
            print(f"🌧️ Esős napok: {summary['rainy_days_count']}")
            print(f"💧 Összes eső: {forecast['total_expected_rain']:.1f} mm")
            print(f"⛈️  Legcsapadékosabb nap: {forecast['max_daily_rain']['date']} ({forecast['max_daily_rain']['amount']:.1f} mm)")
            
            print("\nEsős napok részletesen:")
            for date in forecast['rainy_days']:
                rain_amount = forecast['daily_rain'][date]
                print(f"  📅 {date}: {rain_amount:.1f} mm")
        else:
            print(f"☀️ {location}-ban/ben NEM várható eső!")
            print(f"🌞 Száraz napok: {summary['dry_days_count']}")
            print("🏖️  Kiváló idő a szabadtéri tevékenységekhez!")


if __name__ == "__main__":
    main()
