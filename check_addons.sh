#!/bin/bash

echo "🔍 ADDON ELLENŐRZŐ SCRIPT"
echo "========================"
echo ""

echo "📋 Home Assistant addon mappák:"
echo ""

# Ellenőrizzük, melyik addon van telepítve
if [ -d "/usr/share/hassio/addons/local" ]; then
    echo "🏠 Local addon mappa:"
    ls -la /usr/share/hassio/addons/local/ 2>/dev/null || echo "❌ Nem elérhető"
fi

echo ""
echo "🔍 Docker konténerek keresése:"
docker ps | grep irrigation 2>/dev/null || echo "❌ Nincs futó irrigation konténer"

echo ""
echo "🔍 Docker image-ek keresése:"
docker images | grep irrigation 2>/dev/null || echo "❌ Nincs irrigation image"

echo ""
echo "📊 A két addon különbsége:"
echo ""
echo "1️⃣ FŐ ADDON (irrigation_advisor):"
echo "   📁 Hely: gyökérmappa/"
echo "   🏷️ Slug: irrigation_advisor"  
echo "   📝 Verzió: $(grep version /Users/vmihaly/dev/Python/vm-ha-openweathermap/config.yaml | cut -d'"' -f2)"
echo "   ⏰ Scheduler: VAN"
echo ""
echo "2️⃣ EGYSZERŰ ADDON (irrigation_advisor_simple):"
echo "   📁 Hely: simple_addon_package/"
echo "   🏷️ Slug: irrigation_advisor_simple"
echo "   📝 Verzió: $(grep version /Users/vmihaly/dev/Python/vm-ha-openweathermap/simple_addon_package/config.yaml | cut -d'"' -f2)"
echo "   ⏰ Scheduler: NINCS"
echo ""
echo "💡 MEGOLDÁS:"
echo "   - Töröld az 'Irrigation Advisor (Simple)' addont"
echo "   - Használd csak a fő 'Irrigation Advisor' addont"
