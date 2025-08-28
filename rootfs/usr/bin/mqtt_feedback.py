#!/usr/bin/env python3
"""
MQTT Feedback Handler - Öntözési visszajelzések kezelése
"""

import json
import sqlite3
import os
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
from mqtt_config import *

# Database file for tracking irrigation events
DB_FILE = "irrigation_log.db"

class IrrigationTracker:
    def __init__(self):
        self.setup_database()
        
    def setup_database(self):
        """Initialize SQLite database for tracking"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS irrigation_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                recommended_amount REAL,
                actual_amount REAL,
                reason TEXT,
                executed BOOLEAN DEFAULT 0,
                execution_timestamp TEXT
            )
        ''')
        
        conn.commit()
        conn.close()
        print(f"✅ Database initialized: {DB_FILE}")
        
    def log_recommendation(self, amount, reason):
        """Log irrigation recommendation"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        timestamp = datetime.now().isoformat()
        cursor.execute('''
            INSERT INTO irrigation_events 
            (timestamp, recommended_amount, reason, executed)
            VALUES (?, ?, ?, 0)
        ''', (timestamp, amount, reason))
        
        recommendation_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        print(f"📝 Recommendation logged: ID={recommendation_id}, Amount={amount}L/m²")
        return recommendation_id
        
    def log_execution(self, actual_amount, notes=""):
        """Log actual irrigation execution from Home Assistant"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # Find the most recent unexecuted recommendation
        cursor.execute('''
            SELECT id FROM irrigation_events 
            WHERE executed = 0 
            ORDER BY timestamp DESC 
            LIMIT 1
        ''')
        
        result = cursor.fetchone()
        if result:
            recommendation_id = result[0]
            execution_time = datetime.now().isoformat()
            
            cursor.execute('''
                UPDATE irrigation_events 
                SET executed = 1, actual_amount = ?, execution_timestamp = ?
                WHERE id = ?
            ''', (actual_amount, execution_time, recommendation_id))
            
            conn.commit()
            print(f"✅ Execution logged: ID={recommendation_id}, Actual={actual_amount}L/m²")
        else:
            print("⚠️ No pending recommendation found to mark as executed")
            
        conn.close()
        
    def get_recent_irrigation(self, hours=24):
        """Get recent irrigation events"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT timestamp, recommended_amount, actual_amount, reason, executed, execution_timestamp
            FROM irrigation_events 
            WHERE timestamp >= ? 
            ORDER BY timestamp DESC
        ''', (since,))
        
        events = cursor.fetchall()
        conn.close()
        
        return events
        
    def should_skip_recommendation(self, hours=6):
        """Check if we should skip recommendation due to recent irrigation"""
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        since = (datetime.now() - timedelta(hours=hours)).isoformat()
        
        cursor.execute('''
            SELECT SUM(actual_amount) FROM irrigation_events 
            WHERE executed = 1 AND execution_timestamp >= ?
        ''', (since,))
        
        result = cursor.fetchone()
        recent_irrigation = result[0] if result[0] else 0
        
        conn.close()
        
        if recent_irrigation > 0:
            print(f"ℹ️ Recent irrigation detected: {recent_irrigation}L/m² in last {hours} hours")
            return True, recent_irrigation
        else:
            return False, 0


# MQTT Callback functions
def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("✅ Connected to MQTT broker for feedback")
        # Subscribe to Home Assistant irrigation feedback
        client.subscribe(f"{MQTT_TOPIC_BASE}/executed")
        client.subscribe(f"{MQTT_TOPIC_BASE}/irrigation_status")
    else:
        print(f"❌ MQTT connection failed: {rc}")

def on_message(client, userdata, msg):
    """Handle irrigation feedback messages"""
    try:
        topic = msg.topic
        payload = msg.payload.decode('utf-8')
        
        print(f"📨 Received: {topic} -> {payload}")
        
        if topic.endswith('/executed'):
            # Home Assistant reports irrigation was executed
            try:
                data = json.loads(payload)
                actual_amount = data.get('actual_amount', 0)
                userdata['tracker'].log_execution(actual_amount)
            except json.JSONDecodeError:
                # Simple numeric value
                actual_amount = float(payload)
                userdata['tracker'].log_execution(actual_amount)
                
    except Exception as e:
        print(f"❌ Error processing feedback: {e}")


def start_feedback_listener():
    """Start MQTT listener for irrigation feedback"""
    
    tracker = IrrigationTracker()
    
    try:
        client = mqtt.Client(callback_api_version=mqtt.CallbackAPIVersion.VERSION1, 
                           client_id=MQTT_CLIENT_ID + "_feedback")
        client.user_data_set({'tracker': tracker})
        client.on_connect = on_connect
        client.on_message = on_message
        
        if MQTT_USERNAME and MQTT_PASSWORD:
            client.username_pw_set(MQTT_USERNAME, MQTT_PASSWORD)
            
        print(f"🔄 Connecting to MQTT broker for feedback...")
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
        
        print("👂 Listening for irrigation feedback... (Ctrl+C to stop)")
        client.loop_forever()
        
    except KeyboardInterrupt:
        print("\n🛑 Feedback listener stopped")
    except Exception as e:
        print(f"❌ Feedback listener error: {e}")


if __name__ == "__main__":
    start_feedback_listener()
