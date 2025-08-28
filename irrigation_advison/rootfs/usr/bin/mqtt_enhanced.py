#!/usr/bin/env python3
"""
Enhanced MQTT Simple Publisher with Irrigation Tracking
"""

import json
import sys
import os
from datetime import datetime
import paho.mqtt.client as mqtt
from mqtt_config import *

# Import the irrigation advisor and tracker
sys.path.append(os.path.dirname(__file__))
from irrigation_advisor import get_irrigation_recommendation

# Import tracker if available
try:
    from mqtt_feedback import IrrigationTracker
    TRACKING_AVAILABLE = True
except ImportError:
    print("ℹ️ Tracking not available - install mqtt_feedback.py")
    TRACKING_AVAILABLE = False


def convert_to_simple_format(recommendation_data):
    """
    Convert detailed recommendation to your simple format
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


def check_recent_irrigation(tracker, recommendation):
    """Check if recent irrigation should affect recommendation"""
    
    if not TRACKING_AVAILABLE:
        return recommendation
    
    should_skip, recent_amount = tracker.should_skip_recommendation(hours=6)
    
    if should_skip and recommendation['watering_required']:
        print(f"⚠️ Skipping irrigation - recent execution: {recent_amount}L/m²")
        
        # Modify recommendation
        recommendation['watering_required'] = False
        recommendation['water_amount_lpm2'] = 0
        recommendation['reason'] = f"Frissen öntözve ({recent_amount}L/m²), átmenetileg kihagyva"
        
    return recommendation


def publish_enhanced_message(message):
    """Publish message with tracking support"""
    
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, client_id=MQTT_CLIENT_ID)
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        # Publish raw JSON to main topic
        raw_topic = f"{MQTT_TOPIC_BASE}/raw"
        raw_payload = json.dumps(message)
        
        result1 = client.publish(raw_topic, raw_payload, qos=MQTT_QOS, retain=MQTT_RETAIN)
        
        # Publish individual values to separate topics
        individual_topics = {
            f"{MQTT_TOPIC_BASE}/watering_required": str(message['watering_required']).lower(),
            f"{MQTT_TOPIC_BASE}/water_amount": str(message['water_amount_lpm2']),
            f"{MQTT_TOPIC_BASE}/reason": message['reason']
        }
        
        # Add tracking info if available
        if TRACKING_AVAILABLE:
            tracker = IrrigationTracker()
            recent_events = tracker.get_recent_irrigation(hours=24)
            
            tracking_info = {
                'last_24h_events': len(recent_events),
                'pending_recommendations': len([e for e in recent_events if not e[4]]),  # not executed
                'last_execution': recent_events[0][5] if recent_events and recent_events[0][4] else None
            }
            
            individual_topics[f"{MQTT_TOPIC_BASE}/tracking"] = json.dumps(tracking_info)
        
        success_count = 0
        if result1.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"✅ Published to {raw_topic}")
            success_count += 1
        
        for topic, payload in individual_topics.items():
            result = client.publish(topic, payload, qos=MQTT_QOS, retain=MQTT_RETAIN)
            if result.rc == mqtt.MQTT_ERR_SUCCESS:
                print(f"✅ Published to {topic}: {payload}")
                success_count += 1
            else:
                print(f"❌ Failed to publish to {topic}")
        
        client.disconnect()
        
        # Log recommendation to tracking system
        if TRACKING_AVAILABLE and message['watering_required']:
            tracker = IrrigationTracker()
            tracker.log_recommendation(message['water_amount_lpm2'], message['reason'])
        
        if success_count > 0:
            print(f"📤 Enhanced message: {message}")
            return True
        else:
            print("❌ All publishes failed")
            return False
            
    except Exception as e:
        print(f"❌ MQTT Error: {e}")
        return False


def main():
    """Main function with tracking support"""
    
    print("📡 ENHANCED MQTT PUBLISHER WITH TRACKING")
    print("=" * 45)
    
    # Initialize tracker if available
    if TRACKING_AVAILABLE:
        tracker = IrrigationTracker()
        print("✅ Irrigation tracking enabled")
        
        # Show recent activity
        recent = tracker.get_recent_irrigation(hours=24)
        if recent:
            print(f"📊 Recent activity (24h): {len(recent)} events")
            for event in recent[:3]:  # Show last 3
                status = "✅ Executed" if event[4] else "⏳ Pending"
                print(f"   {event[0][:19]} - {event[1]}L/m² - {status}")
        else:
            print("📊 No recent irrigation events")
    else:
        print("⚠️ Tracking not available")
        tracker = None
    
    print()
    
    # Get recommendation
    print("🌱 Lekérdezem az öntözési javaslatot...")
    recommendation = get_irrigation_recommendation()
    
    # Convert to simple format
    simple_message = convert_to_simple_format(recommendation)
    
    # Check against recent irrigation
    if tracker:
        simple_message = check_recent_irrigation(tracker, simple_message)
    
    # Show what we're publishing
    print(f"\nRecommendation: {simple_message}")
    
    # Publish to MQTT
    if publish_enhanced_message(simple_message):
        print("✅ Enhanced MQTT publikálás sikeres!")
    else:
        print("❌ MQTT publikálás sikertelen!")
    
    return simple_message


if __name__ == "__main__":
    main()
