import json
from urllib import response
import requests
import time
from datetime import datetime, timedelta



# Load configuration options from a JSON file
with open("./data/options.json") as f:
    options = json.load(f)

api_key = options["api_key"]
lat = options["lat"]
lon = options["lon"]
units = options["units"]



def get_daily_aggregation(day):
    """
    Fetch daily weather aggregation from OpenWeatherMap API.
    param 'day': The date for which to fetch the weather aggregation (format: YYYY-MM-DD)
    """
    url = f"https://api.openweathermap.org/data/3.0/onecall/day_summary?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu&date={day}"

    payload = {}
    headers = {}

    response = requests.request("GET", url, headers=headers, data=payload)

    return response.text


def parse_weather_data(raw_data):
    """
    Parse the raw weather data JSON response into a readable format.
    param 'raw_data': Raw JSON string from the API response
    """
    try:
        data = json.loads(raw_data)
        return data
    except json.JSONDecodeError as e:
        print(f"Hiba a JSON feldolgozásában: {e}")
        return None


def format_weather_data(weather_data):
    """
    Format the weather data into a human-readable string.
    param 'weather_data': Parsed weather data dictionary
    """
    if not weather_data:
        return "Nincs elérhető időjárás adat"
    
    formatted = []
    formatted.append(f"Dátum: {weather_data.get('date', 'N/A')}")
    formatted.append(f"Koordináták: {weather_data.get('lat', 'N/A')}, {weather_data.get('lon', 'N/A')}")
    formatted.append(f"Időzóna: {weather_data.get('tz', 'N/A')}")
    
    # Hőmérséklet adatok
    if 'temperature' in weather_data:
        temp = weather_data['temperature']
        formatted.append("\nHŐMÉRSÉKLET:")
        formatted.append(f" - Minimum: {temp.get('min', 'N/A')}°C")
        formatted.append(f" - Maximum: {temp.get('max', 'N/A')}°C")
        formatted.append(f" - Reggel: {temp.get('morning', 'N/A')}°C")
        formatted.append(f" - Délután: {temp.get('afternoon', 'N/A')}°C")
        formatted.append(f" - Este: {temp.get('evening', 'N/A')}°C")
        formatted.append(f" - Éjszaka: {temp.get('night', 'N/A')}°C")
    
    # Páratartalom
    if 'humidity' in weather_data:
        humidity = weather_data['humidity']
        formatted.append("\nPÁRATARTALOM:")
        formatted.append(f" - Délután: {humidity.get('afternoon', 'N/A')}%")
    
    # Légnyomás
    if 'pressure' in weather_data:
        pressure = weather_data['pressure']
        formatted.append("\nLÉGNYOMÁS:")
        formatted.append(f" - Délután: {pressure.get('afternoon', 'N/A')} hPa")
    
    # Csapadék
    if 'precipitation' in weather_data:
        precip = weather_data['precipitation']
        formatted.append("\nCSAPADÉK:")
        formatted.append(f" - Összesen: {precip.get('total', 'N/A')} mm")
    
    # Szél
    if 'wind' in weather_data and 'max' in weather_data['wind']:
        wind = weather_data['wind']['max']
        formatted.append("\nSZÉL:")
        formatted.append(f" - Maximum sebesség: {wind.get('speed', 'N/A')} m/s")
        formatted.append(f" - Irány: {wind.get('direction', 'N/A')}°")
    
    # Felhőzet
    if 'cloud_cover' in weather_data:
        cloud = weather_data['cloud_cover']
        formatted.append("\nFELHŐZET:")
        formatted.append(f" - Délután: {cloud.get('afternoon', 'N/A')}%")
    
    return "\n".join(formatted)


def get_historical_weather_range(start_date, end_date):
    """
    Get historical weather data for a range of dates.
    param 'start_date': Start date in YYYY-MM-DD format
    param 'end_date': End date in YYYY-MM-DD format
    """
    start = datetime.strptime(start_date, "%Y-%m-%d")
    end = datetime.strptime(end_date, "%Y-%m-%d")
    current = start
    
    weather_data = []
    
    while current <= end:
        date_str = current.strftime("%Y-%m-%d")
        print(f"Időjárás adatok lekérdezése: {date_str}")
        
        raw_data = get_daily_aggregation(date_str)
        parsed_data = parse_weather_data(raw_data)
        
        if parsed_data:
            weather_data.append(parsed_data)
        
        current += timedelta(days=1)
        # Kis szünet az API hívások között
        time.sleep(0.1)
    
    return weather_data


