#!/usr/bin/env python3
"""
Egyszerű teszt az esőzés függvényekhez
"""

import json
import requests

# Load config
with open("./data/options.json") as f:
    options = json.load(f)

api_key = options["api_key"]
lat = options["lat"]
lon = options["lon"]
units = options["units"]


def will_it_rain_next_5_days():
    """
    Egyszerű kérdés: esni fog-e az elkövetkező 5 napban?
    Visszatérés: (bool, list_of_rainy_days, total_rain_mm)
    """
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except:
        return None, [], 0
    
    # Napi csapadék számítás
    daily_rain = {}
    
    for item in data.get('list', []):
        dt_txt = item.get('dt_txt', '')
        if not dt_txt:
            continue
            
        date = dt_txt.split(' ')[0]
        
        rain_3h = 0
        if 'rain' in item:
            rain_3h = item['rain'].get('3h', 0)
        if 'snow' in item:
            rain_3h += item['snow'].get('3h', 0)
        
        if date not in daily_rain:
            daily_rain[date] = 0
        daily_rain[date] += rain_3h
    
    # Eredmények
    rainy_days = [date for date, rain in daily_rain.items() if rain > 0]
    total_rain = sum(daily_rain.values())
    will_rain = len(rainy_days) > 0
    
    return will_rain, rainy_days, total_rain


def get_rain_by_day():
    """
    Visszaadja hogy melyik nap mennyi eső esik.
    Visszatérés: dict {date: rain_mm}
    """
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
    except:
        return None
    
    daily_rain = {}
    
    for item in data.get('list', []):
        dt_txt = item.get('dt_txt', '')
        if not dt_txt:
            continue
            
        date = dt_txt.split(' ')[0]
        
        rain_3h = 0
        if 'rain' in item:
            rain_3h = item['rain'].get('3h', 0)
        if 'snow' in item:
            rain_3h += item['snow'].get('3h', 0)
        
        if date not in daily_rain:
            daily_rain[date] = 0
        daily_rain[date] += rain_3h
    
    return daily_rain


def main():
    """Teszt futtatása"""
    
    print("🧪 ESŐZÉS TESZTEK")
    print("=" * 20)
    
    # 1. Alapkérdés: lesz-e eső?
    print("1️⃣ Esni fog-e az elkövetkező 5 napban?")
    will_rain, rainy_days, total_rain = will_it_rain_next_5_days()
    
    if will_rain is None:
        print("❌ Hiba: Nem sikerült lekérdezni az előrejelzést")
    elif will_rain:
        print(f"☔ IGEN! {len(rainy_days)} napon lesz eső")
        print(f"💧 Összes eső: {total_rain:.1f} mm")
        print(f"📅 Esős napok: {', '.join(rainy_days)}")
    else:
        print("☀️ NEM, nem lesz eső!")
    
    print()
    
    # 2. Részletes bontás
    print("2️⃣ Melyik nap mennyi eső?")
    rain_by_day = get_rain_by_day()
    
    if rain_by_day:
        for date, rain_mm in rain_by_day.items():
            if rain_mm > 0:
                emoji = "🌧️" if rain_mm > 5 else "🌦️"
                print(f"{emoji} {date}: {rain_mm:.1f} mm")
            else:
                print(f"☀️ {date}: 0.0 mm")
    else:
        print("❌ Nem sikerült lekérdezni az adatokat")
    
    print()
    
    # 3. Összefoglaló ajánlás
    print("3️⃣ Ajánlás:")
    if will_rain:
        print("🌂 Készülj fel esős napokra!")
        if total_rain > 20:
            print("⚠️ Jelentős csapadék várható!")
        elif total_rain > 5:
            print("🌧️ Mérsékelt esőzés várható")
        else:
            print("🌦️ Kis mennyiségű eső várható")
    else:
        print("🌞 Kiváló idő! Nincs szükség esernyőre")
    
    print()
    print("=" * 20)


if __name__ == "__main__":
    main()
