# 🏠 Home Assistant Addon Integration Solutions

## Probléma

Docker konténerben futó Home Assistant addon és a Home Assistant core közötti kommunikáció az irrigation state management-hez.

## 🎯 Ajánlott Megoldás: MQTT-alapú Kommunikáció

### Miért MQTT?

1. **✅ Natív HA támogatás** - MQTT broker már fut
2. **✅ Egyszerű integráció** - Nincs REST API vagy port mapping szükséges  
3. **✅ Reliable messaging** - QoS és retain flags
4. **✅ Event-driven** - Real-time reakciók

### Architektúra

```
Home Assistant Addon Container:
├── mqtt_simple.py          # Recommendation publisher
├── mqtt_service.py         # State management service  
├── irrigation_state.py     # State persistence
└── data/
    └── irrigation_state.json  # Persistent state

Home Assistant Core:
├── MQTT Sensors            # Read recommendations
├── Automation              # Execute irrigation  
└── MQTT Publish            # Report execution
```

## 📡 MQTT Topic Flow

### 1. Addon → Home Assistant (Recommendation)

```bash
# Addon publishes recommendation
irrigation/scheduler/raw → {"watering_required": true, "water_amount_lpm2": 8, ...}
irrigation/scheduler/watering_required → "true"
irrigation/scheduler/water_amount → "8"  
irrigation/scheduler/reason → "Megfelelő talajnedvesség"
```

### 2. Home Assistant → Addon (Execution Report)

```bash  
# Home Assistant reports execution
irrigation/scheduler/execute → {"amount": 8.0, "notes": "HA automatic", "timestamp": "2025-08-25T16:00:00"}
```

### 3. Addon → Home Assistant (Status Update)

```bash
# Addon confirms and updates status
irrigation/scheduler/addon_status → {"pending_count": 0, "recent_24h_amount": 8.0, ...}
```

## 🔧 Implementation Steps

### Step 1: Home Assistant Configuration

```yaml
# configuration.yaml
mqtt:
  sensor:
    - name: "Garden Needs Watering"
      state_topic: "irrigation/scheduler/watering_required" 
      icon: mdi:sprinkler

automation:
  - alias: "Execute Irrigation"
    trigger:
      platform: state  
      entity_id: binary_sensor.garden_needs_watering
      to: "on"
    action:
      # Execute irrigation logic
      - service: switch.turn_on
        entity_id: switch.irrigation_valve
      # Report execution via MQTT
      - service: mqtt.publish
        data:
          topic: "irrigation/scheduler/execute"
          payload: '{"amount": {{ states("sensor.water_amount") }}, "notes": "HA automatic"}'
```

### Step 2: Addon Services

**mqtt_service.py** (Background service):
```python
# Listens for irrigation/scheduler/execute messages
# Updates irrigation_state.json in /data directory
# Publishes status updates
```

**mqtt_simple.py** (Scheduled publisher):  
```python
# Reads state from /data/irrigation_state.json
# Checks recent irrigation history
# Publishes recommendations to MQTT
```

### Step 3: Addon Configuration

**config.yaml**:
```yaml  
name: "Irrigation Advisor"
map:
  - "share:rw"     # Access to shared data
services:
  - mqtt:need      # MQTT broker dependency
environment:
  DATA_DIR: "/data"
```

**run.sh**:
```bash
# Start background MQTT service
python3 mqtt_service.py &

# Run scheduled recommendations  
while true; do
  python3 mqtt_simple.py
  sleep 3600  # 1 hour
done
```

## 🏠 Praktikus Használat

### Automated Workflow:
1. **Addon** (óránként): recommendation → MQTT topics
2. **Home Assistant**: automation triggers irrigation
3. **Home Assistant**: publishes execution → `irrigation/scheduler/execute`  
4. **Addon**: receives execution → updates state → prevents duplicates

### Manual Override:
```yaml
# Home Assistant script  
script:
  manual_irrigation:
    sequence:
      - service: switch.turn_on
        entity_id: switch.irrigation_valve
      - service: mqtt.publish
        data:
          topic: "irrigation/scheduler/execute" 
          payload: '{"amount": 15.0, "notes": "Manual override"}'
```

## 🔄 Alternative Solutions

### A) REST API (Komplexebb)
- Addon exposes HTTP API on port 8080
- Home Assistant calls REST endpoints
- Requires port mapping and network configuration

### B) Shared Volume (Fájl-alapú)  
- Both containers mount same volume
- Communication via JSON files
- Simple but potential race conditions

### C) Home Assistant Services
- Addon registers as HA service
- Direct Python integration
- Requires addon to run in HA Python environment

## ✅ Recommended Architecture

**MQTT-based solution** a legpraktikusabb:

1. **Minimális konfiguráció** - MQTT broker már elérhető
2. **Reliable messaging** - Automatic retry és persistence  
3. **Event-driven** - Valós idejű válaszok
4. **Scalable** - Könnyen bővíthető további szenzorokkal
5. **Debugging-friendly** - MQTT messages könnyen monitorozhatók

### Production Setup:
```bash
# Addon container
/data/irrigation_state.json  # Persistent state
mqtt_service.py &           # Background listener
mqtt_simple.py              # Scheduled publisher (cron/systemd)

# Home Assistant  
MQTT sensors + automations  # React to recommendations
MQTT publish               # Report executions
```

Ez a megoldás **Docker-friendly**, **HA-native** és **production-ready**! 🚀
