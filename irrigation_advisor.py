#!/usr/bin/env python3
"""
Intelligens gyep öntözési tanácsadó rendszer
Figyelembe veszi a múltbéli, jelenlegi és jövőbeli időjárási adatokat
"""

import json
import requests
import time
import os
from datetime import datetime, timedelta

# Load configuration options from a JSON file
# Support both addon format (latitude/longitude) and legacy format (lat/lon)
config_file = "/data/options.json" if os.path.exists("/data/options.json") else "./options.json"
with open(config_file) as f:
    options = json.load(f)

api_key = options["api_key"]

# Support both formats for coordinates
if "latitude" in options and "longitude" in options:
    # New addon format
    lat = options["latitude"]
    lon = options["longitude"]
else:
    # Legacy format
    lat = options["lat"]
    lon = options["lon"]

units = options.get("units", "metric")  # Default to metric if not specified


# === ADATGYŰJTŐ FÜGGVÉNYEK ===

def get_historical_data(days_back=7):
    """Get historical weather data for the past N days"""
    historical_data = []
    
    for i in range(1, days_back + 1):
        date = (datetime.now() - timedelta(days=i)).strftime("%Y-%m-%d")
        url = f"https://api.openweathermap.org/data/3.0/onecall/day_summary?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu&date={date}"
        
        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()
            
            # Extract relevant data
            day_data = {
                'date': date,
                'temp_max': data.get('temperature', {}).get('max', 0),
                'temp_min': data.get('temperature', {}).get('min', 0),
                'temp_afternoon': data.get('temperature', {}).get('afternoon', 0),
                'humidity': data.get('humidity', {}).get('afternoon', 50),
                'precipitation': data.get('precipitation', {}).get('total', 0),
                'wind_speed': data.get('wind', {}).get('max', {}).get('speed', 0),
                'cloud_cover': data.get('cloud_cover', {}).get('afternoon', 0)
            }
            historical_data.append(day_data)
            
        except requests.RequestException as e:
            print(f"Hiba a múltbéli adatok lekérdezésekor ({date}): {e}")
        
        time.sleep(0.1)  # API rate limiting
    
    return historical_data


def get_current_weather():
    """Get current weather conditions"""
    url = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        return {
            'temperature': data.get('main', {}).get('temp', 0),
            'humidity': data.get('main', {}).get('humidity', 50),
            'wind_speed': data.get('wind', {}).get('speed', 0),
            'clouds': data.get('clouds', {}).get('all', 0),
            'is_raining': 'rain' in data and data['rain'].get('1h', 0) > 0,
            'rain_amount': data.get('rain', {}).get('1h', 0),
            'description': data.get('weather', [{}])[0].get('description', ''),
            'visibility': data.get('visibility', 10000) / 1000
        }
    except requests.RequestException as e:
        print(f"Hiba a jelenlegi időjárás lekérdezésekor: {e}")
        return None


