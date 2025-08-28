#!/usr/bin/env python3
"""
Log viewer for irrigation system - watch addon logs in real-time
"""

import time
import subprocess
import sys
from datetime import datetime

def log_with_timestamp(message):
    """Log with timestamp"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{timestamp}] {message}", flush=True)

def watch_addon_logs():
    """Watch Home Assistant addon logs in real-time"""
    log_with_timestamp("🔍 Starting irrigation system log monitor...")
    log_with_timestamp("📋 Watching for automatic irrigation checks...")
    log_with_timestamp("⏰ Press Ctrl+C to stop monitoring")
    print()
    
    try:
        # Use docker logs with follow flag to stream logs
        process = subprocess.Popen(
            ['docker', 'logs', '-f', '--tail', '10', 'addon_local_irrigation_advisor_simple'],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            bufsize=1
        )
        
        for line in process.stdout:
            line = line.strip()
            if line:
                # Highlight important irrigation events
                if "irrigation check" in line.lower():
                    print(f"🌱 {line}")
                elif "scheduled for" in line.lower():
                    print(f"⏰ {line}")
                elif "mqtt publication" in line.lower():
                    print(f"📡 {line}")
                elif "error" in line.lower() or "failed" in line.lower():
                    print(f"❌ {line}")
                elif "warning" in line.lower():
                    print(f"⚠️  {line}")
                elif "completed" in line.lower() or "successful" in line.lower():
                    print(f"✅ {line}")
                else:
                    print(f"ℹ️  {line}")
                    
    except KeyboardInterrupt:
        log_with_timestamp("🛑 Log monitoring stopped")
        process.terminate()
    except FileNotFoundError:
        log_with_timestamp("❌ Docker command not found. Make sure Docker is installed and running.")
    except subprocess.SubprocessError as e:
        log_with_timestamp(f"❌ Error accessing addon logs: {e}")
        log_with_timestamp("💡 Alternative: Check logs in Home Assistant UI: Settings > Add-ons > Irrigation Advisor > Log")

def show_next_check_time():
    """Calculate and show when the next automatic check should occur"""
    try:
        # Try to read the current addon configuration
        import json
        import os
        
        config_path = "/data/options.json"
        if os.path.exists(config_path):
            with open(config_path, 'r') as f:
                config = json.load(f)
            
            interval_minutes = config.get('check_interval_minutes', 30)
            auto_check_enabled = config.get('enable_auto_check', True)
            
            if auto_check_enabled:
                from datetime import timedelta
                next_check = datetime.now() + timedelta(minutes=interval_minutes)
                log_with_timestamp(f"⏰ Next automatic check should occur around: {next_check.strftime('%Y-%m-%d %H:%M:%S')}")
                log_with_timestamp(f"🕐 Check interval: {interval_minutes} minutes")
            else:
                log_with_timestamp("⏸️ Automatic checks are disabled")
        else:
            log_with_timestamp("⚠️ Cannot determine check schedule - config file not found")
            
    except Exception as e:
        log_with_timestamp(f"⚠️ Cannot determine check schedule: {e}")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--schedule":
        show_next_check_time()
    else:
        watch_addon_logs()
