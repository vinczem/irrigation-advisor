# 🏠 **Irrigation Advisor - Egyszerűsített Telepítés**

## 📋 **Mi a helyzet?**

Az addon telepítésekor hibákat kaphatsz. Az alábbiakban megtalálod:
- ✅ **Egyszerűsített változat** - könnyebb telepítés
- 🔧 **Leggyakoribb hibák megoldása**  
- 📱 **Lépésről lépésre telepítési útmutató**

---

## 🚀 **GYORS TELEPÍTÉS - 3 perc alatt!**

### **1. lépés: Fájlok letöltése**
- Töltsd le a `simple_addon_package` mappát
- Vagy használd a `irrigation_advisor_simple.tar.gz` csomagot

### **2. lépés: Telepítés Home Assistant-ban**

#### **Módszer A: SSH/Terminal**
```bash
# SSH-val csatlakozz a Home Assistant-hoz
mkdir -p /usr/share/hassio/addons/local/irrigation_advisor

# Másold át a fájlokat (SCP/SFTP/SMB share)
cp -r simple_addon_package/* /usr/share/hassio/addons/local/irrigation_advisor/

# Engedélyek beállítása
chmod +x /usr/share/hassio/addons/local/irrigation_advisor/rootfs/run.sh
```

#### **Módszer B: File Editor Addon**
1. **Telepítsd a File Editor addon-t** Home Assistant-ban
2. **Hozd létre** a könyvtár struktúrát: `/usr/share/hassio/addons/local/irrigation_advisor/`
3. **Másold át** a fájlokat egyenként

### **3. lépés: Addon telepítése**
1. Home Assistant UI → **Supervisor** → **Add-on Store**
2. **Frissítsd** az oldalt (F5)
3. **Helyi addon-ok** szekciónban megjelenik: **"Irrigation Advisor (Simple)"**
4. **Telepítsd** → **Indítsd el**

### **4. lépés: Konfiguráció**
```yaml
api_key: "xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx"  # OpenWeatherMap API kulcs
latitude: 46.65                               # Koordináták
longitude: 20.14
mqtt_broker: "core-mosquitto"                # MQTT beállítások
mqtt_port: 1883
```

---

## ❌ **Leggyakoribb Hibák & Megoldások**

### **Hiba 1: "Build failed" vagy "Docker build error"**
```
ERROR: failed to solve: executor failed running [RUN chmod +x ...]
```

**Megoldás:**
- Ellenőrizd, hogy minden fájl a helyén van-e:
```bash
irrigation_advisor/
├── config.yaml
├── Dockerfile  
└── rootfs/
    ├── run.sh
    └── usr/bin/
        ├── irrigation_advisor.py
        ├── mqtt_simple.py
        └── ...
```

### **Hiba 2: "Schema validation failed"**
```
Invalid addon configuration
```

**Megoldás:**
- Használd az egyszerűsített `config.yaml`-t
- Ellenőrizd, hogy nincs-e szintaktikai hiba

### **Hiba 3: "Port already in use"**
```
Port 8099 is already allocated
```

**Megoldás:**
- Módosítsd a `config.yaml`-ban: `8099/tcp: 8098` 
- Vagy állítsd le a többi addon-t

### **Hiba 4: "Permission denied" 
```
/run.sh: Permission denied
```

**Megoldás:**
```bash
chmod +x /usr/share/hassio/addons/local/irrigation_advisor/rootfs/run.sh
chmod +x /usr/share/hassio/addons/local/irrigation_advisor/rootfs/usr/bin/*.py
```

---

## 🐛 **Hibakeresési Lépések**

### **1. Addon Log Ellenőrzése**
Home Assistant UI → Supervisor → Irrigation Advisor → **Log** tab

### **2. Container Status**
```bash
# SSH terminálban
docker ps | grep irrigation
docker logs addon_local_irrigation_advisor_simple
```

### **3. Fájlok Ellenőrzése**
```bash
# Ellenőrizd, hogy minden fájl megvan-e
ls -la /usr/share/hassio/addons/local/irrigation_advisor/
ls -la /usr/share/hassio/addons/local/irrigation_advisor/rootfs/usr/bin/
```

### **4. Manuális Test**
```bash
# Container-ben tesztelés
docker exec -it addon_local_irrigation_advisor_simple /bin/bash
cd /usr/bin
python3 irrigation_advisor.py
```

---

## 🎯 **Ha Minden Más Sikertelen...**

### **Minimális Verzió** (csak az alapfunkciók):

**config.yaml:**
```yaml
name: "Irrigation Test"
version: "0.1.0"
slug: "irrigation_test"
description: "Test irrigation"
arch: ["amd64"]
init: false
options:
  api_key: ""
schema:
  api_key: "str"
```

**Dockerfile:**
```dockerfile
FROM python:3.11-alpine
RUN pip install requests paho-mqtt
COPY rootfs /
RUN chmod +x /run.sh
CMD ["/run.sh"]
```

**run.sh:**
```bash
#!/bin/bash
echo "Starting irrigation test..."
cd /usr/bin
python3 mqtt_simple.py
sleep 3600
```

---

## 📞 **Segítségkérés**

Ha továbbra is problémáid vannak:

1. **Küldd el** a teljes hibaüzenetet
2. **Add meg** a Home Assistant verziódat: `ha core info`
3. **Csatold** a log-ot: Supervisor → Irrigation Advisor → Log → Copy
4. **Ellenőrizd** az architektúrát: `uname -m`

---

## 🌟 **Sikeres Telepítés Után**

### **Tesztelés:**
```bash
# MQTT üzenetek figyelése
mosquitto_sub -h localhost -t "irrigation/scheduler/+"

# Manuális javaslat kérése  
docker exec addon_local_irrigation_advisor_simple python3 /usr/bin/mqtt_simple.py
```

### **Home Assistant Integráció:**
```yaml
# configuration.yaml
shell_command:
  irrigation_check: "docker exec addon_local_irrigation_advisor_simple python3 /usr/bin/mqtt_simple.py"

automation:
  - alias: "Reggeli öntözési ellenőrzés"
    trigger:
      - platform: time
        at: "06:00:00"
    action:
      - service: shell_command.irrigation_check
```

---

**🤞 Remélem ez segít! Mi a pontos hibaüzenet?**
