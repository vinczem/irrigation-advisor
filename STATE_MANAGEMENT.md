# 🔄 Öntözési Nyilvántartás és State Management

## Probléma

A rendszer MQTT-n keresztül javaslatot ad az öntözésre, de nem tudja, hogy a Home Assistant végrehajtotta-e azt. Ez vezethet:
- ✅ **Dupla öntözéshez** (rövid időn belül többször)
- ❌ **Felesleges javaslatokhoz** friss öntözés után
- 📊 **Hiányzó statisztikákhoz**

## Megoldási Alternatívák

### 🥇 **1. Egyszerű Fájl Alapú (Implementált)**

**Fájlok:**
- `irrigation_state.py` - State management osztály
- `irrigation_cli.py` - Parancssori eszközök
- `mqtt_simple.py` - Integrált MQTT publisher

**Működés:**
```bash
# Javaslat küldése (automatikus state logging)
python3 mqtt_simple.py

# Home Assistant öntözés után (manuális)  
python3 irrigation_cli.py mark 8.0 "Home Assistant automatic"

# Állapot ellenőrzése
python3 irrigation_cli.py status
```

**Előnyök:**
- ✅ Egyszerű, gyors implementáció
- ✅ Nincs külső függőség
- ✅ JSON fájl könnyen szerkeszthető
- ✅ Immediate availability

**Hátrányok:**
- ❌ Manuális beavatkozás szükséges
- ❌ Nincs automatikus feedback
- ❌ Race condition lehetőség

### 🥈 **2. MQTT Feedback Loop (Fejlettebb)**

**Fájlok:**
- `mqtt_feedback.py` - MQTT listener service
- `mqtt_enhanced.py` - Enhanced publisher SQLite adatbázissal

**Működés:**
```bash
# Feedback listener indítása (háttérben)
python3 mqtt_feedback.py &

# Home Assistant publikál visszajelzést:
# Topic: irrigation/scheduler/executed
# Payload: {"actual_amount": 8.0, "timestamp": "2025-08-25T16:00:00"}
```

**Előnyök:**
- ✅ Teljes automatizálás
- ✅ Valós idejű feedback
- ✅ SQLite adatbázis
- ✅ Skálázható megoldás

**Hátrányok:**
- ❌ Komplexebb setup
- ❌ MQTT broker dependency
- ❌ Home Assistant konfiguráció szükséges

### 🥉 **3. Hibrid Megoldás (Ajánlott produkciós használatra)**

Kombinálja mindkét megközelítést:
- **Alap**: Fájl alapú state management
- **Opcionális**: MQTT feedback ha elérhető

## Implementált Funkciók

### 📊 **State Tracking**
```python
from irrigation_state import SimpleIrrigationState

state = SimpleIrrigationState()
state.log_recommendation(8.0, "Moderate irrigation needed")
state.mark_executed(8.0, "Home Assistant automatic")
```

### 🛡️ **Duplicate Prevention**
```python
# Automatikus filtering az mqtt_simple.py-ban
should_skip, amount = state.should_skip_recommendation(hours=6)
if should_skip and message['watering_required']:
    message['reason'] = f"Frissen öntözve ({amount}L/m²), átmenetileg kihagyva"
```

### 🔧 **CLI Management**
```bash
# Állapot
python3 irrigation_cli.py status

# Öntözés rögzítése  
python3 irrigation_cli.py mark 10.5

# Megjegyzéssel
python3 irrigation_cli.py mark 8.0 'Manual evening watering'

# Reset
python3 irrigation_cli.py clear
```

## Gyakorlati Workflow

### 📅 **Napi Rutin**
1. **Cron job** futtatja `python3 mqtt_simple.py` óránként
2. **Home Assistant** megkapja a javaslat MQTT üzenetben  
3. **Ha öntöz**: `python3 irrigation_cli.py mark <mennyiség>`
4. **Következő futás**: State filter megakadályozza a dupla öntözést

### 🏠 **Home Assistant Automatizálás**
```yaml
# Home Assistant automation
automation:
  - alias: "Mark Irrigation Executed"
    trigger:
      platform: state
      entity_id: switch.irrigation_valve
      from: "off" 
      to: "on"
    action:
      - service: shell_command.mark_irrigation
        data:
          amount: "{{ states('sensor.irrigation_amount') }}"

shell_command:
  mark_irrigation: 'python3 /path/to/irrigation_cli.py mark {{ amount }} "Home Assistant automatic"'
```

### 📈 **Monitoring & Statistics**
```bash
# Napi ellenőrzés
python3 irrigation_cli.py status

# Legutóbbi öntözések
python3 -c "from irrigation_state import SimpleIrrigationState; s=SimpleIrrigationState(); print(s.get_recent_irrigation(72))"
```

## Fájl Struktúra

```
irrigation_state.json:
{
  "last_recommendation": {
    "timestamp": "2025-08-25T16:04:36",
    "amount_lpm2": 8.0,
    "reason": "Megfelelő talajnedvesség", 
    "executed": true,
    "execution_time": "2025-08-25T16:05:12",
    "execution_amount": 8.0
  },
  "irrigation_log": [...],
  "version": "1.0"
}
```

## Következő Lépések

1. **✅ Fájl alapú rendszer tesztelése**
2. **🔄 Home Assistant integráció finomhangolása**  
3. **📊 Reporting és statisztikák fejlesztése**
4. **🔮 MQTT feedback implementálása (opcionális)**
