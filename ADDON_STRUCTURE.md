# Home Assistant Addon - Irrigation Advisor

## Addon felépítés

```
irrigation-advisor/
├── config.yaml           # Addon konfiguráció
├── Dockerfile            # Docker image
├── rootfs/               # Addon fájlok
│   └── usr/bin/
│       ├── irrigation_advisor.py
│       ├── irrigation_cli.py
│       ├── mqtt_simple.py
│       └── irrigation_state.py
├── data/                 # Perzisztens adatok
│   ├── irrigation_state.json
│   └── options.json
└── README.md
```

## config.yaml (Addon konfiguráció)

```yaml
name: "Irrigation Advisor"
description: "Intelligent lawn irrigation advisor"
version: "1.0.0"
slug: "irrigation_advisor"
init: false
arch:
  - amd64
  - aarch64
  - armhf
  - armv7
  - i386
map:
  - "share:rw"           # /share mapped
  - "config:ro"          # /config mapped (read-only)
options:
  api_key: ""
  latitude: 46.65
  longitude: 20.14
  mqtt_broker: "core-mosquitto"
  mqtt_port: 1883
  update_interval: 60
schema:
  api_key: str
  latitude: float
  longitude: float
  mqtt_broker: str
  mqtt_port: int
  update_interval: int(1,1440)
services:
  - mqtt:need
ports:
  8080/tcp: null
environment:
  LOG_LEVEL: info
```

## Dockerfile

```dockerfile
FROM python:3.11-alpine

# Install dependencies
RUN apk add --no-cache \
    gcc \
    musl-dev \
    && pip install --no-cache-dir \
    paho-mqtt \
    requests

# Copy addon files
COPY rootfs /

# Set permissions
RUN chmod a+x /usr/bin/irrigation_*

# Create data directory
RUN mkdir -p /data

WORKDIR /usr/bin

CMD ["/usr/bin/run.sh"]
```
