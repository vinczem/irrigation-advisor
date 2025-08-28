# 🚨 **Addon Telepítési Hibák Megoldása**

## ❌ **Leggyakoribb Telepítési Problémák**

### **1. Dockerfile Build Hibák**

```bash
# Hiba: Permission denied vagy File not found
ERROR: failed to solve: executor failed running [RUN chmod +x /usr/bin/run.sh]
```

**Megoldás:** ✅
- Ellenőrizd, hogy a `rootfs/` könyvtár struktúra helyes-e
- A `run.sh` fájlnak a `rootfs/` gyökérben kell lennie
- Python scriptek a `rootfs/usr/bin/` könyvtárban

### **2. Konfiguráció Séma Hiba**

```bash
# Hiba: Config validation failed
Schema validation failed
```

**Megoldás:** ✅ Ellenőrizd a `config.yaml` fájlt:
```yaml
name: "Irrigation Advisor"
version: "1.0.0"
slug: "irrigation_advisor"
description: "Intelligent lawn irrigation advisor"
arch:
  - aarch64
  - amd64
  - armv7
init: false
options:
  api_key: ""
  latitude: 46.65
  longitude: 20.14
  mqtt_broker: "core-mosquitto"
  mqtt_port: 1883
  mqtt_username: ""
  mqtt_password: ""
  log_level: "INFO"
schema:
  api_key: "str"
  latitude: "float"
  longitude: "float"
  mqtt_broker: "str"
  mqtt_port: "port"
  mqtt_username: "str?"
  mqtt_password: "password?"
  log_level: "list(DEBUG|INFO|WARNING|ERROR)?"
services:
  - "mqtt:want"
ports:
  8099/tcp: null
```

### **3. Base Image Hiba**

```bash
# Hiba: failed to solve: ghcr.io/hassio-addons/base-python:13.2.0
```

**Megoldás:** ✅ Használj más base image-t:
```dockerfile
ARG BUILD_FROM=ghcr.io/home-assistant/amd64-base-python:3.11-alpine3.18
FROM $BUILD_FROM
```

### **4. Függőségek Hiánya**

```bash
# Hiba: ImportError vagy ModuleNotFoundError
```

**Megoldás:** ✅ Dockerfileben:
```dockerfile
RUN apk add --no-cache \
    gcc \
    musl-dev \
    jq \
    curl \
    && pip install --no-cache-dir \
    paho-mqtt==2.1.0 \
    requests \
    && apk del gcc musl-dev
```

## 🔧 **Gyors Javítási Lépések**

### **1. Fájlok Ellenőrzése**
```bash
# Könyvtár struktúra
irrigation_advisor/
├── config.yaml          ✅ Kötelező
├── Dockerfile           ✅ Kötelező  
├── README.md            ✅ Opcionális
└── rootfs/              ✅ Kötelező
    ├── run.sh           ✅ Kötelező (gyökérben!)
    └── usr/bin/         ✅ Python scriptek
        ├── irrigation_advisor.py
        ├── mqtt_simple.py
        ├── mqtt_service.py
        └── ...
```

### **2. Engedélyek Beállítása**
```bash
chmod +x irrigation_advisor/rootfs/run.sh
chmod +x irrigation_advisor/rootfs/usr/bin/*.py
```

### **3. Telepítési Parancsok**
```bash
# Home Assistant gépen
mkdir -p /usr/share/hassio/addons/local/irrigation_advisor
cp -r irrigation_advisor/* /usr/share/hassio/addons/local/irrigation_advisor/

# Újraindítás
systemctl restart hassio-supervisor
```

### **4. Konfiguráció Validálás**
```bash
# config.yaml ellenőrzés
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# JSON options ellenőrzés  
jq '.' config.yaml
```

## 🐛 **Hibakeresés**

### **Build Log Ellenőrzése**
```bash
# Home Assistant UI-ban -> Supervisor -> Add-on Store -> Local Add-ons
# Telepítés közben nézd a "Log" tabot
```

### **Container Log Nézése**
```bash
# SSH terminálban
docker logs addon_local_irrigation_advisor
```

### **Fájlok Elérhetősége**
```bash
# Container-ben  
docker exec -it addon_local_irrigation_advisor ls -la /usr/bin/
docker exec -it addon_local_irrigation_advisor ls -la /data/
```

## 🚀 **Minimális Működő Konfiguráció**

Ha továbbra is problémáid vannak, használd ezt a egyszerűsített verziót:

### **Dockerfile (minimális)**
```dockerfile
FROM python:3.11-alpine

RUN apk add --no-cache jq curl
RUN pip install paho-mqtt requests

COPY rootfs /

RUN chmod +x /run.sh
RUN chmod +x /usr/bin/*.py

CMD ["/run.sh"]
```

### **run.sh (egyszerűsített)**
```bash
#!/bin/bash
set -e

echo "🏠 Starting Irrigation Advisor..."

# Health check háttérben
python3 -m http.server 8099 &

# MQTT service indítása
cd /usr/bin
python3 mqtt_service.py &

# Várakozás
wait
```

### **config.yaml (minimális)**
```yaml
name: "Irrigation Advisor"
version: "1.0.0"
slug: "irrigation_advisor"
description: "Irrigation advisor"
arch: ["amd64", "armv7", "aarch64"]
init: false
options:
  api_key: ""
schema:
  api_key: "str"
```

## 📞 **Ha Még Mindig Nem Működik**

1. **Küld el a teljes hibaüzenetet** a telepítési logból
2. **Ellenőrizd a Home Assistant verziót**: `ha core info`
3. **Próbáld ki másik architektúrával**: csak `amd64` vagy csak `armv7`
4. **Használj egyszerűbb base image-t**: `python:3.11-alpine`

---

**Mi a pontos hibaüzenet, amit kapsz a telepítéskor? 🤔**
