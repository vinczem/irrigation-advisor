#!/bin/bash
# Home Assistant Addon Entry Point - Service Mode Only

set -e

# Configuration
CONFIG_PATH=/data/options.json
STATE_PATH=/data/irrigation_state.json

echo "🏠 Starting Irrigation Advisor Addon..."
echo "   config_path = $CONFIG_PATH"
echo "   state_path = $STATE_PATH"

# Create required directories
mkdir -p /data
mkdir -p /share/irrigation


# Load configuration from options.json using jq
if [ -f "$CONFIG_PATH" ]; then
    API_KEY=$(jq -r '.api_key // empty' "$CONFIG_PATH")
    LATITUDE=$(jq -r '.latitude // 46.65' "$CONFIG_PATH")
    LONGITUDE=$(jq -r '.longitude // 20.14' "$CONFIG_PATH")
    MQTT_BROKER=$(jq -r '.mqtt_broker // "core-mosquitto"' "$CONFIG_PATH")
    MQTT_PORT=$(jq -r '.mqtt_port // 1883' "$CONFIG_PATH")
    MQTT_USERNAME=$(jq -r '.mqtt_username // ""' "$CONFIG_PATH")
    MQTT_PASSWORD=$(jq -r '.mqtt_password // ""' "$CONFIG_PATH")
    LOG_LEVEL=$(jq -r '.log_level // "INFO"' "$CONFIG_PATH")
    ENABLE_AUTO_CHECK=$(jq -r '.enable_auto_check // "true"' "$CONFIG_PATH")
    CHECK_INTERVAL_MINUTES=$(jq -r '.check_interval_minutes // 30' "$CONFIG_PATH")
    echo "✅ Configuration loaded from $CONFIG_PATH"
    echo "   Location: $LATITUDE, $LONGITUDE"
    echo "   MQTT: $MQTT_BROKER:$MQTT_PORT"
    echo "   Log level: $LOG_LEVEL"
else
    echo "❌ No configuration found at $CONFIG_PATH"
    exit 1
fi

# Create options.json for Python scripts
cat > /usr/bin/data/options.json << EOF
{
    "api_key": "$API_KEY",
    "lat": $LATITUDE,
    "lon": $LONGITUDE
}
EOF

# Update MQTT config for Python scripts
cat > /usr/bin/mqtt_config.py << EOF
# Auto-generated MQTT config for Home Assistant Addon

MQTT_BROKER = "$MQTT_BROKER"
MQTT_PORT = $MQTT_PORT
MQTT_CLIENT_ID = "irrigation_advisor_addon"
MQTT_USERNAME = "$MQTT_USERNAME"
MQTT_PASSWORD = "$MQTT_PASSWORD"
MQTT_TOPIC_BASE = "irrigation/scheduler"
MQTT_QOS = 1
MQTT_RETAIN = True
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



# Start background services
python3 /usr/bin/mqtt_service.py &
SERVICE_PID=$!
echo "� MQTT service started (PID: $SERVICE_PID)"



# Start health check service
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
                'timestamp': datetime.now().isoformat(),
                'auto_checks': ENABLE_AUTO_CHECK,
                'interval_minutes': CHECK_INTERVAL_MINUTES
            }
            self.wfile.write(json.dumps(health).encode())

with socketserver.TCPServer(('', 8099), HealthHandler) as httpd:
    httpd.serve_forever()
" &
HEALTH_PID=$!
echo "🏥 Health service started on port 8099 (PID: $HEALTH_PID)"

# Function to handle shutdown
cleanup() {
    echo "🛑 Shutting down services..."
    kill $SERVICE_PID 2>/dev/null || true
    kill $HEALTH_PID 2>/dev/null || true
    kill $SCHEDULER_PID 2>/dev/null || true
    echo "🛑 Services stopped."
    exit 0
}



