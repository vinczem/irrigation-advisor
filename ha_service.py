#!/usr/bin/env python3
"""
Home Assistant Service Interface
REST API az addon és a Home Assistant közötti kommunikációhoz
"""

from flask import Flask, request, jsonify
import logging
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

from irrigation_state import SimpleIrrigationState
from irrigation_advisor import get_irrigation_recommendation
from mqtt_simple import convert_to_simple_format, publish_simple_message

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)

# Use shared data directory
DATA_DIR = "/data" if os.path.exists("/data") else "."
STATE_FILE = os.path.join(DATA_DIR, "irrigation_state.json")

class AddonIrrigationState(SimpleIrrigationState):
    def __init__(self):
        # Override state file location for addon
        self.state_file = STATE_FILE
        self.state = self.load_state()


@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "service": "irrigation-advisor"})


@app.route('/recommendation', methods=['GET'])
def get_recommendation():
    """Get irrigation recommendation"""
    try:
        # Get fresh recommendation
        recommendation = get_irrigation_recommendation()
        simple = convert_to_simple_format(recommendation)
        
        # Check against state
        state = AddonIrrigationState()
        should_skip, recent_amount = state.should_skip_recommendation(hours=6)
        
        if should_skip and simple['watering_required']:
            simple = {
                'watering_required': False,
                'water_amount_lpm2': 0,
                'reason': f'Frissen öntözve ({recent_amount}L/m²), átmenetileg kihagyva'
            }
        
        # Log recommendation if irrigation needed
        if simple['watering_required']:
            state.log_recommendation(simple['water_amount_lpm2'], simple['reason'])
        
        return jsonify({
            "success": True,
            "recommendation": simple,
            "recent_irrigation": recent_amount if should_skip else 0
        })
        
    except Exception as e:
        logging.error(f"Recommendation error: {e}")
        return jsonify({
            "success": False,
            "error": str(e),
            "recommendation": {
                'watering_required': False,
                'water_amount_lpm2': 0,
                'reason': 'API hiba történt'
            }
        }), 500


@app.route('/mark_executed', methods=['POST'])
def mark_executed():
    """Mark irrigation as executed (called by Home Assistant)"""
    try:
        data = request.get_json()
        amount = float(data.get('amount', 0))
        notes = data.get('notes', 'Home Assistant automatic')
        
        state = AddonIrrigationState()
        state.mark_executed(amount, notes)
        
        logging.info(f"Irrigation marked as executed: {amount}L/m² - {notes}")
        
        return jsonify({
            "success": True,
            "message": f"Irrigation marked as executed: {amount}L/m²"
        })
        
    except Exception as e:
        logging.error(f"Mark executed error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 400


@app.route('/status', methods=['GET'])
def get_status():
    """Get current irrigation status"""
    try:
        state = AddonIrrigationState()
        summary = state.get_status_summary()
        recent = state.get_recent_irrigation(48)
        
        return jsonify({
            "success": True,
            "status": summary,
            "recent_irrigation": [
                {
                    "timestamp": entry['execution_time'][:19] if entry['execution_time'] else entry['timestamp'][:19],
                    "amount": entry['execution_amount'] or entry['amount_lpm2'],
                    "executed": entry['executed'],
                    "reason": entry['reason']
                }
                for entry in recent[:10]  # Last 10 entries
            ]
        })
        
    except Exception as e:
        logging.error(f"Status error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@app.route('/publish_mqtt', methods=['POST'])
def publish_mqtt():
    """Manually trigger MQTT publish"""
    try:
        # Get recommendation
        recommendation = get_irrigation_recommendation()
        simple = convert_to_simple_format(recommendation)
        
        # Check state
        state = AddonIrrigationState()
        should_skip, recent_amount = state.should_skip_recommendation(hours=6)
        
        if should_skip and simple['watering_required']:
            simple = {
                'watering_required': False,
                'water_amount_lpm2': 0,
                'reason': f'Frissen öntözve ({recent_amount}L/m²), átmenetileg kihagyva'
            }
        
        # Publish to MQTT
        success = publish_simple_message(simple)
        
        # Log if irrigation recommended
        if simple['watering_required'] and success:
            state.log_recommendation(simple['water_amount_lpm2'], simple['reason'])
        
        return jsonify({
            "success": success,
            "message": simple,
            "mqtt_published": success
        })
        
    except Exception as e:
        logging.error(f"MQTT publish error: {e}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


if __name__ == '__main__':
    # Run Flask app
    port = int(os.environ.get('PORT', 8080))
    debug = os.environ.get('LOG_LEVEL', 'info').lower() == 'debug'
    
    logging.info(f"Starting Irrigation Advisor Service on port {port}")
    logging.info(f"Data directory: {DATA_DIR}")
    logging.info(f"State file: {STATE_FILE}")
    
    app.run(host='0.0.0.0', port=port, debug=debug)
