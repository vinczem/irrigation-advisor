#!/usr/bin/env python3
"""
Egyszerű MQTT Publisher az öntözési rendszerhez
Enhanced logging with timestamps
"""

print("**************************")
print("Egyszerű MQTT Publisher az öntözési rendszerhez")
print("**************************")

import json
import sys
import os
from datetime import datetime
import paho.mqtt.client as mqtt

# Import the irrigation advisor and state tracker
sys.path.append(os.path.dirname(__file__))
from irrigation_advisor import get_irrigation_recommendation

# Import state tracker if available
try:
    from irrigation_state import SimpleIrrigationState
    STATE_TRACKING = True
except ImportError:
    print("ℹ️ State tracking not available")
    STATE_TRACKING = False

# Addon data directory
DATA_DIR = "/data" if os.path.exists("/data") else "."
CONFIG_FILE = os.path.join(DATA_DIR, "options.json")

def log_with_timestamp(message, level="INFO"):
    """Enhanced logging with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {level}: {message}", flush=True)

def load_addon_config():
    """Load configuration from Home Assistant addon options"""
    print("mqtt_simple > Loading addon config")

    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # MQTT configuration from addon options
        mqtt_config = {
            'MQTT_BROKER': config.get('mqtt_broker', 'core-mosquitto'),
            'MQTT_PORT': config.get('mqtt_port', 1883),
            'MQTT_USERNAME': config.get('mqtt_username', None),
            'MQTT_PASSWORD': config.get('mqtt_password', None),
            'MQTT_CLIENT_ID': 'irrigation_advisor_publisher',
            'MQTT_TOPIC_BASE': 'irrigation/scheduler'
        }
        
        # Convert empty strings to None
        if mqtt_config['MQTT_USERNAME'] == '':
            mqtt_config['MQTT_USERNAME'] = None
        if mqtt_config['MQTT_PASSWORD'] == '':
            mqtt_config['MQTT_PASSWORD'] = None
            
        log_with_timestamp(f"MQTT config loaded: {mqtt_config['MQTT_BROKER']}:{mqtt_config['MQTT_PORT']}")
        return mqtt_config
        
    except FileNotFoundError:
        log_with_timestamp(f"Config file not found: {CONFIG_FILE}, using defaults", "WARN")
        # Fallback to mqtt_config.py if exists
        try:
            import mqtt_config
            return {
                'MQTT_BROKER': mqtt_config.MQTT_BROKER,
                'MQTT_PORT': mqtt_config.MQTT_PORT,
                'MQTT_USERNAME': mqtt_config.MQTT_USERNAME,
                'MQTT_PASSWORD': mqtt_config.MQTT_PASSWORD,
                'MQTT_CLIENT_ID': mqtt_config.MQTT_CLIENT_ID,
                'MQTT_TOPIC_BASE': mqtt_config.MQTT_TOPIC_BASE
            }
        except ImportError:
            return {
                'MQTT_BROKER': 'core-mosquitto',
                'MQTT_PORT': 1883,
                'MQTT_USERNAME': None,
                'MQTT_PASSWORD': None,
                'MQTT_CLIENT_ID': 'irrigation_advisor_publisher',
                'MQTT_TOPIC_BASE': 'irrigation/scheduler'
            }
    except Exception as e:
        print(f"Error loading config: {e}")
        raise


def convert_to_simple_format(recommendation_data):
    """
    Convert detailed recommendation to your simple format:
    {'watering_required': False, 'water_amount_lpm2': 0, 'reason': 'recent_rain_and_upcoming_rain'}
    """

    print("mqtt_simple > Converting to simple format")

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


def check_recent_irrigation_state(message):
    """Check recent irrigation using state file"""

    print("mqtt_simple > Checking recent irrigation state")

    if not STATE_TRACKING:
        return message
    
    try:
        state = SimpleIrrigationState()
        should_skip, recent_amount = state.should_skip_recommendation(hours=6)
        
        if should_skip and message['watering_required']:
            log_with_timestamp(f"Skipping due to recent irrigation: {recent_amount}L/m²", "WARN")
            message = {
                'watering_required': False,
                'water_amount_lpm2': 0,
                'reason': f"Frissen öntözve ({recent_amount}L/m²), átmenetileg kihagyva"
            }
            
    except Exception as e:
        print(f"⚠️ State check error: {e}")
    
    return message


def publish_simple_message(message):
    """Publish simple message to MQTT - both raw JSON and individual values"""

    print("mqtt_simple > Publishing simple message")

    # Load MQTT configuration
    mqtt_config = load_addon_config()
    
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, client_id=mqtt_config['MQTT_CLIENT_ID'])
        
        # Set credentials if provided
        if mqtt_config['MQTT_USERNAME'] and mqtt_config['MQTT_PASSWORD']:
            client.username_pw_set(mqtt_config['MQTT_USERNAME'], mqtt_config['MQTT_PASSWORD'])
            
        client.connect(mqtt_config['MQTT_BROKER'], mqtt_config['MQTT_PORT'], 60)
        
        # Publish raw JSON to main topic
        raw_topic = f"{mqtt_config['MQTT_TOPIC_BASE']}/raw"
        raw_payload = json.dumps(message)
        
        result1 = client.publish(raw_topic, raw_payload, qos=1, retain=True)
        
        # Publish individual values to separate topics
        individual_topics = {
            f"{mqtt_config['MQTT_TOPIC_BASE']}/watering_required": str(message['watering_required']).lower(),
            f"{mqtt_config['MQTT_TOPIC_BASE']}/water_amount": str(message['water_amount_lpm2']),
            f"{mqtt_config['MQTT_TOPIC_BASE']}/reason": message['reason']
        }
        
        success_count = 0
        if result1.rc == mqtt.MQTT_ERR_SUCCESS:
            log_with_timestamp(f"Published to {raw_topic}")
            success_count += 1
        
        for topic, payload in individual_topics.items():
            result = client.publish(topic, payload, qos=1, retain=True)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                log_with_timestamp(f"Published to {topic}: {payload}")
                success_count += 1
            else:
                log_with_timestamp(f"Failed to publish to {topic}", "ERROR")
        
        client.disconnect()
        
        # Log recommendation if tracking enabled and irrigation required
        if STATE_TRACKING and message['watering_required']:
            try:
                state = SimpleIrrigationState()
                state.log_recommendation(message['water_amount_lpm2'], message['reason'])
            except Exception as e:
                print(f"⚠️ Logging error: {e}")
        
        if success_count > 0:
            print(f"📤 Original message: {message}")
            return True
        else:
            print("❌ All publishes failed")
            return False
            
    except Exception as e:
        print(f"❌ MQTT Error: {e}")
        return False


def main():
    """Main function with state tracking"""
    
    print("📡 MQTT PUBLISHER WITH STATE TRACKING")
    print("=" * 40)
    
    # Show tracking status
    if STATE_TRACKING:
        try:
            state = SimpleIrrigationState()
            summary = state.get_status_summary()
            print(f"✅ State tracking enabled")
            print(f"📊 Status: {summary['pending_recommendations']} pending, {summary['recent_24h']['count']} recent (24h)")
        except Exception as e:
            print(f"⚠️ State tracking error: {e}")
    else:
        print("⚠️ State tracking not available")
    
    log_with_timestamp("Starting irrigation recommendation check...")
    
    # Get recommendation
    log_with_timestamp("Getting irrigation recommendation...")
    recommendation = get_irrigation_recommendation()
    
    # Convert to simple format
    simple_message = convert_to_simple_format(recommendation)
    
    # Check against recent irrigation state
    simple_message = check_recent_irrigation_state(simple_message)
    
    # Show what we're publishing (exactly your format)
    log_with_timestamp(f"Publishing message: {simple_message}")
    
    # Publish to MQTT
    if publish_simple_message(simple_message):
        log_with_timestamp("MQTT publication successful!")
        
        if STATE_TRACKING:
            log_with_timestamp("Manual commands for marking execution:")
            log_with_timestamp("   python3 -c \"from irrigation_state import SimpleIrrigationState; s=SimpleIrrigationState(); s.mark_executed(10.5)\"")
    else:
        log_with_timestamp("MQTT publication failed!", "ERROR")
    
    return simple_message


if __name__ == "__main__":
    main()
