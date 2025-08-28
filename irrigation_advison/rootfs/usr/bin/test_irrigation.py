#!/usr/bin/env python3
"""
Öntözési tanácsadó teszt különböző szcenáriókkal
"""

import json
from datetime import datetime
from irrigation_advisor import calculate_evapotranspiration, analyze_soil_moisture_history


def test_evapotranspiration():
    """Test the evapotranspiration calculation"""
    print("🧪 EVAPOTRANSPIRÁCIÓ TESZT")
    print("=" * 30)
    
    test_cases = [
        # temp_max, humidity, wind_speed, cloud_cover, expected_description
        (25, 50, 2, 50, "Normál körülmények"),
        (35, 30, 5, 10, "Forró, száraz, szeles"),
        (15, 80, 1, 90, "Hűvös, párás, felhős"),
        (30, 20, 3, 0, "Meleg, száraz, tiszta ég"),
        (20, 90, 0, 100, "Hűvös, nagyon párás, borús")
    ]
    
    for temp, humidity, wind, clouds, desc in test_cases:
        et = calculate_evapotranspiration(temp, humidity, wind, clouds)
        print(f"{desc}:")
        print(f"   Hőmérséklet: {temp}°C, Páratartalom: {humidity}%, Szél: {wind}m/s, Felhő: {clouds}%")
        print(f"   💧 Párolgás: {et:.1f} mm/nap")
        print()


def test_soil_moisture_scenarios():
    """Test different soil moisture scenarios"""
    print("🌱 TALAJNEDVESSÉG SZCENÁRIÓK")
    print("=" * 35)
    
    # Scenario 1: Very dry week
    dry_week = [
        {'temp_max': 32, 'humidity': 25, 'precipitation': 0, 'wind_speed': 4, 'cloud_cover': 10},
        {'temp_max': 35, 'humidity': 20, 'precipitation': 0, 'wind_speed': 5, 'cloud_cover': 5},
        {'temp_max': 33, 'humidity': 30, 'precipitation': 0, 'wind_speed': 3, 'cloud_cover': 15},
        {'temp_max': 31, 'humidity': 35, 'precipitation': 0, 'wind_speed': 2, 'cloud_cover': 20},
        {'temp_max': 34, 'humidity': 25, 'precipitation': 0, 'wind_speed': 4, 'cloud_cover': 0},
        {'temp_max': 36, 'humidity': 20, 'precipitation': 0, 'wind_speed': 5, 'cloud_cover': 5},
        {'temp_max': 33, 'humidity': 30, 'precipitation': 0, 'wind_speed': 3, 'cloud_cover': 10}
    ]
    
    deficit1 = analyze_soil_moisture_history(dry_week)
    print(f"1. Száraz hét (7 nap forróság, 0mm eső):")
    print(f"   💧 Hiány: {deficit1:.1f} mm")
    print(f"   🚨 Öntözési igény: {'MAGAS' if deficit1 > 15 else 'KÖZEPES' if deficit1 > 8 else 'ALACSONY'}")
    print()
    
    # Scenario 2: Mixed week with some rain
    mixed_week = [
        {'temp_max': 28, 'humidity': 45, 'precipitation': 0, 'wind_speed': 2, 'cloud_cover': 30},
        {'temp_max': 25, 'humidity': 70, 'precipitation': 15, 'wind_speed': 1, 'cloud_cover': 80},
        {'temp_max': 22, 'humidity': 80, 'precipitation': 8, 'wind_speed': 1, 'cloud_cover': 90},
        {'temp_max': 26, 'humidity': 60, 'precipitation': 0, 'wind_speed': 2, 'cloud_cover': 40},
        {'temp_max': 29, 'humidity': 50, 'precipitation': 0, 'wind_speed': 3, 'cloud_cover': 20},
        {'temp_max': 31, 'humidity': 40, 'precipitation': 0, 'wind_speed': 3, 'cloud_cover': 10},
        {'temp_max': 30, 'humidity': 45, 'precipitation': 0, 'wind_speed': 2, 'cloud_cover': 25}
    ]
    
    deficit2 = analyze_soil_moisture_history(mixed_week)
    print(f"2. Vegyes hét (23mm eső + melegebb napok):")
    print(f"   💧 Hiány: {deficit2:.1f} mm")
    print(f"   🚨 Öntözési igény: {'MAGAS' if deficit2 > 15 else 'KÖZEPES' if deficit2 > 8 else 'ALACSONY'}")
    print()
    
    # Scenario 3: Rainy week
    rainy_week = [
        {'temp_max': 20, 'humidity': 85, 'precipitation': 12, 'wind_speed': 1, 'cloud_cover': 95},
        {'temp_max': 18, 'humidity': 90, 'precipitation': 8, 'wind_speed': 0, 'cloud_cover': 100},
        {'temp_max': 22, 'humidity': 75, 'precipitation': 20, 'wind_speed': 2, 'cloud_cover': 85},
        {'temp_max': 24, 'humidity': 70, 'precipitation': 5, 'wind_speed': 1, 'cloud_cover': 70},
        {'temp_max': 21, 'humidity': 80, 'precipitation': 15, 'wind_speed': 1, 'cloud_cover': 90},
        {'temp_max': 19, 'humidity': 85, 'precipitation': 10, 'wind_speed': 1, 'cloud_cover': 95},
        {'temp_max': 23, 'humidity': 75, 'precipitation': 3, 'wind_speed': 2, 'cloud_cover': 60}
    ]
    
    deficit3 = analyze_soil_moisture_history(rainy_week)
    print(f"3. Esős hét (73mm eső, hűvösebb idő):")
    print(f"   💧 Hiány: {deficit3:.1f} mm")
    print(f"   🚨 Öntözési igény: {'MAGAS' if deficit3 > 15 else 'KÖZEPES' if deficit3 > 8 else 'ALACSONY'}")
    print()


