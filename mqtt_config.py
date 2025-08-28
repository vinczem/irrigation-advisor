#!/usr/bin/env python3
"""
MQTT Config fájl - Itt állítsd be az MQTT beállításokat
"""

# MQTT Broker beállítások
MQTT_BROKER = "192.168.0.98"  # Pl: "192.168.1.100" vagy "broker.hivemq.com"
MQTT_PORT = 2883
MQTT_CLIENT_ID = "irrigation_advisor"

# Ha szükséges authentication:
MQTT_USERNAME = None  # "your_username"
MQTT_PASSWORD = None  # "your_password"

# Topic struktura
MQTT_TOPIC_BASE = "irrigation/scheduler"  # Base topic

# Topic mapping
MQTT_TOPICS = {
    "raw": f"{MQTT_TOPIC_BASE}/raw",                 # Teljes JSON üzenet
    "status": f"{MQTT_TOPIC_BASE}/status",           # Részletes státusz JSON (mqtt_publisher.py)
    "watering_required": f"{MQTT_TOPIC_BASE}/watering_required", # Boolean: kell-e öntözni
    "water_amount": f"{MQTT_TOPIC_BASE}/water_amount",      # Float: liter/m²  
    "reason": f"{MQTT_TOPIC_BASE}/reason",           # String: magyar indoklás
    "temperature": f"{MQTT_TOPIC_BASE}/temperature", # Float: jelenlegi hőmérséklet
    "deficit": f"{MQTT_TOPIC_BASE}/soil_deficit",    # Float: talaj hiány mm
    "rain_forecast": f"{MQTT_TOPIC_BASE}/rain_forecast" # Float: várható eső mm
}

# Message options
MQTT_QOS = 1        # Quality of Service
MQTT_RETAIN = True  # Retain messages
