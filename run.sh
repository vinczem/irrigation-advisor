#!/bin/bash
# Home Assistant Addon Entry Point - Service Mode Only

set -e

# Configuration
CONFIG_PATH=/data/options.json
STATE_PATH=/data/irrigation_state.json

bashio::log.info "------------------------------------------"
bashio::log.info "-=( run.sh version: 2.1.20250828_1941 )=-"
bashio::log.info "🏠 Starting Irrigation Advisor Addon... 🏠"

# Create required directories
mkdir -p /data
mkdir -p /share/irrigation

# Load addon configuration from Home Assistant
if bashio::config.exists 'api_key'; then
    API_KEY=$(bashio::config 'api_key')
    LATITUDE=$(bashio::config 'latitude')
    LONGITUDE=$(bashio::config 'longitude')
    MQTT_BROKER=$(bashio::config 'mqtt_broker')
    MQTT_PORT=$(bashio::config 'mqtt_port')
    MQTT_USERNAME=$(bashio::config 'mqtt_username')
    MQTT_PASSWORD=$(bashio::config 'mqtt_password')
    LOG_LEVEL=$(bashio::config 'log_level')
    
    bashio::log.info "✅ Configuration loaded from Home Assistant"
    bashio::log.info "   Location: $LATITUDE, $LONGITUDE"
    bashio::log.info "   MQTT: $MQTT_BROKER:$MQTT_PORT"
    bashio::log.info "   Log level: $LOG_LEVEL"
else
    bashio::log.error "❌ No configuration found"
    exit 1
fi

# check if options.json exists
if [ ! -f /usr/bin/data/options.json ]; then
    bashio::log.error "❌ options.json not found"
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

MQTT_USERNAME = $(if [ -n "$MQTT_USERNAME" ]; then echo "\"$MQTT_USERNAME\""; else echo "None"; fi)
MQTT_PASSWORD = $(if [ -n "$MQTT_PASSWORD" ]; then echo "\"$MQTT_PASSWORD\""; else echo "None"; fi)

MQTT_TOPIC_BASE = "irrigation/scheduler"

MQTT_TOPICS = {
    "raw": f"{MQTT_TOPIC_BASE}/raw",
    "status": f"{MQTT_TOPIC_BASE}/status", 
    "watering_required": f"{MQTT_TOPIC_BASE}/watering_required",
    "water_amount": f"{MQTT_TOPIC_BASE}/water_amount",
    "reason": f"{MQTT_TOPIC_BASE}/reason",
    "temperature": f"{MQTT_TOPIC_BASE}/temperature",
    "deficit": f"{MQTT_TOPIC_BASE}/soil_deficit",
    "rain_forecast": f"{MQTT_TOPIC_BASE}/rain_forecast"
}

MQTT_QOS = 1
MQTT_RETAIN = True
EOF

bashio::log.info "📝 Configuration files updated"

# Set log level for Python scripts
export LOG_LEVEL=$LOG_LEVEL
export PYTHONPATH="/usr/bin:$PYTHONPATH"



# Start health check service in background
bashio::log.info "🏥 Starting health check service..."
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
bashio::log.info "🏥 Health check service started (PID: $HEALTH_PID)"



# Start background services
python3 /usr/bin/mqtt_service.py &
SERVICE_PID=$!
bashio::log.info "� MQTT service started (PID: $SERVICE_PID)"



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
                'auto_checks': '$(bashio::config 'enable_auto_check' 'true')',
                'interval_minutes': $(bashio::config 'check_interval_minutes' '30')
            }
            self.wfile.write(json.dumps(health).encode())

with socketserver.TCPServer(('', 8099), HealthHandler) as httpd:
    httpd.serve_forever()
" &
HEALTH_PID=$!
bashio::log.info "� Health service started on port 8099 (PID: $HEALTH_PID)"

# Function to handle shutdown
cleanup() {
    bashio::log.info "🛑 Shutting down services..."
    kill $SERVICE_PID 2>/dev/null || true
    kill $HEALTH_PID 2>/dev/null || true
    kill $SCHEDULER_PID 2>/dev/null || true
    bashio::log.info "🛑 Services stopped."
    exit 0
}



