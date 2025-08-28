FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    jq \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip install --no-cache-dir \
    requests \
    paho-mqtt

COPY rootfs /

RUN chmod +x /run.sh
RUN find /usr/bin -name "*.py" -exec chmod +x {} \;

RUN mkdir -p /data

WORKDIR /usr/bin

LABEL \
    io.hass.name="Irrigation Advisor" \
    io.hass.description="Intelligent lawn irrigation advisor with weather data" \
    io.hass.arch="aarch64|amd64|armhf|armv7|i386" \
    io.hass.type="addon" \
    maintainer="Mihaly Vincze <g889ln@gmail.com>" \
    org.opencontainers.image.title="Irrigation Advisor" \
    org.opencontainers.image.description="Weather-based irrigation decision system" \
    org.opencontainers.image.source="https://github.com/vinczem/irrigation-advisor" \
    org.opencontainers.image.licenses="MIT"

HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8099/health || exit 1

CMD ["/run.sh"]
