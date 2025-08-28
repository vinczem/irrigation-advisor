#!/usr/bin/env python3
"""
MQTT Dry-Run Publisher - Csak teszteléshez
Nem küld MQTT üzenetet, csak kiírja a konzolra
"""

import json
import sys
import os
from datetime import datetime

# Import the irrigation advisor
sys.path.append(os.path.dirname(__file__))
from irrigation_advisor import get_irrigation_recommendation
from mqtt_config import MQTT_TOPIC_BASE


def convert_to_simple_format(recommendation_data):
    """
    Convert detailed recommendation to your simple format:
    {'watering_required': False, 'water_amount_lpm2': 0, 'reason': 'recent_rain_and_upcoming_rain'}
    """
    
    if 'error' in recommendation_data:
        return {
            'watering_required': False,
            'water_amount_lpm2': 0,
            'reason': 'API hiba történt az adatok lekérdezésekor'
        }
    
    # Extract basic data
    rec = recommendation_data['recommendation']
    watering_required = rec in ['yes', 'light']
    water_amount = recommendation_data['irrigation_amount_liters_per_m2']
    
    # Use full Hungarian reason text
    reasons = recommendation_data.get('reasons', [])
    primary_reason = reasons[0] if reasons else 'Ismeretlen ok'
    
    return {
        'watering_required': watering_required,
        'water_amount_lpm2': water_amount,
        'reason': primary_reason
    }


def simulate_mqtt_publish(message):
    """Simulate MQTT publish - print to console for both raw JSON and individual topics"""
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    print(f"\n📡 MQTT SZIMULÁCIÓ - {timestamp}")
    print("=" * 50)
    
    # Simulate raw JSON topic
    raw_topic = f"{MQTT_TOPIC_BASE}/raw"
    raw_payload = json.dumps(message, ensure_ascii=False)
    print(f"📍 Topic: {raw_topic}")
    print(f"📦 Payload: {raw_payload}")
    
    # Simulate individual topics
    individual_topics = {
        f"{MQTT_TOPIC_BASE}/watering_required": str(message['watering_required']).lower(),
        f"{MQTT_TOPIC_BASE}/water_amount": str(message['water_amount_lpm2']),
        f"{MQTT_TOPIC_BASE}/reason": message['reason']
    }
    
    print(f"\n📡 EGYEDI TOPIC-OK:")
    print("-" * 25)
    for topic, payload in individual_topics.items():
        print(f"� {topic}: {payload}")
    
    print(f"\n🔄 QoS: 1, Retain: True")
    print("\n✅ Minden üzenet 'publikálva' (szimuláció)")
    
    return True


def main():
    """Main function - dry run MQTT publisher"""
    
    print("📡 MQTT DRY-RUN PUBLIKÁLÓ")
    print("=" * 35)
    print("ℹ️  Ez csak szimuláció - nem küld valós MQTT üzenetet")
    print()
    
    # Get recommendation
    print("🌱 Lekérdezem az öntözési javaslatot...")
    recommendation = get_irrigation_recommendation()
    
    # Convert to simple format
    simple_message = convert_to_simple_format(recommendation)
    
    # Show what we would publish (exactly your format)
    print(f"\nPublished message: {simple_message}")
    
    # Simulate MQTT publish
    if simulate_mqtt_publish(simple_message):
        print("\n🎯 Szimuláció befejezve!")
        print("\n📋 A valós MQTT használathoz:")
        print("   1. Indíts MQTT broker-t (pl. mosquitto)")
        print("   2. Állítsd be az mqtt_config.py fájlban a broker címét")
        print("   3. Futtasd a mqtt_simple.py fájlt")
    
    return simple_message


if __name__ == "__main__":
    main()