# Function for automatic irrigation checks
irrigation_scheduler() {
    local CHECK_INTERVAL_MINUTES=$(bashio::config 'check_interval_minutes' '30')
    local ENABLE_AUTO_CHECK=$(bashio::config 'enable_auto_check' 'true')
    local next_check_time
    local current_time
    
    bashio::log.info "🕒 Scheduler started: checks every $CHECK_INTERVAL_MINUTES minutes"
    bashio::log.info "🤖 Auto checks enabled: $ENABLE_AUTO_CHECK"
    bashio::log.info "[DEBUG] ENABLE_AUTO_CHECK értéke: $ENABLE_AUTO_CHECK"
    
    # Calculate and log next check time
    next_check_time=$(date -d "+${CHECK_INTERVAL_MINUTES} minutes" '+%Y-%m-%d %H:%M:%S')
    bashio::log.info "⏰ Next irrigation check scheduled for: $next_check_time"
    
    while true; do
        if [[ "$ENABLE_AUTO_CHECK" == "true" ]]; then
            current_time=$(date '+%Y-%m-%d %H:%M:%S')
            bashio::log.info "🌱 [${current_time}] Starting automatic irrigation check (interval: ${CHECK_INTERVAL_MINUTES}min)..."
            
            # Run irrigation check with enhanced logging
            if python3 /usr/bin/mqtt_simple.py > /tmp/irrigation_check.log 2>&1; then
                current_time=$(date '+%Y-%m-%d %H:%M:%S')
                bashio::log.info "✅ [${current_time}] Automatic irrigation check completed successfully"
                
                # Log basic results if available
                if [ -f "/tmp/irrigation_check.log" ]; then
                    if grep -q "watering_required" /tmp/irrigation_check.log; then
                        local watering_status=$(grep "watering_required" /tmp/irrigation_check.log | tail -1)
                        bashio::log.info "📊 Result: $watering_status"
                    fi
                fi
            else
                current_time=$(date '+%Y-%m-%d %H:%M:%S')
                bashio::log.warning "⚠️  [${current_time}] Automatic irrigation check failed!"
                bashio::log.warning "📋 Error log content:"
                if [ -f "/tmp/irrigation_check.log" ]; then
                    cat /tmp/irrigation_check.log | while IFS= read -r line; do
                        bashio::log.warning "   $line"
                    done
                fi
            fi
            
            # Calculate and log next check time
            next_check_time=$(date -d "+${CHECK_INTERVAL_MINUTES} minutes" '+%Y-%m-%d %H:%M:%S')
            bashio::log.info "⏰ Next irrigation check scheduled for: $next_check_time"
            
        else
            current_time=$(date '+%Y-%m-%d %H:%M:%S')
            bashio::log.debug "⏸️ [${current_time}] Auto checks disabled, skipping... (next check would be in ${CHECK_INTERVAL_MINUTES}min)"
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
bashio::log.info "⏰ Irrigation scheduler started (PID: $SCHEDULER_PID)"

# Wait and monitor services
bashio::log.info "✅ Irrigation Advisor Addon is running"
bashio::log.info "   - MQTT Listener: Active (listening for irrigation executions)"  
bashio::log.info "   - Health Check: http://addon:8099/health"
bashio::log.info "   - State File: /data/irrigation_state.json"
bashio::log.info ""
bashio::log.info "💡 To trigger recommendations:"
bashio::log.info "   - Use Home Assistant automation to call: python3 /usr/bin/mqtt_simple.py"
bashio::log.info "   - Or use shell_command service in HA configuration"

# Keep the container running and monitor child processes
while true; do
    # Check if MQTT service is still running
    if ! kill -0 $SERVICE_PID 2>/dev/null; then
        bashio::log.warning "⚠️  MQTT service died, restarting..."
        python3 /usr/bin/mqtt_service.py &
        SERVICE_PID=$!
    fi
    
    # Check if health service is still running  
    if ! kill -0 $HEALTH_PID 2>/dev/null; then
        bashio::log.warning "⚠️  Health service died, restarting..."
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
                'auto_checks': '$(bashio::config 'enable_auto_check' 'true')',
                'interval_minutes': $(bashio::config 'check_interval_minutes' '30')
            }
            self.wfile.write(json.dumps(health).encode())

with socketserver.TCPServer(('', 8099), HealthHandler) as httpd:
    httpd.serve_forever()
" &
        HEALTH_PID=$!
    fi
    
    # Check if scheduler is still running
    if ! kill -0 $SCHEDULER_PID 2>/dev/null; then
        bashio::log.warning "⚠️  Irrigation scheduler died, restarting..."
        irrigation_scheduler &
        SCHEDULER_PID=$!
    fi
    
    sleep 30
done
