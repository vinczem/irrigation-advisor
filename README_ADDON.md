# 🏠 **Irrigation Advisor - Home Assistant Addon**

## 📁 **Addon Directory Structure**

For proper Home Assistant addon deployment, organize files as follows:

```
irrigation_advisor/
├── config.yaml                 # Addon configuration & options
├── Dockerfile                  # Container definition  
├── run.sh                     # Entry point script
├── README.md                  # Addon documentation
├── CHANGELOG.md               # Version history
├── icon.png                   # Addon icon (optional)
└── rootfs/                    # Container filesystem
    └── usr/
        └── bin/               # Python scripts location
            ├── irrigation_advisor.py
            ├── mqtt_simple.py
            ├── mqtt_service.py  
            ├── irrigation_state.py
            ├── irrigation_cli.py
            ├── mqtt_config.py
            └── data/
                └── options.json (auto-generated)
```

## 🚀 **Installation Steps**

### **Option 1: Local Addon Repository**

1. **Create addon directory in Home Assistant:**
   ```bash
   mkdir -p /usr/share/hassio/addons/local/irrigation_advisor
   ```

2. **Copy all files to addon directory:**
   ```bash
   cp config.yaml /usr/share/hassio/addons/local/irrigation_advisor/
   cp Dockerfile /usr/share/hassio/addons/local/irrigation_advisor/
   cp run.sh /usr/share/hassio/addons/local/irrigation_advisor/
   mkdir -p /usr/share/hassio/addons/local/irrigation_advisor/rootfs/usr/bin
   cp *.py /usr/share/hassio/addons/local/irrigation_advisor/rootfs/usr/bin/
   ```

3. **Set permissions:**
   ```bash
   chmod +x /usr/share/hassio/addons/local/irrigation_advisor/run.sh
   chmod +x /usr/share/hassio/addons/local/irrigation_advisor/rootfs/usr/bin/*.py
   ```

### **Option 2: Development Environment**

1. **Use VS Code with Home Assistant addon:**
   - Install "Home Assistant Community Add-on: SSH & Web Terminal"
   - Access via terminal and upload files directly

2. **Docker development:**
   ```bash
   # Build locally for testing
   docker build -t irrigation-advisor .
   
   # Test run
   docker run -p 8099:8099 \
     -e API_KEY="your_api_key" \
     -e LATITUDE="46.65" \
     -e LONGITUDE="20.14" \
     irrigation-advisor
   ```

## ⚙️ **Configuration**

After installation, configure in Home Assistant UI:

```yaml
# Required
api_key: "your_openweathermap_api_key"
latitude: 46.65
longitude: 20.14

# MQTT Settings
mqtt_broker: "core-mosquitto"
mqtt_port: 1883
mqtt_username: ""    # Optional
mqtt_password: ""    # Optional

# Optional
log_level: "INFO"
```

## 📡 **MQTT Topics**

The addon publishes to these topics:

| Topic | Description | Example Value |
|-------|-------------|---------------|
| `irrigation/scheduler/raw` | Full JSON decision | `{"watering_required": true, ...}` |
| `irrigation/scheduler/watering_required` | Boolean recommendation | `true` |
| `irrigation/scheduler/water_amount` | Liters per m² needed | `5.2` |
| `irrigation/scheduler/reason` | Decision explanation | `"soil_deficit_no_rain"` |
| `irrigation/scheduler/temperature` | Current temperature | `24.5` |
| `irrigation/scheduler/soil_deficit` | Soil moisture deficit | `8.3` |
| `irrigation/scheduler/rain_forecast` | 24h rain prediction | `2.1` |

## 🤖 **Home Assistant Integration**

### **1. Automation for Triggering Recommendations**

```yaml
automation:
  - alias: "Daily Irrigation Check"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: shell_command.irrigation_check
```

### **2. Shell Command Configuration**

```yaml
shell_command:
  irrigation_check: "docker exec addon_local_irrigation_advisor python3 /usr/bin/mqtt_simple.py"
```

### **3. MQTT Sensors**

```yaml
mqtt:
  sensor:
    - name: "Irrigation Required"
      state_topic: "irrigation/scheduler/watering_required"
      value_template: "{{ 'Yes' if value == 'true' else 'No' }}"
      
    - name: "Water Amount Needed"
      state_topic: "irrigation/scheduler/water_amount"
      unit_of_measurement: "L/m²"
      
    - name: "Irrigation Reason"
      state_topic: "irrigation/scheduler/reason"
      
    - name: "Soil Moisture Deficit"  
      state_topic: "irrigation/scheduler/soil_deficit"
      unit_of_measurement: "mm"
```

### **4. Irrigation Execution Tracking**

```yaml
automation:
  - alias: "Mark Irrigation Executed"
    trigger:
      - platform: state
        entity_id: switch.irrigation_system
        to: "off"
        for: "00:01:00"
    condition:
      - condition: state
        entity_id: switch.irrigation_system
        state: "off"
    action:
      - service: mqtt.publish
        data:
          topic: "irrigation/scheduler/execute"
          payload: >
            {
              "executed": true,
              "timestamp": "{{ now().isoformat() }}",
              "duration_minutes": 15
            }
```

## 🔧 **Troubleshooting**

### **Check Addon Logs**
```bash
docker logs addon_local_irrigation_advisor
```

### **Manual State Management**
```bash
# Check current state
docker exec addon_local_irrigation_advisor python3 /usr/bin/irrigation_cli.py status

# Mark irrigation as executed
docker exec addon_local_irrigation_advisor python3 /usr/bin/irrigation_cli.py mark

# Clear state history
docker exec addon_local_irrigation_advisor python3 /usr/bin/irrigation_cli.py clear
```

### **Test MQTT Connection**
```bash
# Subscribe to all irrigation topics
mosquitto_sub -h localhost -t "irrigation/scheduler/+"

# Trigger manual recommendation
docker exec addon_local_irrigation_advisor python3 /usr/bin/mqtt_simple.py
```

### **Health Check**
```bash
curl http://addon_ip:8099/health
```

## 📋 **Service Management**

The addon runs two main components:

1. **MQTT Service** (`mqtt_service.py`)
   - Runs continuously in background
   - Listens for irrigation execution confirmations
   - Updates state file when irrigation is performed

2. **Recommendation Publisher** (`mqtt_simple.py`)  
   - Triggered by Home Assistant automation
   - Analyzes weather data and makes recommendations
   - Publishes results to MQTT topics

## 🔄 **Update Process**

1. **Stop the addon** in Home Assistant UI
2. **Replace files** in addon directory
3. **Rebuild container** if Dockerfile changed
4. **Start the addon** and verify logs

---

**🌱 Happy Automated Irrigating! 💧**
