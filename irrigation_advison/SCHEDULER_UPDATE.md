# Irrigation Advisor v2.1.0 - Automatic Scheduler Update

## ✨ New Features

### 🕒 **Automatic Irrigation Checks**
- Built-in scheduler runs irrigation checks automatically
- No need for Home Assistant automations
- Configurable check intervals (5 minutes to 24 hours)
- Can be enabled/disabled via addon configuration

### ⚙️ **New Configuration Options**

```yaml
# config.yaml additions
enable_auto_check: true           # Enable/disable automatic checks
check_interval_minutes: 30        # Check every 30 minutes
log_level: "info"                # Debug verbosity level
```

### 📊 **Enhanced Health Endpoint**
- Health check now shows scheduler status
- View at: http://homeassistant:8099/health
- Includes auto-check status and interval

## 🎯 **How It Works**

### **1. Background Processes**
The addon now runs 3 background services:
- **MQTT Service**: Handles MQTT communications
- **Health Service**: Provides system status on port 8099
- **Irrigation Scheduler**: Automatic irrigation checks

### **2. Automatic Checks**
```bash
# Every X minutes (configurable):
python3 /usr/bin/mqtt_simple.py
```

### **3. Process Monitoring**
- All services are monitored and auto-restarted if they crash
- Graceful shutdown handling
- Detailed logging for troubleshooting

## 🛠️ **Configuration Examples**

### **Quick Setup (30-minute checks):**
```yaml
api_key: "your_openweather_api_key"
latitude: 46.65
longitude: 20.14
mqtt_broker: "core-mosquitto"
mqtt_port: 1883
enable_auto_check: true
check_interval_minutes: 30
```

### **Frequent Monitoring (every 10 minutes):**
```yaml
enable_auto_check: true
check_interval_minutes: 10
log_level: "debug"
```

### **Manual Mode Only (no auto checks):**
```yaml
enable_auto_check: false
# Still allows manual triggers via HA
```

## 🔍 **Monitoring & Debugging**

### **Health Check:**
```bash
curl http://homeassistant:8099/health
```

### **View Logs:**
```bash
# In Home Assistant:
# Settings > Add-ons > Irrigation Advisor > Log tab

# Via command line:
docker logs addon_local_irrigation_advisor_simple
```

### **Check Process Status:**
All processes show their PID in logs:
```
🔄 MQTT service started (PID: 123)
🔍 Health service started on port 8099 (PID: 124) 
⏰ Irrigation scheduler started (PID: 125)
```

## 🚀 **Benefits**

1. **Set & Forget**: Configure once, runs automatically
2. **Reliable**: Process monitoring and auto-restart
3. **Flexible**: Configurable intervals from 5 min to 24 hours
4. **Compatible**: Still works with manual Home Assistant triggers
5. **Debuggable**: Enhanced logging and health monitoring

## 📝 **Migration from v2.0.0**

Existing installations will work unchanged:
- Default: `enable_auto_check: true` (30-minute intervals)
- Home Assistant automations still work as before
- No breaking changes to MQTT topics or sensor names

## 🎛️ **Configuration UI**

In Home Assistant:
1. **Settings** → **Add-ons** → **Irrigation Advisor**
2. **Configuration** tab
3. Set your preferences:
   - ✅ **Enable Auto Check**: Turn automatic scheduling on/off
   - ⏰ **Check Interval**: Minutes between checks (5-1440)
   - 📋 **Log Level**: Verbosity (debug/info/warning/error)

Perfect for users who want a fully automated irrigation monitoring system! 🌱💧
