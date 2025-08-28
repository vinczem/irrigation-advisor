#!/bin/bash

echo "🚀 EGYSZERŰ ADDON FRISSÍTÉS"
echo "========================="

echo "📋 Current addon files:"
echo "  📄 config.yaml - v$(grep version config.yaml | cut -d'"' -f2)"
echo "  🔧 run.sh - $(wc -l < run.sh) lines"
echo "  🐍 mqtt_simple.py - $(wc -l < mqtt_simple.py) lines"
echo ""

echo "⏰ Scheduler check:"
if grep -q "irrigation_scheduler" run.sh; then
    echo "  ✅ Scheduler function found in run.sh"
else
    echo "  ❌ Scheduler function missing!"
fi

if grep -q "log_with_timestamp" mqtt_simple.py; then
    echo "  ✅ Timestamped logging found in mqtt_simple.py"
else
    echo "  ❌ Timestamped logging missing!"
fi

echo ""
echo "🏠 Home Assistant addon frissítés:"
echo "1. Menj Settings > Add-ons > Irrigation Advisor"
echo "2. Stop the addon"
echo "3. Kattints a ⋮ menü > Rebuild"
echo "4. Start the addon"
echo ""
echo "📊 Várható log üzenetek restart után:"
echo "  ⏰ Irrigation scheduler started (PID: XXX)"
echo "  🌱 [$(date '+%Y-%m-%d %H:%M:%S')] Starting automatic irrigation check..."