def get_current_weather():
    """
    Fetch current weather data from OpenWeatherMap API.
    Returns current weather conditions including rain status.
    """
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        print(f"Hiba a jelenlegi időjárás lekérdezésekor: {e}")
        return None


def is_it_raining():
    """
    Check if it's currently raining.
    Returns a tuple: (is_raining: bool, rain_info: dict, weather_description: str, additional_info: dict)
    """
    current_weather = get_current_weather()
    
    if not current_weather:
        return None, None, "Nincs elérhető időjárás adat", {}
    
    # Esőzés ellenőrzése - több módszer kombinálása
    is_raining = False
    rain_info = {}
    weather_description = ""
    
    # 1. Ellenőrizd a 'rain' mezőt (csapadék mm-ben az elmúlt 1-3 órában)
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
        weather_description = condition.get('description', '')
        
        if weather_id in rain_codes:
            is_raining = True
            break
    
    # 3. További információk gyűjtése
    additional_info = {
        'temperature': current_weather.get('main', {}).get('temp', 'N/A'),
        'humidity': current_weather.get('main', {}).get('humidity', 'N/A'),
        'clouds': current_weather.get('clouds', {}).get('all', 'N/A'),
        'wind_speed': current_weather.get('wind', {}).get('speed', 'N/A'),
        'visibility': current_weather.get('visibility', 'N/A') / 1000 if current_weather.get('visibility') else 'N/A',
        'city': current_weather.get('name', 'N/A')
    }
    
    return is_raining, rain_info, weather_description, additional_info


def format_rain_status():
    """
    Format and display current rain status with detailed information.
    """
    print("🌧️" * 20)
    print("JELENLEGI ESŐZÉS ELLENŐRZÉSE")
    print("🌧️" * 20)
    
    result = is_it_raining()
    
    if result[0] is None:
        print("❌ Nem sikerült lekérdezni az aktuális időjárást!")
        return
    
    is_raining, rain_info, weather_desc, additional_info = result
    
    # Fő válasz
    if is_raining:
        print("☔ IGEN, JELENLEG ESIK AZ ESŐ! ☔")
        print(f"🌦️  Időjárás leírása: {weather_desc}")
        
        if rain_info:
            if '1h' in rain_info:
                print(f"🌧️  Csapadék az elmúlt 1 órában: {rain_info['1h']} mm")
            if '3h' in rain_info:
                print(f"🌧️  Csapadék az elmúlt 3 órában: {rain_info['3h']} mm")
    else:
        print("☀️ NEM, JELENLEG NEM ESIK AZ ESŐ")
        print(f"🌤️  Időjárás leírása: {weather_desc}")
    
    # További részletek
    print(f"\n📍 Helyszín: {additional_info['city']}")
    print(f"🌡️  Hőmérséklet: {additional_info['temperature']}°C")
    print(f"💧 Páratartalom: {additional_info['humidity']}%")
    print(f"☁️  Felhőzet: {additional_info['clouds']}%")
    print(f"🌬️  Szélsebesség: {additional_info['wind_speed']} m/s")
    
    if additional_info['visibility'] != 'N/A':
        print(f"👁️  Látótávolság: {additional_info['visibility']} km")
    
    print("🌧️" * 20)


def is_raining_simple():
    """
    Egyszerű wrapper függvény: esik-e az eső?
    Visszatérés: True, False, vagy None hiba esetén
    """
    result = is_it_raining()
    return result[0] if result else None


def get_5day_forecast():
    """
    Fetch 5-day weather forecast from OpenWeatherMap API.
    Returns 5-day/3-hour forecast data.
    """
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
        
        # Snow is also precipitation
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


def get_rainy_days_forecast():
    """
    Get only the rainy days from the 5-day forecast.
    Returns: list of days with expected rain
    """
    daily_forecast = extract_daily_rain_forecast()
    
    if not daily_forecast:
        return None
    
    rainy_days = [day for day in daily_forecast if day['total_rain_mm'] > 0]
    return rainy_days


