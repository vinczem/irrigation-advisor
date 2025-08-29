#!/usr/bin/env python3
"""
MQTT-based Irrigation State Service
MQTT üzenetek alapján kezeli az öntözési állapotot
"""

import json
import sys
import os
import logging
from datetime import datetime, timedelta
import paho.mqtt.client as mqtt
import time

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from irrigation_state import SimpleIrrigationState

# Addon data directory
DATA_DIR = "/data" if os.path.exists("/data") else "."
STATE_FILE = os.path.join(DATA_DIR, "irrigation_state.json")
CONFIG_FILE = os.path.join(DATA_DIR, "options.json")

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def load_addon_config():
    """Load configuration from Home Assistant addon options"""
    try:
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
        
        # MQTT configuration from addon options
        mqtt_config = {
            'MQTT_BROKER': config.get('mqtt_broker', 'core-mosquitto'),
            'MQTT_PORT': config.get('mqtt_port', 1883),
            'MQTT_USERNAME': config.get('mqtt_username', None),
            'MQTT_PASSWORD': config.get('mqtt_password', None),
            'MQTT_CLIENT_ID': 'irrigation_advisor_service',
            'MQTT_TOPIC_BASE': 'irrigation/scheduler'
        }
        
        # Convert empty strings to None
        if mqtt_config['MQTT_USERNAME'] == '':
            mqtt_config['MQTT_USERNAME'] = None
        if mqtt_config['MQTT_PASSWORD'] == '':
            mqtt_config['MQTT_PASSWORD'] = None
            
        logger.info(f"MQTT config loaded: {mqtt_config['MQTT_BROKER']}:{mqtt_config['MQTT_PORT']}")
        return mqtt_config
        
    except FileNotFoundError:
        logger.error(f"Config file not found: {CONFIG_FILE}")
        # Fallback to default values
        return {
            'MQTT_BROKER': 'core-mosquitto',
            'MQTT_PORT': 1883,
            'MQTT_USERNAME': None,
            'MQTT_PASSWORD': None,
            'MQTT_CLIENT_ID': 'irrigation_advisor_service',
            'MQTT_TOPIC_BASE': 'irrigation/scheduler'
        }
    except Exception as e:
        logger.error(f"Error loading config: {e}")
        raise