# Function for automatic irrigation checks
irrigation_scheduler() {
    local CHECK_INTERVAL_MINUTES="$CHECK_INTERVAL_MINUTES"
    local ENABLE_AUTO_CHECK="$ENABLE_AUTO_CHECK"
    local next_check_time
    local current_time

    echo "🕒 Scheduler started: checks every $CHECK_INTERVAL_MINUTES minutes"
    echo "🤖 Auto checks enabled: $ENABLE_AUTO_CHECK"
    echo "[DEBUG] ENABLE_AUTO_CHECK értéke: $ENABLE_AUTO_CHECK"

    # Calculate and log next check time
    next_check_time=$(date -d "+${CHECK_INTERVAL_MINUTES} minutes" '+%Y-%m-%d %H:%M:%S')
    echo "⏰ Next irrigation check scheduled for: $next_check_time"

    while true; do
        if [[ "$ENABLE_AUTO_CHECK" == "true" ]]; then
            current_time=$(date '+%Y-%m-%d %H:%M:%S')
            echo "🌱 [${current_time}] Starting automatic irrigation check (interval: ${CHECK_INTERVAL_MINUTES}min)..."

            # Run irrigation check with enhanced logging
            if python3 /usr/bin/mqtt_simple.py > /tmp/irrigation_check.log 2>&1; then
                current_time=$(date '+%Y-%m-%d %H:%M:%S')
                echo "✅ [${current_time}] Automatic irrigation check completed successfully"

                # Log basic results if available
                if [ -f "/tmp/irrigation_check.log" ]; then
                    if grep -q "watering_required" /tmp/irrigation_check.log; then
                        local watering_status=$(grep "watering_required" /tmp/irrigation_check.log | tail -1)
                        echo "📊 Result: $watering_status"
                    fi
                fi
            else
                current_time=$(date '+%Y-%m-%d %H:%M:%S')
                echo "⚠️  [${current_time}] Automatic irrigation check failed!"
                echo "📋 Error log content:"
                if [ -f "/tmp/irrigation_check.log" ]; then
                    cat /tmp/irrigation_check.log | while IFS= read -r line; do
                        echo "   $line"
                    done
                fi
            fi
            
            # Calculate and log next check time
            next_check_time=$(date -d "+${CHECK_INTERVAL_MINUTES} minutes" '+%Y-%m-%d %H:%M:%S')
            echo "⏰ Next irrigation check scheduled for: $next_check_time"

        else
            current_time=$(date '+%Y-%m-%d %H:%M:%S')
            echo "⏸️ [${current_time}] Auto checks disabled, skipping... (next check would be in ${CHECK_INTERVAL_MINUTES}min)"
        fi
        
        # Wait for next check (convert minutes to seconds)
        sleep $((CHECK_INTERVAL_MINUTES * 60))
    done
}

# Set trap for clean shutdown
trap cleanup SIGTERM SIGINT

# Start automatic irrigation scheduler
irrigation_scheduler &
SCHEDULER_PID=$!
echo "⏰ Irrigation scheduler started (PID: $SCHEDULER_PID)"

# Wait and monitor services
echo "✅ Irrigation Advisor Addon is running"
echo "   - MQTT Listener: Active (listening for irrigation executions)"  
echo "   - Health Check: http://addon:8099/health"
echo "   - State File: /data/irrigation_state.json"
echo ""
echo "💡 To trigger recommendations:"
echo "   - Use Home Assistant automation to call: python3 /usr/bin/mqtt_simple.py"
echo "   - Or use shell_command service in HA configuration"

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

ENABLE_AUTO_CHECK = '$ENABLE_AUTO_CHECK'
CHECK_INTERVAL_MINUTES = $CHECK_INTERVAL_MINUTES

class HealthHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/health':
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            health = {
                'status': 'healthy',
                'service': 'irrigation-advisor',
                'timestamp': datetime.now().isoformat(),
                'auto_checks': ENABLE_AUTO_CHECK,
                'interval_minutes': CHECK_INTERVAL_MINUTES
            }
            self.wfile.write(json.dumps(health).encode())
        else:
            self.send_response(404)
            self.end_headers()

with socketserver.TCPServer(('', 8099), HealthHandler) as httpd:
    httpd.serve_forever()
" &
        HEALTH_PID=$!
    fi
    # Check if scheduler is still running
    if ! kill -0 $SCHEDULER_PID 2>/dev/null; then
        echo "⚠️  Irrigation scheduler died, restarting..."
        irrigation_scheduler &
        SCHEDULER_PID=$!
    fi
    sleep 30
done
