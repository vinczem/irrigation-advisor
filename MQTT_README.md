# MQTT Integráció - Öntözési Tanácsadó

Ez a modul MQTT üzeneteket publikál az öntözési rendszer javaslataiból.

## Fájlok

### `mqtt_config.py`
Konfigurációs fájl az MQTT beállításokhoz:
- Broker címe és port
- Topic struktura
- Authentication beállítások

### `mqtt_simple.py`
Egyszerű MQTT publisher, ami pontosan olyan formátumot használ, mint amit mutattál:
```json
{
  "watering_required": false,
  "water_amount_lpm2": 0,
  "reason": "recent_heavy_rain"
}
```

### `mqtt_publisher.py`
Részletes MQTT publisher több topic-ra és bővebb adatokkal.

### `mqtt_dryrun.py`
Tesztelő verzió, ami nem küld valós MQTT üzenetet, csak szimulál.

## Használat

### 1. MQTT Broker beállítása

Módosítsd az `mqtt_config.py` fájlt:
```python
MQTT_BROKER = "your_broker_ip"  # pl: "192.168.1.100"
MQTT_PORT = 1883
MQTT_USERNAME = "your_username"  # ha szükséges
MQTT_PASSWORD = "your_password"  # ha szükséges
```

### 2. Függőségek telepítése

```bash
pip install paho-mqtt
```

### 3. Egyszerű használat

```bash
python3 mqtt_simple.py
```

Kimenet:
```
Published message: {'watering_required': False, 'water_amount_lpm2': 0, 'reason': 'recent_heavy_rain'}
✅ Published to garden/irrigation/simple
```

### 4. Tesztelés MQTT broker nélkül

```bash
python3 mqtt_dryrun.py
```

## MQTT Topic struktúra

### Egyszerű verzió (mqtt_simple.py):
- `irrigation/scheduler/raw` - Teljes JSON üzenet magyar indoklással
- `irrigation/scheduler/watering_required` - Boolean érték (true/false)
- `irrigation/scheduler/water_amount` - Numerikus érték (liter/m²)
- `irrigation/scheduler/reason` - Magyar indoklás teljes szöveggel

Példa publikálás:
```bash
Topic: irrigation/scheduler/raw
Payload: {"watering_required": false, "water_amount_lpm2": 0, "reason": "Talaj jól öntözött, többlet: 21.8mm"}

Topic: irrigation/scheduler/watering_required
Payload: false

Topic: irrigation/scheduler/water_amount  
Payload: 0

Topic: irrigation/scheduler/reason
Payload: Talaj jól öntözött, többlet: 21.8mm
```

### Részletes verzió (mqtt_publisher.py):
- `irrigation/scheduler/status` - Teljes részletes státusz JSON
- `irrigation/scheduler/watering_required` - Boolean: kell-e öntözni
- `irrigation/scheduler/water_amount` - Float: liter/m²
- `irrigation/scheduler/reason` - String: magyar indoklás
- `irrigation/scheduler/temperature` - Float: jelenlegi hőmérséklet
- `irrigation/scheduler/soil_deficit` - Float: talaj hiány mm
- `irrigation/scheduler/rain_forecast` - Float: várható eső mm

## Reason formátum

Az új verzióban a `reason` mező **teljes magyar mondatokat** tartalmaz:

- `"Talaj jól öntözött, többlet: 21.8mm"` - Bő csapadék után nincs szükség öntözésre
- `"Várható eső (15.2mm) fedezi az igényt"` - Közelgő csapadék miatt várjunk
- `"Jelenleg erősen esik az eső (5.2mm/h)"` - Aktív csapadék alatt nem öntözünk
- `"Nagy talajnedvesség hiány (18.5mm)"` - Komoly öntözésre van szükség
- `"Mérsékelt hiány + forró idő várható"` - Kombinált tényezők miatt öntözés
- `"Megfelelő talajnedvesség"` - Egyensúly, nincs teendő
- `"API hiba történt az adatok lekérdezésekor"` - Technikai probléma esetén

Ez sokkal informatívabb, mint a korábbi angol kódok (`well_watered`, `recent_heavy_rain`, stb.).

## Példa Home Assistant integráció

```yaml
# configuration.yaml
mqtt:
  sensor:
    # Raw JSON message
    - name: "Garden Irrigation Status"
      state_topic: "irrigation/scheduler/raw"
      value_template: "{{ value_json.watering_required }}"
      json_attributes_topic: "irrigation/scheduler/raw"
    
    # Individual values
    - name: "Garden Watering Required"
      state_topic: "irrigation/scheduler/watering_required"
      
    - name: "Garden Water Amount"
      state_topic: "irrigation/scheduler/water_amount"
      unit_of_measurement: "L/m²"
      
    - name: "Garden Irrigation Reason"
      state_topic: "irrigation/scheduler/reason"

  binary_sensor:
    - name: "Garden Needs Watering"
      state_topic: "irrigation/scheduler/watering_required"
      payload_on: "true"
      payload_off: "false"
```

**Előnyök:**
- 🎯 **Egyszerű értékek**: Külön topic-okban könnyebb feldolgozni
- 🏠 **Home Assistant**: Minden érték külön szenzorként használható
- 🔧 **Automatizálás**: Könnyebb triggerek (pl. csak `watering_required` változásra)
- 📊 **Monitorozás**: Külön-külön figyelhetők az értékek

## Automatizálás

### Cron job (óránkénti ellenőrzés):
```bash
# crontab -e
0 * * * * cd /path/to/project && python3 mqtt_simple.py >> mqtt.log 2>&1
```

### Systemd timer:
```ini
# /etc/systemd/system/irrigation-mqtt.service
[Unit]
Description=Irrigation MQTT Publisher

[Service]
Type=oneshot
WorkingDirectory=/path/to/project
ExecStart=/usr/bin/python3 mqtt_simple.py
User=your_user

# /etc/systemd/system/irrigation-mqtt.timer  
[Unit]
Description=Run irrigation MQTT publisher every hour

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

## Hibaelhárítás

### Connection refused:
- Ellenőrizd, hogy fut-e az MQTT broker
- Ellenőrizd a broker címét és portját az `mqtt_config.py`-ban

### Import error:
```bash
pip install paho-mqtt
```

### Tesztelés mosquitto-val:
```bash
# Broker indítása
mosquitto -v

# Üzenetek figyelése másik terminálban  
mosquitto_sub -t "garden/irrigation/#" -v
```
