#!/usr/bin/env python3
"""
Simple File-based Irrigation State Manager
Egyszerű fájl alapú megoldás MQTT feedback nélkül
"""

import json
import os
from datetime import datetime, timedelta

# State file for tracking irrigation
STATE_FILE = "irrigation_state.json"

class SimpleIrrigationState:
    def __init__(self):
        self.state_file = STATE_FILE
        self.state = self.load_state()
    
    def load_state(self):
        """Load irrigation state from file"""
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, 'r', encoding='utf-8') as f:
                    state = json.load(f)
                print(f"📂 State loaded from {self.state_file}")
                return state
            except Exception as e:
                print(f"⚠️ Error loading state: {e}")
                return self.default_state()
        else:
            print(f"📂 Creating new state file: {self.state_file}")
            return self.default_state()
    
    def default_state(self):
        """Default state structure"""
        return {
            "last_recommendation": None,
            "last_execution": None,  # Manual entry
            "irrigation_log": [],
            "version": "1.0"
        }
    
    def save_state(self):
        """Save state to file"""
        try:
            with open(self.state_file, 'w', encoding='utf-8') as f:
                json.dump(self.state, f, indent=2, ensure_ascii=False)
            print(f"💾 State saved to {self.state_file}")
        except Exception as e:
            print(f"❌ Error saving state: {e}")
    
    def log_recommendation(self, amount, reason):
        """Log irrigation recommendation"""
        recommendation = {
            "timestamp": datetime.now().isoformat(),
            "amount_lpm2": amount,
            "reason": reason,
            "executed": False,
            "execution_time": None,
            "execution_amount": None
        }
        
        self.state["last_recommendation"] = recommendation
        self.state["irrigation_log"].append(recommendation)
        
        # Keep only last 50 entries
        if len(self.state["irrigation_log"]) > 50:
            self.state["irrigation_log"] = self.state["irrigation_log"][-50:]
        
        self.save_state()
        print(f"📝 Recommendation logged: {amount}L/m² - {reason}")
        return len(self.state["irrigation_log"]) - 1  # Return index
    
    def mark_executed(self, execution_amount=None, notes=""):
        """Manually mark last recommendation as executed"""
        if self.state["last_recommendation"] and not self.state["last_recommendation"]["executed"]:
            self.state["last_recommendation"]["executed"] = True
            self.state["last_recommendation"]["execution_time"] = datetime.now().isoformat()
            self.state["last_recommendation"]["execution_amount"] = execution_amount or self.state["last_recommendation"]["amount_lpm2"]
            
            if notes:
                self.state["last_recommendation"]["notes"] = notes
            
            # Update in log as well
            for entry in reversed(self.state["irrigation_log"]):
                if not entry["executed"] and entry["timestamp"] == self.state["last_recommendation"]["timestamp"]:
                    entry.update(self.state["last_recommendation"])
                    break
            
            self.save_state()
            print(f"✅ Marked as executed: {execution_amount or 'recommended amount'}L/m²")
        else:
            print("⚠️ No pending recommendation to mark as executed")
    
    def get_recent_irrigation(self, hours=24):
        """Get recent executed irrigation"""
        cutoff = datetime.now() - timedelta(hours=hours)
        
        recent = []
        for entry in reversed(self.state["irrigation_log"]):
            if entry["executed"] and entry["execution_time"]:
                exec_time = datetime.fromisoformat(entry["execution_time"])
                if exec_time > cutoff:
                    recent.append(entry)
        
        return recent
    
    def should_skip_recommendation(self, hours=6):
        """Check if should skip due to recent irrigation"""
        recent = self.get_recent_irrigation(hours)
        
        if recent:
            total_amount = sum(entry["execution_amount"] or 0 for entry in recent)
            print(f"ℹ️ Recent irrigation in last {hours}h: {total_amount}L/m²")
            
            # Skip if recently irrigated significantly
            if total_amount > 5:  # More than 5L/m² recently
                return True, total_amount
        
        return False, 0
    
    def get_status_summary(self):
        """Get current status summary"""
        last_rec = self.state["last_recommendation"]
        recent = self.get_recent_irrigation(24)
        
        summary = {
            "last_recommendation": {
                "time": last_rec["timestamp"][:19] if last_rec else None,
                "amount": last_rec["amount_lpm2"] if last_rec else 0,
                "executed": last_rec["executed"] if last_rec else False
            },
            "recent_24h": {
                "count": len(recent),
                "total_amount": sum(e["execution_amount"] or 0 for e in recent)
            },
            "pending_recommendations": len([e for e in self.state["irrigation_log"] if not e["executed"]])
        }
        
        return summary


def demo_manual_workflow():
    """Demo of manual workflow"""
    
    print("🔧 MANUAL IRRIGATION STATE DEMO")
    print("=" * 35)
    
    state = SimpleIrrigationState()
    
    # Show current status
    summary = state.get_status_summary()
    print(f"📊 Current status:")
    print(f"   Last recommendation: {summary['last_recommendation']['time']}")
    print(f"   Pending: {summary['pending_recommendations']}")
    print(f"   Recent 24h: {summary['recent_24h']['count']} irrigation(s)")
    
    print()
    print("🎮 Manual commands:")
    print("   python3 -c \"from irrigation_state import SimpleIrrigationState; s=SimpleIrrigationState(); s.mark_executed(10.5, 'Manual irrigation')\"")
    print("   python3 -c \"from irrigation_state import SimpleIrrigationState; s=SimpleIrrigationState(); print(s.get_status_summary())\"")
    
    return state


if __name__ == "__main__":
    demo_manual_workflow()