class MQTTIrrigationService:
    def __init__(self):
        self.state_file = STATE_FILE
        self.mqtt_config = load_addon_config()
        self.client = None
        self.state = self.load_state()
        
    def load_state(self):
        """Load state with addon-specific path"""
        try:
            if os.path.exists(self.state_file):
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                logger.info(f"State loaded from {self.state_file}")
                return state
            else:
                logger.info(f"Creating new state file: {self.state_file}")
                return self.default_state()
        except Exception as e:
            logger.error(f"Error loading state: {e}")
            return self.default_state()
    
    def default_state(self):
        return {
            "last_recommendation": None,
            "last_execution": None,
            "irrigation_log": [],
            "version": "1.0"
        }
    
    def save_state(self):
        """Save state to addon data directory"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            logger.info(f"State saved to {self.state_file}")
        except Exception as e:
            logger.error(f"Error saving state: {e}")
    
    def mark_executed(self, amount, notes=""):
        """Log a new irrigation execution entry"""
        print("[DEBUG] mark_executed called with amount:", amount, "notes:", notes)
        entry = {
            "timestamp": datetime.now().isoformat(),
            "amount_lpm2": amount,
            "notes": notes,
            "type": "manual"
        }
        self.state["irrigation_log"].append(entry)
        # Keep only last 50 entries
        if len(self.state["irrigation_log"]) > 50:
            self.state["irrigation_log"] = self.state["irrigation_log"][-50:]
        self.save_state()
        print(f"[DEBUG] Manual irrigation logged: {amount}L/m² - {notes}")
        logger.info(f"Manual irrigation logged: {amount}L/m² - {notes}")
        self.publish_status_update()
    
    def publish_status_update(self):
        """Publish status update to MQTT (naplóalapú)"""
        try:
            summary = self.get_status_summary()
            status_topic = f"{self.mqtt_config['MQTT_TOPIC_BASE']}/addon_status"
            status_message = {
                "timestamp": datetime.now().isoformat(),
                "last_execution": summary["last_execution"],
                "recent_24h_amount": summary["recent_24h_amount"],
                "recent_24h_count": summary["recent_24h_count"]
            }
            self.client.publish(status_topic, json.dumps(status_message), qos=1, retain=True)
            logger.info(f"Status update published to {status_topic}")
        except Exception as e:
            logger.error(f"Error publishing status: {e}")
    
    def get_status_summary(self):
        """Get status summary (naplóalapú)"""
        # Legutóbbi locsolás (manual vagy advisor)
        last_execution = None
        for entry in reversed(self.state["irrigation_log"]):
            if entry.get("type") in ["manual", "advisor"]:
                last_execution = entry["timestamp"][:19]
                break
        # Utolsó 24 óra locsolásai
        cutoff = datetime.now() - timedelta(hours=24)
        recent = [e for e in self.state["irrigation_log"]
                  if datetime.fromisoformat(e["timestamp"]) > cutoff and e.get("type") in ["manual", "advisor"]]
        recent_24h_amount = sum(e["amount_lpm2"] or 0 for e in recent)
        recent_24h_count = len(recent)
        return {
            "last_execution": last_execution,
            "recent_24h_amount": recent_24h_amount,
            "recent_24h_count": recent_24h_count
        }
    
    def on_connect(self, client, userdata, flags, rc):
        """MQTT connection callback"""
        if rc == 0:
            logger.info(f"Connected to MQTT broker: {self.mqtt_config['MQTT_BROKER']}:{self.mqtt_config['MQTT_PORT']}")
            
            # Subscribe to execution commands from Home Assistant
            execution_topic = f"{self.mqtt_config['MQTT_TOPIC_BASE']}/execute"
            client.subscribe(execution_topic)
            logger.info(f"Subscribed to {execution_topic}")
            
        else:
            logger.error(f"MQTT connection failed: {rc}")
    
    def on_message(self, client, userdata, msg):
        """Handle MQTT messages"""
        try:
            topic = msg.topic
            payload = msg.payload.decode('utf-8')
            
            logger.info(f"Received: {topic} -> {payload}")
            
            if topic.endswith('/execute'):
                # Home Assistant reports irrigation execution
                try:
                    data = json.loads(payload)
                    amount = float(data.get('amount', 0))
                    notes = data.get('notes', 'Home Assistant automatic')
                    
                    self.mark_executed(amount, notes)
                    
                except (json.JSONDecodeError, ValueError):
                    # Simple numeric value
                    try:
                        amount = float(payload)
                        self.mark_executed(amount, 'Home Assistant automatic')
                    except ValueError:
                        logger.error(f"Invalid execution payload: {payload}")
                        
        except Exception as e:
            logger.error(f"Error processing MQTT message: {e}")
    
    def start_service(self):
        """Start MQTT service"""
        try:
            self.client = mqtt.Client(
                callback_api_version=mqtt.CallbackAPIVersion.VERSION1,
                client_id=self.mqtt_config['MQTT_CLIENT_ID']
            )
            
            self.client.on_connect = self.on_connect
            self.client.on_message = self.on_message
            
            if self.mqtt_config['MQTT_USERNAME'] and self.mqtt_config['MQTT_PASSWORD']:
                self.client.username_pw_set(self.mqtt_config['MQTT_USERNAME'], self.mqtt_config['MQTT_PASSWORD'])
            
            logger.info(f"Connecting to MQTT broker: {self.mqtt_config['MQTT_BROKER']}:{self.mqtt_config['MQTT_PORT']}")
            self.client.connect(self.mqtt_config['MQTT_BROKER'], self.mqtt_config['MQTT_PORT'], 60)
            
            logger.info("Starting MQTT irrigation service... (Ctrl+C to stop)")
            self.client.loop_forever()
            
        except KeyboardInterrupt:
            logger.info("Service stopped by user")
        except Exception as e:
            logger.error(f"Service error: {e}")
        finally:
            if self.client:
                self.client.disconnect()


def main():
    """Main function"""
    logger.info("🏠 MQTT IRRIGATION SERVICE FOR HOME ASSISTANT ADDON")
    logger.info("=" * 55)
    logger.info(f"Data directory: {DATA_DIR}")
    logger.info(f"State file: {STATE_FILE}")
    
    service = MQTTIrrigationService()
    service.start_service()


if __name__ == "__main__":
    main()