def get_forecast_data():
    """Get 5-day forecast data"""
    url = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={api_key}&units={units}&lang=hu"
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        # Group by day
        daily_forecast = {}
        
        for item in data.get('list', []):
            dt_txt = item.get('dt_txt', '')
            if not dt_txt:
                continue
                
            date = dt_txt.split(' ')[0]
            
            if date not in daily_forecast:
                daily_forecast[date] = {
                    'date': date,
                    'temp_max': float('-inf'),
                    'temp_min': float('inf'),
                    'total_rain': 0,
                    'humidity_avg': 0,
                    'wind_max': 0,
                    'cloud_avg': 0,
                    'humidity_readings': 0
                }
            
            # Temperature
            temp = item.get('main', {}).get('temp', 0)
            daily_forecast[date]['temp_max'] = max(daily_forecast[date]['temp_max'], temp)
            daily_forecast[date]['temp_min'] = min(daily_forecast[date]['temp_min'], temp)
            
            # Rain
            rain_3h = item.get('rain', {}).get('3h', 0) + item.get('snow', {}).get('3h', 0)
            daily_forecast[date]['total_rain'] += rain_3h
            
            # Humidity
            humidity = item.get('main', {}).get('humidity', 50)
            daily_forecast[date]['humidity_avg'] += humidity
            daily_forecast[date]['humidity_readings'] += 1
            
            # Wind
            wind_speed = item.get('wind', {}).get('speed', 0)
            daily_forecast[date]['wind_max'] = max(daily_forecast[date]['wind_max'], wind_speed)
            
            # Clouds
            clouds = item.get('clouds', {}).get('all', 0)
            daily_forecast[date]['cloud_avg'] += clouds
        
        # Calculate averages and clean up
        forecast_list = []
        for date in sorted(daily_forecast.keys()):
            day = daily_forecast[date]
            if day['humidity_readings'] > 0:
                day['humidity_avg'] = day['humidity_avg'] / day['humidity_readings']
                day['cloud_avg'] = day['cloud_avg'] / day['humidity_readings']
            
            # Handle infinite values
            if day['temp_max'] == float('-inf'):
                day['temp_max'] = 25
            if day['temp_min'] == float('inf'):
                day['temp_min'] = 15
            
            del day['humidity_readings']  # Remove helper field
            forecast_list.append(day)
        
        return forecast_list
        
    except requests.RequestException as e:
        print(f"Hiba az előrejelzés lekérdezésekor: {e}")
        return []


# === ÖNTÖZÉSI LOGIKA ===

def calculate_evapotranspiration(temp_max, humidity, wind_speed, cloud_cover):
    """
    Simplified evapotranspiration calculation (Penman-Monteith inspired)
    Returns daily water loss in mm
    """
    # Base evapotranspiration for grass (rough estimate)
    base_et = 4.0  # mm/day for moderate conditions
    
    # Temperature factor (higher temp = more evaporation)
    temp_factor = 1.0 + (temp_max - 25) * 0.08  # +8% per degree above 25°C
    temp_factor = max(0.2, temp_factor)  # Minimum 20%
    
    # Humidity factor (lower humidity = more evaporation)
    humidity_factor = 1.5 - (humidity / 100.0)  # 50% humidity = 1.0 factor
    humidity_factor = max(0.3, min(2.0, humidity_factor))
    
    # Wind factor (more wind = more evaporation)
    wind_factor = 1.0 + (wind_speed * 0.1)  # +10% per m/s
    wind_factor = max(1.0, min(2.5, wind_factor))
    
    # Cloud factor (more clouds = less evaporation)
    cloud_factor = 1.0 - (cloud_cover / 100.0 * 0.3)  # Max 30% reduction
    cloud_factor = max(0.4, cloud_factor)
    
    et = base_et * temp_factor * humidity_factor * wind_factor * cloud_factor
    
    return max(0.5, et)  # Minimum 0.5mm/day


def analyze_soil_moisture_history(historical_data):
    """
    Analyze historical data to estimate current soil moisture deficit
    Returns estimated deficit in mm (can be negative if surplus)
    """
    net_balance = 0
    
    for day in historical_data:
        # Calculate daily water loss
        et = calculate_evapotranspiration(
            day['temp_max'], 
            day['humidity'], 
            day['wind_speed'], 
            day['cloud_cover']
        )
        
        # Water gained from precipitation
        water_gained = day['precipitation']
        
        # Net balance for this day (positive = surplus, negative = deficit)
        daily_balance = water_gained - et
        net_balance += daily_balance
    
    # Convert to deficit (positive = deficit, negative = surplus)
    deficit = -net_balance
    
    # Soil can't hold infinite water - assume max 30mm excess capacity
    # If we have more than 30mm surplus, the rest runs off
    if deficit < -30:
        deficit = -30
    
    # Soil moisture deficit can't be less than 0 (well-watered)
    # But we allow small negative values to indicate recent good watering
    return max(-30, deficit)


