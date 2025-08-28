#!/bin/bash
# 🔍 Home Assistant Addon Visibility Debug

echo "🏠 HOME ASSISTANT ADDON DEBUG"
echo "============================="

# 1. Ellenőrizzük a könyvtár struktúrát
echo "📁 Addon könyvtár struktúra:"
ls -la /usr/share/hassio/addons/local/

echo ""
echo "📂 Helyi addon-ok:"
for dir in /usr/share/hassio/addons/local/*/; do
    if [ -d "$dir" ]; then
        echo "  → $(basename "$dir")"
        
        # Config.yaml ellenőrzés
        if [ -f "${dir}config.yaml" ]; then
            echo "    ✅ config.yaml megvan"
            
            # Név és verzió kiolvasása
            name=$(grep "^name:" "${dir}config.yaml" | cut -d'"' -f2)
            version=$(grep "^version:" "${dir}config.yaml" | cut -d'"' -f2)
            slug=$(grep "^slug:" "${dir}config.yaml" | head -1)
            
            echo "    📝 Name: $name"  
            echo "    🏷️  Version: $version"
            echo "    🔗 Slug: $slug"
            
            # YAML syntax ellenőrzés
            if python3 -c "import yaml; yaml.safe_load(open('${dir}config.yaml'))" 2>/dev/null; then
                echo "    ✅ YAML syntax OK"
            else
                echo "    ❌ YAML syntax ERROR!"
            fi
        else
            echo "    ❌ config.yaml HIÁNYZIK!"
        fi
        
        # Dockerfile ellenőrzés
        if [ -f "${dir}Dockerfile" ]; then
            echo "    ✅ Dockerfile megvan"
        else
            echo "    ❌ Dockerfile HIÁNYZIK!"
        fi
        
        echo ""
    fi
done

# 2. Supervisor szolgáltatás állapot
echo "🔄 Supervisor állapot:"
systemctl is-active hassio-supervisor

# 3. Supervisor logok (utolsó 5 sor)
echo ""
echo "📋 Supervisor log (utolsó 5 sor):"
journalctl -u hassio-supervisor --no-pager -n 5

echo ""
echo "💡 Ha nem látod az addon-t:"
echo "   1. systemctl restart hassio-supervisor"
echo "   2. Várj 30 másodpercet"  
echo "   3. Frissítsd a böngészőt (Ctrl+F5)"
