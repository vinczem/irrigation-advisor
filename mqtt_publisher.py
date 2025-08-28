#!/usr/bin/env python3
"""
MQTT Publisher az öntözési tanácsadó rendszerhez
Egyszerű, könnyű üzenetek publikálása MQTT broker-re
"""

import json
import sys
import os
from datetime import datetime

# MQTT import (telepíteni kell: pip install paho-mqtt)
try:
    import paho.mqtt.client as mqtt
    MQTT_AVAILABLE = True
except ImportError:
    print("❌ paho-mqtt nincs telepítve. Telepítsd: pip install paho-mqtt")
    MQTT_AVAILABLE = False

# Import the irrigation advisor
sys.path.append(os.path.dirname(__file__))
from irrigation_advisor import get_irrigation_recommendation


# MQTT Configuration
MQTT_BROKER = "192.168.0.98"  # Módosítsd szükség szerint
MQTT_PORT = 2883
MQTT_TOPIC_BASE = "irrigation/scheduler"  # Base topic
MQTT_CLIENT_ID = "irrigation_advisor"

# MQTT credentials (opcionális)
MQTT_USERNAME = None  # Ha szükséges, add meg
MQTT_PASSWORD = None  # Ha szükséges, add meg


def create_mqtt_message(recommendation_data):
    """
    Convert irrigation recommendation to simple MQTT message format
    Hasonló a te mostani formátumhoz
    """
    if 'error' in recommendation_data:
        return {
            'watering_required': None,
            'water_amount_lpm2': 0,
            'reason': 'API hiba történt az adatok lekérdezésekor',
            'timestamp': datetime.now().isoformat(),
            'confidence': 0
        }
    
    # Map our recommendation to boolean
    rec = recommendation_data['recommendation']
    watering_required = rec in ['yes', 'light']
    
    # Get water amount
    water_amount = recommendation_data['irrigation_amount_liters_per_m2']
    
    # Use full Hungarian reason text instead of codes
    reasons = recommendation_data.get('reasons', ['Ismeretlen ok'])
    primary_reason = reasons[0] if reasons else 'Ismeretlen ok'
    
    return {
        'watering_required': watering_required,
        'water_amount_lpm2': water_amount,
        'reason': primary_reason,
        'timestamp': datetime.now().isoformat(),
        'confidence': recommendation_data.get('confidence_percent', 0),
        'soil_deficit_mm': recommendation_data.get('data_analysis', {}).get('soil_moisture_deficit_mm', 0),
        'current_temp': recommendation_data.get('data_analysis', {}).get('current_conditions', {}).get('temperature', 0),
        'upcoming_rain_mm': recommendation_data.get('data_analysis', {}).get('upcoming_rain_3days_mm', 0)
    }


def on_connect(client, userdata, flags, rc):
    """MQTT connection callback"""
    if rc == 0:
        print(f"✅ Kapcsolódva az MQTT broker-hez: {MQTT_BROKER}:{MQTT_PORT}")
    else:
        print(f"❌ MQTT kapcsolódási hiba. Return code: {rc}")


def on_publish(client, userdata, mid):
    """MQTT publish callback"""
    print(f"📤 Üzenet publikálva. Message ID: {mid}")


def publish_to_mqtt(message_data, topics=None):
    """
    Publish irrigation recommendation to MQTT
    """
    if not MQTT_AVAILABLE:
        print("❌ MQTT nem elérhető")
        return False
    
    if topics is None:
        topics = {
            f"{MQTT_TOPIC_BASE}/status": message_data,
            f"{MQTT_TOPIC_BASE}/watering_required": message_data['watering_required'],
            f"{MQTT_TOPIC_BASE}/water_amount": message_data['water_amount_lpm2'],
            f"{MQTT_TOPIC_BASE}/reason": message_data['reason']
        }
    
    try:
        # Create MQTT client
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, client_id=MQTT_CLIENT_ID)
        client.on_connect = on_connect
        client.on_publish = on_publish
        
        # Set credentials if provided
        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
        
        # Connect to broker
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        client.loop_start()
        
        # Publish messages
        success_count = 0
        for topic, payload in topics.items():
            if isinstance(payload, dict):
                payload_str = json.dumps(payload)
            else:
                payload_str = str(payload)
            
            result = client.publish(topic, payload_str, qos=1, retain=True)
            
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Publikálva: {topic}")
                success_count += 1
            else:
                print(f"❌ Hiba publikáláskor: {topic}, error: {result.rc}")
        
        # Wait for messages to be sent
        client.loop_stop()
        client.disconnect()
        
        return success_count > 0
        
    except Exception as e:
        print(f"❌ MQTT hiba: {e}")
        return False


def main():
    """Main function - get recommendation and publish to MQTT"""
    
    print("📡 MQTT PUBLIKÁLÓ - Öntözési Tanácsadó")
    print("=" * 45)
    
    # Get irrigation recommendation
    print("🌱 Öntözési tanács lekérdezése...")
    recommendation = get_irrigation_recommendation()
    
    # Create MQTT message
    mqtt_message = create_mqtt_message(recommendation)
    
    print("\n📋 MQTT ÜZENET:")
    print("-" * 20)
    print(json.dumps(mqtt_message, indent=2, ensure_ascii=False))
    
    # Publish to MQTT
    print(f"\n📡 Publikálás MQTT broker-re ({MQTT_BROKER}:{MQTT_PORT})...")
    
    if publish_to_mqtt(mqtt_message):
        print("✅ MQTT publikálás sikeres!")
    else:
        print("❌ MQTT publikálás sikertelen!")
    
    # Also show the simple format like yours
    print(f"\n🔄 Egyszerű formátum (mint a tiéd):")
    simple_message = {
        'watering_required': mqtt_message['watering_required'],
        'water_amount_lpm2': mqtt_message['water_amount_lpm2'],
        'reason': mqtt_message['reason']
    }
    print(f"Published message: {simple_message}")


if __name__ == "__main__":
    main()
