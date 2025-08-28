#!/usr/bin/env python3
"""
🧪 Addon Service Test Script
Tests both continuous and triggered service components
"""

import subprocess
import time
import json
import requests
from datetime import datetime

def test_health_service():
    """Test the health check endpoint"""
    print("🏥 Testing health check service...")
    try:
        response = requests.get("http://localhost:8099/health", timeout=5)
        if response.status_code == 200:
            health_data = response.json()
            print(f"✅ Health check OK: {health_data}")
            return True
        else:
            print(f"❌ Health check failed: {response.status_code}")
            return False
    except Exception as e:
        print(f"❌ Health check error: {e}")
        return False

def test_mqtt_simple():
    """Test the recommendation publisher"""
    print("📡 Testing irrigation recommendation publisher...")
    try:
        result = subprocess.run(
            ["python3", "mqtt_simple.py"], 
            capture_output=True, 
            text=True,
            timeout=30
        )
        
        if result.returncode == 0:
            print("✅ MQTT simple publisher executed successfully")
            print(f"Output: {result.stdout}")
            return True
        else:
            print(f"❌ MQTT simple publisher failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ MQTT simple publisher error: {e}")
        return False

def test_state_management():
    """Test irrigation state management"""
    print("📝 Testing state management...")
    try:
        # Check status
        result = subprocess.run(
            ["python3", "irrigation_cli.py", "status"], 
            capture_output=True, 
            text=True
        )
        
        if result.returncode == 0:
            print("✅ State management working")
            print(f"Status: {result.stdout}")
            return True
        else:
            print(f"❌ State management failed: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ State management error: {e}")
        return False

def simulate_addon_startup():
    """Simulate addon startup sequence"""
    print("\n🚀 Simulating Home Assistant Addon Startup...")
    print("=" * 50)
    
    # Test 1: Health Service
    health_ok = test_health_service()
    
    # Test 2: State Management
    state_ok = test_state_management()
    
    # Test 3: Recommendation Publisher
    mqtt_ok = test_mqtt_simple()
    
    # Summary
    print("\n📊 Test Results:")
    print("=" * 30)
    print(f"🏥 Health Service: {'✅ PASS' if health_ok else '❌ FAIL'}")
    print(f"📝 State Management: {'✅ PASS' if state_ok else '❌ FAIL'}")
    print(f"📡 MQTT Publisher: {'✅ PASS' if mqtt_ok else '❌ FAIL'}")
    
    all_tests_passed = health_ok and state_ok and mqtt_ok
    print(f"\n🎯 Overall Result: {'✅ ALL TESTS PASSED' if all_tests_passed else '❌ SOME TESTS FAILED'}")
    
    return all_tests_passed

if __name__ == "__main__":
    print("🏠 Home Assistant Irrigation Advisor - Service Test")
    print(f"⏰ Test started at: {datetime.now()}")
    
    # Check if we have required files
    required_files = [
        "mqtt_simple.py",
        "irrigation_cli.py", 
        "irrigation_state.py"
    ]
    
    missing_files = []
    for file in required_files:
        try:
            with open(file, 'r') as f:
                pass
        except FileNotFoundError:
            missing_files.append(file)
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        print("Please ensure all Python scripts are in the current directory")
        exit(1)
    
    # Run the test simulation
    success = simulate_addon_startup()
    
    if success:
        print("\n🎉 All tests passed! The addon services are ready for deployment.")
        print("💡 Next steps:")
        print("   1. Create the complete addon directory structure")
        print("   2. Copy all files to /usr/share/hassio/addons/local/irrigation_advisor/")
        print("   3. Install the addon through Home Assistant UI")
        print("   4. Configure with your OpenWeatherMap API key")
    else:
        print("\n⚠️  Some tests failed. Please check the errors above.")
    
    exit(0 if success else 1)
