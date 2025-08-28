#!/usr/bin/env python3
"""
🧪 MQTT Configuration Test
Test the new addon-config-based MQTT setup
"""

import json
import os

def test_config_loading():
    """Test the config loading function"""
    print("🧪 Testing MQTT config loading...")
    
    # Test data directory
    data_dir = "/data" if os.path.exists("/data") else "."
    config_file = os.path.join(data_dir, "options.json")
    
    # Create test config
    test_config = {
        "api_key": "test_api_key",
        "lat": 46.65,                   # Legacy format for irrigation_advisor.py
        "lon": 20.14,
        "latitude": 46.65,              # New addon format for MQTT config
        "longitude": 20.14,
        "mqtt_broker": "192.168.0.98",  # Your MQTT server
        "mqtt_port": 2883,              # Your MQTT port
        "mqtt_username": "",            # If you have credentials
        "mqtt_password": "",
        "units": "metric"
    }
    
    print(f"📁 Using data directory: {data_dir}")
    print(f"📄 Config file: {config_file}")
    
    # Write test config
    try:
        with open(config_file, 'w') as f:
            json.dump(test_config, f, indent=2)
        print("✅ Test config file created")
    except Exception as e:
        print(f"❌ Error creating config: {e}")
        return False
    
    # Test loading with mqtt_simple.py
    try:
        import sys
        sys.path.append(os.path.dirname(__file__))
        from mqtt_simple import load_addon_config
        
        mqtt_config = load_addon_config()
        
        print("\n📡 Loaded MQTT Config:")
        print(f"   Broker: {mqtt_config['MQTT_BROKER']}")
        print(f"   Port: {mqtt_config['MQTT_PORT']}")
        print(f"   Username: {mqtt_config['MQTT_USERNAME']}")
        print(f"   Client ID: {mqtt_config['MQTT_CLIENT_ID']}")
        print(f"   Topic Base: {mqtt_config['MQTT_TOPIC_BASE']}")
        
        # Validate config values
        if mqtt_config['MQTT_BROKER'] == "192.168.0.98" and mqtt_config['MQTT_PORT'] == 2883:
            print("✅ MQTT config loaded correctly from addon options!")
            return True
        else:
            print("❌ MQTT config values don't match expected")
            return False
            
    except Exception as e:
        print(f"❌ Error loading config: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_fallback_config():
    """Test fallback to mqtt_config.py"""
    print("\n🔄 Testing fallback config...")
    
    # Temporarily rename options.json
    data_dir = "/data" if os.path.exists("/data") else "."
    config_file = os.path.join(data_dir, "options.json")
    backup_file = config_file + ".backup"
    
    try:
        if os.path.exists(config_file):
            os.rename(config_file, backup_file)
            
        # Test fallback
        from mqtt_simple import load_addon_config
        mqtt_config = load_addon_config()
        
        print("📡 Fallback MQTT Config:")
        print(f"   Broker: {mqtt_config['MQTT_BROKER']}")
        print(f"   Port: {mqtt_config['MQTT_PORT']}")
        
        # Restore file
        if os.path.exists(backup_file):
            os.rename(backup_file, config_file)
            
        return True
        
    except Exception as e:
        print(f"❌ Fallback test error: {e}")
        # Restore file
        if os.path.exists(backup_file):
            os.rename(backup_file, config_file)
        return False

if __name__ == "__main__":
    print("🏠 Home Assistant Addon - MQTT Config Test")
    print("=" * 50)
    
    success1 = test_config_loading()
    success2 = test_fallback_config()
    
    if success1 and success2:
        print("\n🎉 All MQTT config tests passed!")
        print("✅ The addon will now read MQTT settings from Home Assistant UI")
        print("💡 You can configure your MQTT broker in the addon options")
    else:
        print("\n⚠️  Some tests failed. Check the errors above.")