def get_irrigation_recommendation():
    """
    Main function: analyze all data and provide irrigation recommendation
    """
    print("🌱 Adatok gyűjtése az öntözési tanácshoz...")
    
    # Collect all data
    historical = get_historical_data(7)  # Last 7 days
    current = get_current_weather()
    forecast = get_forecast_data()
    
    if not historical or not current or not forecast:
        return {
            'error': 'Nem sikerült az összes szükséges adatot lekérdezni',
            'recommendation': 'no_data'
        }
    
    # Analyze current situation
    soil_deficit = analyze_soil_moisture_history(historical)
    
    # Check if it's currently raining
    currently_raining = current['is_raining']
    
    # Check upcoming rain in next 3 days
    upcoming_rain = sum(day['total_rain'] for day in forecast[:3])
    
    # Calculate expected water loss for next 3 days
    expected_loss = 0
    for day in forecast[:3]:
        et = calculate_evapotranspiration(
            day['temp_max'],
            day['humidity_avg'],
            day['wind_max'],
            day['cloud_avg']
        )
        expected_loss += et
    
    # Decision logic
    recommendation = 'no'
    irrigation_amount = 0
    confidence = 0
    reasons = []
    
    # Rule 0: Soil has surplus moisture (recent heavy rain)
    if soil_deficit < -5:  # Surplus > 5mm
        recommendation = 'no'
        reasons.append(f'Talaj jól öntözött, többlet: {abs(soil_deficit):.1f}mm')
        confidence = 95
    
    # Rule 1: Currently raining heavily
    elif currently_raining and current['rain_amount'] > 2:
        recommendation = 'no'
        reasons.append('Jelenleg erősen esik az eső')
        confidence = 95
    
    # Rule 2: Significant rain expected in next 24 hours
    elif forecast[0]['total_rain'] > 10:
        recommendation = 'wait'
        reasons.append(f"Holnap {forecast[0]['total_rain']:.1f}mm eső várható")
        confidence = 85
    
    # Rule 3: High soil deficit
    elif soil_deficit > 15:
        recommendation = 'yes'
        irrigation_amount = min(25, soil_deficit * 0.7)  # Irrigate 70% of deficit, max 25mm
        reasons.append(f'Nagy talajnedvesség hiány ({soil_deficit:.1f}mm)')
        confidence = 90
    
    # Rule 4: Moderate deficit + hot weather expected
    elif soil_deficit > 8 and forecast[0]['temp_max'] > 30:
        recommendation = 'yes'
        irrigation_amount = 15
        reasons.append('Mérsékelt hiány + forró idő várható')
        confidence = 75
    
    # Rule 5: Low deficit but very hot and dry conditions
    elif soil_deficit > 5 and forecast[0]['temp_max'] > 32 and current['humidity'] < 30:
        recommendation = 'yes'
        irrigation_amount = 10
        reasons.append('Nagyon forró és száraz körülmények')
        confidence = 70
    
    # Rule 6: Upcoming rain will cover needs
    elif upcoming_rain > expected_loss:
        recommendation = 'no'
        reasons.append(f'Várható eső ({upcoming_rain:.1f}mm) fedezi az igényt ({expected_loss:.1f}mm)')
        confidence = 80
    
    # Rule 7: Small deficit, but manageable
    elif soil_deficit > 0 and soil_deficit <= 5:
        if upcoming_rain < expected_loss * 0.3:  # Less rain expected than needed
            recommendation = 'light'
            irrigation_amount = 8
            reasons.append('Kis hiány, mérsékelt öntözés')
            confidence = 60
        else:
            recommendation = 'no'
            reasons.append('Kis hiány, de várható eső segít')
            confidence = 65
    
    # Rule 8: No deficit (well watered)
    else:
        recommendation = 'no'
        reasons.append('Megfelelő talajnedvesség')
        confidence = 75
    
    # Seasonal adjustment (August is typically dry in Hungary)
    if datetime.now().month in [7, 8, 9] and recommendation == 'no' and soil_deficit > 8:
        recommendation = 'light'
        irrigation_amount = max(irrigation_amount, 8)
        reasons.append('Nyár végi korrekcó: száraz évszak')
        confidence = max(60, confidence - 10)
    
    return {
        'timestamp': datetime.now().isoformat(),
        'recommendation': recommendation,
        'irrigation_amount_mm': round(irrigation_amount, 1),
        'irrigation_amount_liters_per_m2': round(irrigation_amount, 1),  # 1mm = 1 liter/m²
        'confidence_percent': confidence,
        'reasons': reasons,
        'data_analysis': {
            'soil_moisture_deficit_mm': round(soil_deficit, 1),
            'currently_raining': currently_raining,
            'current_rain_intensity': current['rain_amount'],
            'upcoming_rain_3days_mm': round(upcoming_rain, 1),
            'expected_water_loss_3days_mm': round(expected_loss, 1),
            'current_conditions': {
                'temperature': current['temperature'],
                'humidity': current['humidity'],
                'wind_speed': current['wind_speed'],
                'description': current['description']
            },
            'forecast_highlights': [
                {
                    'date': day['date'],
                    'temp_max': day['temp_max'],
                    'expected_rain': day['total_rain']
                } for day in forecast[:3]
            ]
        }
    }