def format_5day_rain_forecast():
    """
    Format and display 5-day rain forecast in a readable format.
    """
    print("🌦️" * 25)
    print("5 NAPOS CSAPADÉK ELŐREJELZÉS")
    print("🌦️" * 25)
    
    daily_forecast = extract_daily_rain_forecast()
    
    if not daily_forecast:
        print("❌ Nem sikerült lekérdezni az előrejelzést!")
        return
    
    city = daily_forecast[0]['city'] if daily_forecast else 'N/A'
    print(f"📍 Helyszín: {city}")
    print(f"📅 Időszak: {daily_forecast[0]['date']} - {daily_forecast[-1]['date']}")
    print()
    
    total_expected_rain = 0
    rainy_days_count = 0
    
    for i, day in enumerate(daily_forecast, 1):
        date = day['date']
        rain_mm = day['total_rain_mm']
        rain_periods = day['rain_periods']
        min_temp = day['min_temp']
        max_temp = day['max_temp']
        descriptions = day['descriptions']
        
        # Napi kijelzés
        if rain_mm > 0:
            rain_icon = "🌧️" if rain_mm > 5 else "🌦️"
            rainy_days_count += 1
        else:
            rain_icon = "☀️" if 'tiszta' in descriptions or 'derült' in descriptions else "⛅"
        
        print(f"{rain_icon} {i}. NAP ({date}):")
        print(f"   💧 Várható csapadék: {rain_mm:.1f} mm")
        
        if rain_periods > 0:
            print(f"   ⏰ Esős időszakok: {rain_periods} (3 órás periódusok)")
        
        if min_temp != 'N/A' and max_temp != 'N/A':
            print(f"   🌡️  Hőmérséklet: {min_temp:.1f}°C - {max_temp:.1f}°C")
        
        print(f"   🌤️  Időjárás: {descriptions}")
        print()
        
        total_expected_rain += rain_mm
    
    # Összesítő
    print("📊 ÖSSZESÍTŐ:")
    print("-" * 15)
    print(f"🌧️ Összes várható csapadék: {total_expected_rain:.1f} mm")
    print(f"☔ Esős napok száma: {rainy_days_count} / {len(daily_forecast)}")
    
    if rainy_days_count > 0:
        avg_rain = total_expected_rain / rainy_days_count
        print(f"📈 Átlagos csapadék (esős napokon): {avg_rain:.1f} mm/nap")
    
    print("🌦️" * 25)


def get_rain_summary():
    """
    Get a simple summary of upcoming rain.
    Returns: dict with summary information
    """
    rainy_days = get_rainy_days_forecast()
    
    if not rainy_days:
        return None
    
    total_rain = sum(day['total_rain_mm'] for day in rainy_days)
    heaviest_day = max(rainy_days, key=lambda x: x['total_rain_mm'])
    
    return {
        'rainy_days_count': len(rainy_days),
        'total_rain_mm': total_rain,
        'heaviest_day': {
            'date': heaviest_day['date'],
            'rain_mm': heaviest_day['total_rain_mm']
        },
        'rainy_dates': [day['date'] for day in rainy_days]
    }



### Időjárás adatok lekérdezése és feldolgozása
today = time.strftime("%Y-%m-%d")
two_days_ago = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400 * 2))
yesterday = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400))

print("="*60)
print("MÚLTBÉLI IDŐJÁRÁS ADATOK FELDOLGOZÁSA")
print("="*60)

# Példa: utolsó 5 nap adatainak lekérdezése
print("\n\n" + "="*60)
print("UTOLSÓ 5 NAP IDŐJÁRÁS ÖSSZESÍTŐ")
print("="*60)

five_days_ago = time.strftime("%Y-%m-%d", time.gmtime(time.time() - 86400 * 5))
historical_data = get_historical_weather_range(five_days_ago, yesterday)

for i, day_data in enumerate(historical_data):
    print(f"\n{i+1}. NAP:")
    print("-" * 30)
    print(format_weather_data(day_data))

