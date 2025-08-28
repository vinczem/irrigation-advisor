#!/bin/bash

# ADDON UPDATE SCRIPT
# Run this to rebuild and update the Home Assistant addon

echo "🔄 Updating Irrigation Advisor Addon..."
echo "========================================"

# 1. Check current version
echo "📋 Current version info:"
grep -E "version|description" config.yaml

echo ""
echo "🏗️ Building new addon version..."

# 2. Create build.yaml with cache busting
cat > build.yaml << 'EOF'
build_from:
  amd64: "ghcr.io/home-assistant/amd64-base-python:3.11"
  armv7: "ghcr.io/home-assistant/armv7-base-python:3.11"
  aarch64: "ghcr.io/home-assistant/aarch64-base-python:3.11"
args:
  CACHE_BUST: "20250828185500"
labels:
  org.opencontainers.image.title: "Irrigation Advisor"
  org.opencontainers.image.description: "Weather-based irrigation system with scheduler"
  org.opencontainers.image.source: "https://github.com/vinczem/irrigation-advisor"
  org.opencontainers.image.licenses: "MIT"
EOF

# 3. Create addon package for Home Assistant
echo "� Creating addon package..."

# Create a temporary package directory
mkdir -p addon_package
cp config.yaml addon_package/
cp build.yaml addon_package/
cp Dockerfile addon_package/
cp run.sh addon_package/
cp *.py addon_package/ 2>/dev/null || true

echo "✅ Addon package created in addon_package/"

echo ""
echo "🔄 Steps to update addon in Home Assistant:"
echo "1. Stop the current addon in Home Assistant"
echo "2. Go to Settings > Add-ons > Browse & Backup tab"
echo "3. Upload the addon_package/ folder as a new local addon"
echo "4. Or use the existing local addon and rebuild it"
echo "5. Start the addon again"
echo ""
echo "📊 After restart, check logs for:"
echo "   ⏰ Irrigation scheduler started (PID: XXX)"
echo "   🌱 [YYYY-MM-DD HH:MM:SS] Starting automatic irrigation check..."
echo ""
echo "💡 Or use: docker logs -f addon_local_irrigation_advisor"
