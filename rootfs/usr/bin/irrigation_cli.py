#!/usr/bin/env python3
"""
Irrigation Management CLI Tools
Egyszerű parancssori eszközök az öntözés nyilvántartásához
"""

import sys
from irrigation_state import SimpleIrrigationState
from datetime import datetime

def show_status():
    """Show current irrigation status"""
    state = SimpleIrrigationState()
    summary = state.get_status_summary()
    
    print("📊 ÖNTÖZÉSI ÁLLAPOT")
    print("=" * 25)
    
    last_rec = summary['last_recommendation']
    if last_rec['time']:
        status = "✅ Elvégezve" if last_rec['executed'] else "⏳ Függőben"
        print(f"🕐 Utolsó javaslat: {last_rec['time']} - {last_rec['amount']}L/m² - {status}")
    else:
        print("🕐 Még nem volt javaslat")
    
    print(f"📈 Utóbbi 24 órában: {summary['recent_24h']['count']} öntözés, összesen {summary['recent_24h']['total_amount']}L/m²")
    print(f"⏳ Függőben lévő: {summary['pending_recommendations']} javaslat")
    
    # Show recent irrigation history
    recent = state.get_recent_irrigation(48)
    if recent:
        print(f"\n📋 Legutóbbi öntözések (48h):")
        for entry in recent[:5]:
            exec_time = entry['execution_time'][:16] if entry['execution_time'] else 'N/A'
            amount = entry['execution_amount'] or entry['amount_lpm2']
            print(f"   {exec_time} - {amount}L/m²")

def mark_irrigation(amount_str, notes=""):
    """Mark irrigation as executed"""
    try:
        amount = float(amount_str)
        state = SimpleIrrigationState()
        state.mark_executed(amount, notes)
        print(f"✅ Öntözés rögzítve: {amount}L/m²")
        if notes:
            print(f"📝 Megjegyzés: {notes}")
    except ValueError:
        print(f"❌ Hibás mennyiség: {amount_str}")

def clear_state():
    """Clear irrigation state (with confirmation)"""
    response = input("⚠️  Biztosan törölni szeretnéd az állapotot? (yes/no): ")
    if response.lower() in ['yes', 'y', 'igen', 'i']:
        import os
        from irrigation_state import STATE_FILE
        if os.path.exists(STATE_FILE):
            os.remove(STATE_FILE)
            print(f"🗑️  Állapotfájl törölve: {STATE_FILE}")
        else:
            print("ℹ️  Nincs állapotfájl")
    else:
        print("❌ Művelet megszakítva")

def main():
    """CLI interface"""
    if len(sys.argv) < 2:
        print("🔧 ÖNTÖZÉSI MANAGEMENT ESZKÖZÖK")
        print("=" * 35)
        print("Használat:")
        print(f"  {sys.argv[0]} status              - Állapot megtekintése")
        print(f"  {sys.argv[0]} mark <mennyiség>    - Öntözés rögzítése (L/m²)")
        print(f"  {sys.argv[0]} mark <mennyiség> '<megjegyzés>' - Öntözés rögzítése megjegyzéssel")
        print(f"  {sys.argv[0]} clear               - Állapot törlése")
        print()
        print("Példák:")
        print(f"  {sys.argv[0]} status")
        print(f"  {sys.argv[0]} mark 10.5")
        print(f"  {sys.argv[0]} mark 8.0 'Manual watering'")
        return
    
    command = sys.argv[1].lower()
    
    if command == 'status':
        show_status()
    elif command == 'mark':
        if len(sys.argv) >= 3:
            amount = sys.argv[2]
            notes = sys.argv[3] if len(sys.argv) >= 4 else ""
            mark_irrigation(amount, notes)
        else:
            print("❌ Hiányzó mennyiség paraméter")
    elif command == 'clear':
        clear_state()
    else:
        print(f"❌ Ismeretlen parancs: {command}")

if __name__ == "__main__":
    main()