# Egyszerű statisztikai összesítés
if historical_data:
    print("\n\n" + "="*60)
    print("STATISZTIKAI ÖSSZESÍTŐ")
    print("="*60)
    
    temps_min = [day.get('temperature', {}).get('min', 0) for day in historical_data if day.get('temperature', {}).get('min')]
    temps_max = [day.get('temperature', {}).get('max', 0) for day in historical_data if day.get('temperature', {}).get('max')]
    precipitations = [day.get('precipitation', {}).get('total', 0) for day in historical_data if day.get('precipitation', {}).get('total')]
    
    if temps_min:
        print(f"🌡️  Legalacsonyabb minimum hőmérséklet: {min(temps_min):.2f}°C")
        print(f"🌡️  Legmagasabb minimum hőmérséklet: {max(temps_min):.2f}°C")
        print(f"🌡️  Átlagos minimum hőmérséklet: {sum(temps_min)/len(temps_min):.2f}°C")
    
    if temps_max:
        print(f"🌡️  Legalacsonyabb maximum hőmérséklet: {min(temps_max):.2f}°C")
        print(f"🌡️  Legmagasabb maximum hőmérséklet: {max(temps_max):.2f}°C")
        print(f"🌡️  Átlagos maximum hőmérséklet: {sum(temps_max)/len(temps_max):.2f}°C")
    
    if precipitations:
        total_precip = sum(precipitations)
        print(f"🌧️  Összes csapadék: {total_precip:.2f} mm")
        print(f"🌧️  Átlagos napi csapadék: {total_precip/len(precipitations):.2f} mm")
        print(f"🌧️  Legnagyobb napi csapadék: {max(precipitations):.2f} mm")

print("\n" + "="*60)
print("FELDOLGOZÁS BEFEJEZVE")
print("="*60)


### JELENLEGI ESŐZÉS ELLENŐRZÉSE - TESZT
print("\n\n")
format_rain_status()

# Egyszerű teszt függvény
print("\n\n🧪 EGYSZERŰ TESZT:")
print("-" * 30)
result = is_it_raining()
if result[0] is not None:
    is_raining, rain_info, desc, info = result
    if is_raining:
        print(f"✅ TESZT EREDMÉNY: Jelenleg ESIK az eső ({desc})")
    else:
        print(f"❌ TESZT EREDMÉNY: Jelenleg NEM esik az eső ({desc})")
    print(f"📊 Hőmérséklet: {info['temperature']}°C, Páratartalom: {info['humidity']}%")
else:
    print("⚠️ TESZT EREDMÉNY: Nem sikerült lekérdezni az aktuális időjárást")

# Egyszerű wrapper teszt
print("\n🔧 EGYSZERŰ WRAPPER TESZT:")
print("-" * 35)
simple_result = is_raining_simple()
if simple_result is None:
    print("⚠️ WRAPPER: Hiba történt")
elif simple_result:
    print("✅ WRAPPER: ESIK!")
else:
    print("❌ WRAPPER: NEM esik")


### 5 NAPOS ELŐREJELZÉS TESZTELÉSE
print("\n\n" + "="*60)
print("5 NAPOS CSAPADÉK ELŐREJELZÉS TESZT")
print("="*60)

# Teljes előrejelzés megjelenítése
format_5day_rain_forecast()

# Csak az esős napok
print("\n\n🌧️ CSAK AZ ESŐS NAPOK:")
print("-" * 25)
rainy_days = get_rainy_days_forecast()

if rainy_days:
    for day in rainy_days:
        print(f"📅 {day['date']}: {day['total_rain_mm']:.1f} mm eső várható")
        print(f"   🌤️  {day['descriptions']}")
else:
    print("☀️ Nincs esős nap az előrejelzésben!")

# Összefoglaló
print("\n\n📋 GYORS ÖSSZEFOGLALÓ:")
print("-" * 25)
summary = get_rain_summary()

if summary:
    print(f"🌧️ Esős napok: {summary['rainy_days_count']} nap")
    print(f"💧 Összes eső: {summary['total_rain_mm']:.1f} mm")
    print(f"☔ Legcsapadékosabb nap: {summary['heaviest_day']['date']} ({summary['heaviest_day']['rain_mm']:.1f} mm)")
    print(f"📅 Esős dátumok: {', '.join(summary['rainy_dates'])}")
else:
    print("☀️ Nincs esős nap várható!")


### INTELLIGENS ÖNTÖZÉSI TANÁCSADÓ TESZT
print("\n\n" + "="*60)
print("INTELLIGENS ÖNTÖZÉSI TANÁCSADÓ")
print("="*60)

# Import the irrigation advisor
try:
    import subprocess
    result = subprocess.run(['python3', 'irrigation_advisor.py'], 
                          capture_output=True, text=True, cwd='.')
    if result.returncode == 0:
        print(result.stdout)
    else:
        print("❌ Hiba az öntözési tanácsadó futtatásakor:")
        print(result.stderr)
except Exception as e:
    print(f"❌ Nem sikerült futtatni az öntözési tanácsadót: {e}")
    print("💡 Futtasd külön: python3 irrigation_advisor.py")