def format_irrigation_advice():
    """Format the irrigation advice in human-readable form"""
    
    advice = get_irrigation_recommendation()
    
    if 'error' in advice:
        print(f"❌ {advice['error']}")
        return
    
    print("🌱" * 30)
    print("INTELLIGENS GYEP ÖNTÖZÉSI TANÁCSADÓ")
    print("🌱" * 30)
    
    print(f"📅 Időpont: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print()
    
    # Main recommendation
    rec = advice['recommendation']
    amount = advice['irrigation_amount_liters_per_m2']
    confidence = advice['confidence_percent']
    
    if rec == 'yes':
        print(f"💧 JAVASLAT: ÖNTÖZZ!")
        print(f"💦 Javasolt mennyiség: {amount} liter/m² ({amount} mm)")
        print(f"🎯 Biztonság: {confidence}%")
    elif rec == 'light':
        print(f"🌦️ JAVASLAT: KÖNNYŰ ÖNTÖZÉS")
        print(f"💦 Javasolt mennyiség: {amount} liter/m² ({amount} mm)")
        print(f"🎯 Biztonság: {confidence}%")
    elif rec == 'wait':
        print(f"⏳ JAVASLAT: VÁRJ!")
        print(f"🌧️ Hamarosan eső várható")
        print(f"🎯 Biztonság: {confidence}%")
    else:
        print(f"✅ JAVASLAT: NINCS SZÜKSÉG ÖNTÖZÉSRE")
        print(f"💚 A gyep megfelelően hidratált")
        print(f"🎯 Biztonság: {confidence}%")
    
    print()
    
    # Reasons
    print("📋 INDOKLÁS:")
    for i, reason in enumerate(advice['reasons'], 1):
        print(f"   {i}. {reason}")
    
    print()
    
    # Analysis details
    analysis = advice['data_analysis']
    print("📊 RÉSZLETES ELEMZÉS:")
    print(f"   🏜️  Talaj nedvességhiány: {analysis['soil_moisture_deficit_mm']} mm")
    print(f"   🌧️ Várható eső (3 nap): {analysis['upcoming_rain_3days_mm']} mm")
    print(f"   📈 Várható párolgás (3 nap): {analysis['expected_water_loss_3days_mm']} mm")
    
    print()
    print("🌤️ JELENLEGI KÖRÜLMÉNYEK:")
    current = analysis['current_conditions']
    print(f"   🌡️  Hőmérséklet: {current['temperature']}°C")
    print(f"   💧 Páratartalom: {current['humidity']}%")
    print(f"   🌬️  Szél: {current['wind_speed']} m/s")
    print(f"   ☁️  Időjárás: {current['description']}")
    
    if analysis['currently_raining']:
        print(f"   ☔ Jelenleg esik: {analysis['current_rain_intensity']} mm/h")
    
    print()
    print("📅 3 NAPOS ELŐREJELZÉS:")
    for day in analysis['forecast_highlights']:
        rain_text = f"{day['expected_rain']:.1f}mm" if day['expected_rain'] > 0 else "száraz"
        print(f"   {day['date']}: max {day['temp_max']:.1f}°C, eső: {rain_text}")
    
    print()
    print("🌱" * 30)


def main():
    """Main function"""
    format_irrigation_advice()


if __name__ == "__main__":
    main()