def simulate_irrigation_decisions():
    """Simulate different irrigation decision scenarios"""
    print("🤖 DÖNTÉSHOZATAL SZIMULÁCIÓ")
    print("=" * 30)
    
    scenarios = [
        {
            'name': 'Forró száraz nyár',
            'soil_deficit': 25,
            'currently_raining': False,
            'current_rain': 0,
            'upcoming_rain': 0,
            'expected_loss': 15,
            'temp_max': 35,
            'humidity': 20
        },
        {
            'name': 'Közelgő eső',
            'soil_deficit': 12,
            'currently_raining': False,
            'current_rain': 0,
            'upcoming_rain': 18,
            'expected_loss': 10,
            'temp_max': 28,
            'humidity': 60
        },
        {
            'name': 'Jelenleg esik',
            'soil_deficit': 8,
            'currently_raining': True,
            'current_rain': 5,
            'upcoming_rain': 12,
            'expected_loss': 8,
            'temp_max': 22,
            'humidity': 85
        },
        {
            'name': 'Ideális körülmények',
            'soil_deficit': 3,
            'currently_raining': False,
            'current_rain': 0,
            'upcoming_rain': 8,
            'expected_loss': 6,
            'temp_max': 25,
            'humidity': 55
        }
    ]
    
    for scenario in scenarios:
        print(f"📊 {scenario['name']}:")
        
        # Simple decision logic (simplified version of the main algorithm)
        if scenario['currently_raining'] and scenario['current_rain'] > 2:
            decision = 'NEM'
            amount = 0
            reason = 'Jelenleg esik'
        elif scenario['upcoming_rain'] > 10:
            decision = 'VÁRJ'
            amount = 0
            reason = 'Hamarosan eső várható'
        elif scenario['soil_deficit'] > 15:
            decision = 'IGEN'
            amount = min(25, scenario['soil_deficit'] * 0.7)
            reason = 'Nagy talajhiány'
        elif scenario['soil_deficit'] > 8 and scenario['temp_max'] > 30:
            decision = 'IGEN'
            amount = 15
            reason = 'Mérsékelt hiány + forró idő'
        elif scenario['upcoming_rain'] > scenario['expected_loss']:
            decision = 'NEM'
            amount = 0
            reason = 'Eső fedezi az igényt'
        elif scenario['soil_deficit'] > 3:
            decision = 'KICSIT'
            amount = 8
            reason = 'Mérsékelt viszonyok'
        else:
            decision = 'NEM'
            amount = 0
            reason = 'Megfelelő nedvesség'
        
        print(f"   🎯 Döntés: {decision}")
        if amount > 0:
            print(f"   💦 Mennyiség: {amount:.1f} liter/m²")
        print(f"   📝 Indok: {reason}")
        print(f"   📈 Talajhiány: {scenario['soil_deficit']}mm, Várható eső: {scenario['upcoming_rain']}mm")
        print()


def main():
    """Run all tests"""
    print("🧪" * 20)
    print("ÖNTÖZÉSI RENDSZER TESZTEK")
    print("🧪" * 20)
    print()
    
    test_evapotranspiration()
    print("\n" + "="*50 + "\n")
    
    test_soil_moisture_scenarios()
    print("\n" + "="*50 + "\n")
    
    simulate_irrigation_decisions()
    
    print("🧪" * 20)
    print("TESZTEK BEFEJEZVE")
    print("🧪" * 20)


if __name__ == "__main__":
    main()
