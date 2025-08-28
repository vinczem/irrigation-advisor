#!/bin/bash
# Home Assistant Addon Entry Point - Simplified Version

set -e

# Configuration
CONFIG_PATH=/data/options.json
STATE_PATH=/data/irrigation_state.json

echo "🏠 Starting Irrigation Advisor Addon..."

# Create required directories
mkdir -p /data
mkdir -p /share/irrigation

# Load addon configuration from Home Assistant
if [ -f "$CONFIG_PATH" ]; then
    API_KEY=$(jq -r '.api_key // empty' "$CONFIG_PATH")
    LATITUDE=$(jq -r '.latitude // 46.65' "$CONFIG_PATH") 
    LONGITUDE=$(jq -r '.longitude // 20.14' "$CONFIG_PATH")
    MQTT_BROKER=$(jq -r '.mqtt_broker // "core-mosquitto"' "$CONFIG_PATH")
    MQTT_PORT=$(jq -r '.mqtt_port // 1883' "$CONFIG_PATH")
    MQTT_USERNAME=$(jq -r '.mqtt_username // ""' "$CONFIG_PATH")
    MQTT_PASSWORD=$(jq -r '.mqtt_password // ""' "$CONFIG_PATH")
    LOG_LEVEL=$(jq -r '.log_level // "INFO"' "$CONFIG_PATH")
    
    echo "✅ Configuration loaded from Home Assistant"
    echo "   Location: $LATITUDE, $LONGITUDE"
    echo "   MQTT: $MQTT_BROKER:$MQTT_PORT"
    echo "   Log level: $LOG_LEVEL"
else
    echo "❌ No configuration found at $CONFIG_PATH"
    exit 1
fi

# Create options.json for Python scripts (combined format for compatibility)
cat > /usr/bin/data/options.json << EOF
{
    "api_key": "$API_KEY",
    "lat": $LATITUDE,
    "lon": $LONGITUDE,
    "latitude": $LATITUDE,
    "longitude": $LONGITUDE,
    "units": "metric",
    "mqtt_broker": "$MQTT_BROKER",
    "mqtt_port": $MQTT_PORT,
    "mqtt_username": "$MQTT_USERNAME",
    "mqtt_password": "$MQTT_PASSWORD"
}
EOF

echo "📝 Configuration files updated"

# Set log level for Python scripts
export LOG_LEVEL=$LOG_LEVEL
export PYTHONPATH="/usr/bin:$PYTHONPATH"

# Start health check service in background
echo "🏥 Starting health check service..."
python3 -c "
import http.server
import socketserver
import json
from datetime import datetime

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            health = {
                'status': 'healthy',
                'service': 'irrigation-advisor',
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(health).encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(('', 8099), HealthHandler) as httpd:
    httpd.serve_forever()
" &

HEALTH_PID=$!
echo "🏥 Health check service started (PID: $HEALTH_PID)"

# Start MQTT service for execution listening
echo "👂 Starting MQTT listener service..."
python3 /usr/bin/mqtt_service.py &
SERVICE_PID=$!
echo "📡 MQTT service started (PID: $SERVICE_PID)"

# Wait and monitor services
echo "✅ Irrigation Advisor Addon is running"
echo "   - MQTT Listener: Active (listening for irrigation executions)"  
echo "   - Health Check: http://addon:8099/health"
echo "   - State File: /data/irrigation_state.json"
echo ""
echo "💡 To trigger recommendations:"
echo "   - Use Home Assistant automation to call: python3 /usr/bin/mqtt_simple.py"
echo "   - Or use shell_command service in HA configuration"

# Function to handle shutdown
cleanup() {
    echo "🛑 Shutting down services..."
    kill $SERVICE_PID 2>/dev/null || true
    kill $HEALTH_PID 2>/dev/null || true
    exit 0
}

# Set trap for clean shutdown
trap cleanup SIGTERM SIGINT

# Keep the container running and monitor child processes
while true; do
    # Check if MQTT service is still running
    if ! kill -0 $SERVICE_PID 2>/dev/null; then
        echo "⚠️  MQTT service died, restarting..."
        python3 /usr/bin/mqtt_service.py &
        SERVICE_PID=$!
    fi
    
    # Check if health service is still running  
    if ! kill -0 $HEALTH_PID 2>/dev/null; then
        echo "⚠️  Health service died, restarting..."
        python3 -c "
import http.server
import socketserver
import json
from datetime import datetime

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            health = {
                'status': 'healthy',
                'service': 'irrigation-advisor',
                'timestamp': datetime.now().isoformat()
            }
            self.wfile.write(json.dumps(health).encode())

with socketserver.TCPServer(('', 8099), HealthHandler) as httpd:
    httpd.serve_forever()
" &
        HEALTH_PID=$!
    fi
    
    sleep 30
done
