#!/usr/bin/env python3
"""
Test script to verify timestamp logging is working
"""

from datetime import datetime
import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(__file__))

# Import the modified mqtt_simple
import mqtt_simple

def test_logging():
    """Test the enhanced logging function"""
    print("🧪 Testing enhanced logging...")
    
    # Test the log_with_timestamp function
    mqtt_simple.log_with_timestamp("Test message", "INFO")
    mqtt_simple.log_with_timestamp("Warning message", "WARN") 
    mqtt_simple.log_with_timestamp("Error message", "ERROR")
    
    print("\n✅ Timestamp logging test completed!")
    
    # Test the actual irrigation check (if config is available)
    print("\n🌱 Testing irrigation recommendation...")
    try:
        result = mqtt_simple.main()
        print(f"📊 Result: {result}")
    except Exception as e:
        print(f"⚠️ Test failed: {e}")

if __name__ == "__main__":
    test_logging()
