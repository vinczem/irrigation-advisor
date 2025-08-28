# Home Assistant OS 2025 - Irrigation Advisor Integration

## 1. MQTT Sensors (configuration.yaml)

```yaml
# MQTT Configuration for Home Assistant OS 2025
mqtt:
  sensor:
    # Raw irrigation recommendation with modern attributes
    - name: "Irrigation Recommendation"
      unique_id: "irrigation_recommendation_raw"
      state_topic: "irrigation/scheduler/raw"
      value_template: "{{ value_json.watering_required | default('unknown') }}"
      json_attributes_topic: "irrigation/scheduler/raw"
      icon: mdi:sprinkler-variant
      device_class: enum
      availability_topic: "irrigation/scheduler/status"
      availability_template: "{{ 'online' if value else 'offline' }}"
      
    # Individual sensor values
    - name: "Irrigation Required"
      unique_id: "irrigation_required"
      state_topic: "irrigation/scheduler/watering_required"
      icon: mdi:water-pump
      device_class: enum
      
    - name: "Water Amount"
      unique_id: "irrigation_water_amount"
      state_topic: "irrigation/scheduler/water_amount"
      unit_of_measurement: "L/m²"
      icon: mdi:water
      device_class: volume
      state_class: measurement
      
    - name: "Irrigation Reason"
      unique_id: "irrigation_reason"
      state_topic: "irrigation/scheduler/reason"
      icon: mdi:information-outline
      
    # Additional weather context sensors
    - name: "Soil Deficit"
      unique_id: "irrigation_soil_deficit"  
      state_topic: "irrigation/scheduler/soil_deficit"
      unit_of_measurement: "mm"
      icon: mdi:water-minus
      device_class: precipitation
      state_class: measurement
      
    - name: "Rain Forecast"
      unique_id: "irrigation_rain_forecast"
      state_topic: "irrigation/scheduler/rain_forecast"
      unit_of_measurement: "mm"
      icon: mdi:weather-rainy
      device_class: precipitation
      state_class: measurement
      
    - name: "Current Temperature"
      unique_id: "irrigation_temperature"
      state_topic: "irrigation/scheduler/temperature"
      unit_of_measurement: "°C"
      icon: mdi:thermometer
      device_class: temperature
      state_class: measurement
      
    # System status
    - name: "Irrigation Service Status"
      unique_id: "irrigation_service_status"
      state_topic: "irrigation/scheduler/addon_status"
      value_template: "{{ value_json.pending_count | default(0) }}"
      json_attributes_topic: "irrigation/scheduler/addon_status"
      unit_of_measurement: "pending"
      icon: mdi:cog

  # Binary sensors with modern configuration
  binary_sensor:
    - name: "Garden Needs Watering"
      unique_id: "garden_needs_watering"
      state_topic: "irrigation/scheduler/watering_required"
      payload_on: "true"
      payload_off: "false"
      device_class: problem
      icon: mdi:sprinkler

  # MQTT Device Registry (HA OS 2025 feature)
  device:
    identifiers: ["irrigation_advisor_addon"]
    name: "Irrigation Advisor"
    model: "Weather-based Irrigation System"
    manufacturer: "Home Assistant Community"
    sw_version: "2.0.0"
```

## 2. Modern Automations (Home Assistant OS 2025)

```yaml
# Modern automation configuration
automation:
  # Scheduled irrigation checks with advanced triggers
  - id: "irrigation_daily_schedule"
    alias: "Daily Irrigation Assessment"
    description: "Automated daily irrigation recommendations"
    
    trigger:
      # Multiple time-based triggers
      - platform: time
        at: "06:00:00"  # Morning check
        id: "morning_check"
      - platform: time  
        at: "18:00:00"  # Evening check
        id: "evening_check"
      # Sun-based triggers (HA OS 2025 enhancement)
      - platform: sun
        event: sunrise
        offset: "+01:00:00"  # 1 hour after sunrise
        id: "post_sunrise"
        
    condition:
      # Advanced conditions
      - condition: state
        entity_id: input_boolean.irrigation_system_enabled
        state: "on"
      - condition: not
        conditions:
          - condition: state
            entity_id: binary_sensor.rain_detected
            state: "on"
    
    action:
      # Modern action with variables
      - variables:
          trigger_source: "{{ trigger.id }}"
          current_temp: "{{ states('sensor.outdoor_temperature') | float(0) }}"
          
      - service: shell_command.irrigation_check
        data:
          source: "{{ trigger_source }}"
          
      # Enhanced logging with context
      - service: logbook.log
        data:
          name: "Irrigation System"
          message: >
            Irrigation check triggered by {{ trigger_source }} 
            (Temp: {{ current_temp }}°C)
          entity_id: binary_sensor.garden_needs_watering

  # Weather-responsive irrigation checks
  - id: "irrigation_weather_response"
    alias: "Weather-Responsive Irrigation"
    description: "Adjust irrigation based on weather changes"
    mode: queued  # HA OS 2025 mode setting
    max: 5
    
    trigger:
      # Advanced weather triggers
      - platform: numeric_state
        entity_id: 
          - sensor.openweathermap_forecast_precipitation
          - sensor.weather_precipitation_forecast
        above: 3
        for: "00:15:00"  # Sustained forecast
        id: "rain_forecast"
        
      - platform: numeric_state
        entity_id: sensor.outdoor_temperature
        above: 32
        for: "01:00:00"  # Hot weather sustained
        id: "heat_wave"
        
      - platform: numeric_state
        entity_id: sensor.wind_speed
        above: 25  # High wind (affects irrigation efficiency)
        id: "windy_conditions"
        
    condition:
      # Time-based conditions
      - condition: time
        after: "05:00:00"
        before: "22:00:00"
        
    action:
      - choose:
          # Rain forecast response
          - conditions:
              - condition: trigger
                id: "rain_forecast"
            sequence:
              - service: shell_command.irrigation_check
              - service: notify.persistent_notification
                data:
                  title: "🌧️ Irrigation Update"
                  message: >
                    Rain forecast detected ({{ trigger.to_state.state }}mm).
                    Irrigation recommendation updated.
                  notification_id: "irrigation_rain_update"
                  
          # Heat wave response  
          - conditions:
              - condition: trigger
                id: "heat_wave"
            sequence:
              - service: shell_command.irrigation_check
              - service: notify.mobile_app_your_phone
                data:
                  title: "🔥 Heat Alert"
                  message: >
                    High temperature detected ({{ trigger.to_state.state }}°C).
                    Check irrigation recommendations.
                  data:
                    priority: high
                    tag: "irrigation_heat"

  # Smart irrigation execution with conditions
  - id: "irrigation_smart_execution"
    alias: "Smart Irrigation Execution"
    description: "Execute irrigation with advanced logic"
    mode: single
    
    trigger:
      - platform: state
        entity_id: binary_sensor.garden_needs_watering
        to: "on"
        for: "00:05:00"  # Prevent false triggers
        
    condition:
      # Advanced execution conditions
      - condition: and
        conditions:
          - condition: state
            entity_id: input_boolean.irrigation_auto_mode
            state: "on"
          - condition: time
            after: "05:30:00"
            before: "09:00:00"  # Optimal irrigation window
          - condition: numeric_state
            entity_id: sensor.water_amount
            above: 2  # Minimum threshold
          - condition: template
            value_template: >
              {{ (as_timestamp(now()) - as_timestamp(states.automation.irrigation_smart_execution.attributes.last_triggered | default(0))) > 21600 }}
            # Prevent multiple executions within 6 hours
    
    action:
      - variables:
          water_amount: "{{ states('sensor.water_amount') | float(0) }}"
          irrigation_duration: "{{ (water_amount * 45) | int }}"  # 45 sec per L/m²
          
      # Pre-irrigation checks
      - service: switch.turn_on
        entity_id: switch.irrigation_pump
        
      - delay: "00:00:05"  # Pump startup delay
      
      # Main irrigation sequence
      - service: switch.turn_on
        entity_id: switch.irrigation_valve
        
      - delay: "{{ irrigation_duration }}"
      
      # Shutdown sequence
      - service: switch.turn_off
        entity_id: switch.irrigation_valve
        
      - delay: "00:00:10"  # Drain time
      
      - service: switch.turn_off
        entity_id: switch.irrigation_pump
        
      # Log execution to addon
      - service: mqtt.publish
        data:
          topic: "irrigation/scheduler/execute"
          retain: false
          payload: >
            {
              "executed": true,
              "amount": {{ water_amount }},
              "duration_seconds": {{ irrigation_duration }},
              "notes": "HA OS 2025 automatic execution",
              "timestamp": "{{ now().isoformat() }}",
              "weather_temp": "{{ states('sensor.outdoor_temperature') }}",
              "soil_deficit": "{{ states('sensor.soil_deficit') }}"
            }
            
      # Modern notification with rich data
      - service: notify.mobile_app_your_phone
        data:
          title: "💧 Irrigation Complete"
          message: >
            Garden irrigated with {{ water_amount }}L/m² 
            ({{ irrigation_duration }}s duration)
          data:
            tag: "irrigation_complete"
            group: "irrigation"
            actions:
              - action: "VIEW_GARDEN_CAM"
                title: "View Garden Camera"
              - action: "IRRIGATION_STATUS" 
                title: "Check Status"
```

## 3. Modern Dashboard (HA OS 2025 Lovelace)

```yaml
# Modern card configuration with new HA OS 2025 features
type: custom:layout-card
layout_type: grid
layout_options:
  grid-template-columns: 1fr 1fr
  grid-template-rows: auto
  gap: 16px
cards:
  # Primary Status Card with new tile design
  - type: tile
    entity: binary_sensor.garden_needs_watering
    name: Garden Irrigation Status
    icon: mdi:sprinkler
    color: primary
    show_entity_picture: false
    tap_action:
      action: more-info
    features:
      - type: irrigation-status
        
  # Weather-aware Irrigation Card
  - type: custom:mushroom-chips-card
    chips:
      - type: entity
        entity: sensor.water_amount
        content_info: state
        use_entity_picture: false
        icon_color: blue
        tap_action:
          action: more-info
          
      - type: entity
        entity: sensor.soil_deficit
        content_info: state
        icon_color: brown
        
      - type: entity
        entity: sensor.rain_forecast
        content_info: state
        icon_color: light-blue

  # Modern Action Buttons
  - type: horizontal-stack
    cards:
      - type: custom:mushroom-entity-card
        entity: script.refresh_irrigation_forecast
        name: Update Forecast
        icon: mdi:refresh
        layout: vertical
        primary_info: name
        secondary_info: none
        tap_action:
          action: call-service
          service: script.refresh_irrigation_forecast
        card_mod:
          style: |
            ha-card {
              --ha-card-background: var(--green-color);
            }
            
      - type: conditional
        conditions:
          - entity: binary_sensor.garden_needs_watering
            state: "on"
        card:
          type: custom:mushroom-entity-card
          entity: script.execute_irrigation
          name: Execute Now
          icon: mdi:play-circle
          layout: vertical
          tap_action:
            action: call-service
            service: script.execute_irrigation
          card_mod:
            style: |
              ha-card {
                --ha-card-background: var(--blue-color);
                animation: pulse 2s infinite;
              }

  # Enhanced Weather Context (spanning full width)
  - type: custom:weather-card
    entity: weather.openweathermap
    name: Irrigation Weather Context
    forecast: true
    details: true
    hourly_forecast: true
    animated_icons: true
    grid-column: 1 / -1
    
  # Advanced System Information
  - type: entities
    title: System Information
    entities:
      - entity: sensor.irrigation_service_status
        name: Pending Recommendations
        icon: mdi:clipboard-list
        
      - type: custom:template-entity-row
        name: Last Update
        state: >
          {{ as_timestamp(states.sensor.irrigation_recommendation.last_updated) 
             | timestamp_custom('%d/%m %H:%M') }}
        icon: mdi:clock-outline
        
      - type: custom:template-entity-row
        name: Next Scheduled Check
        state: >
          {% set now = now() %}
          {% set morning = today_at("06:00") %}
          {% set evening = today_at("18:00") %}
          {% if now < morning %}
            Today 06:00
          {% elif now < evening %}
            Today 18:00  
          {% else %}
            Tomorrow 06:00
          {% endif %}
        icon: mdi:calendar-clock
        
      - entity: input_boolean.irrigation_auto_mode
        name: Automatic Mode
        
  # Manual Control Panel
  - type: entities
    title: Manual Control
    entities:
      - entity: input_number.manual_irrigation_amount
        name: Water Amount (L/m²)
        
      - entity: switch.irrigation_valve
        name: Irrigation Valve
        
      - entity: switch.irrigation_pump  
        name: Irrigation Pump
        
      - type: custom:mushroom-entity-card
        entity: script.manual_irrigation
        name: Start Manual Irrigation
        icon: mdi:sprinkler-variant
        layout: horizontal
        tap_action:
          action: call-service
          service: script.manual_irrigation
          service_data:
            amount: "{{ states('input_number.manual_irrigation_amount') }}"

  # Rich Information Card with Charts
  - type: custom:apexcharts-card
    header:
      show: true
      title: Irrigation Analytics (7 days)
    graph_span: 7d
    series:
      - entity: sensor.water_amount
        name: Daily Recommendation
        type: column
        group_by:
          func: max
          duration: 1d
          
      - entity: sensor.soil_deficit
        name: Soil Deficit
        type: line
        yaxis_id: deficit
        
      - entity: sensor.rain_forecast
        name: Rain Forecast
        type: area
        yaxis_id: rain
    yaxis:
      - id: water
        min: 0
        max: 25
      - id: deficit
        opposite: true
        min: 0
      - id: rain
        opposite: true
        min: 0
        
  # System Status & Debug
  - type: markdown
    content: |
      ### 🌱 Irrigation System Status
      
      **Current Status:** {{ states('binary_sensor.garden_needs_watering') | title }}
      **Reason:** {{ states('sensor.irrigation_reason') }}
      
      **Weather Context:**
      - 🌡️ Temperature: {{ states('sensor.current_temperature') }}°C  
      - 🌧️ Rain Forecast: {{ states('sensor.rain_forecast') }}mm
      - 💧 Soil Deficit: {{ states('sensor.soil_deficit') }}mm
      
      **System Health:**
      - 📡 MQTT: {{ 'Connected' if states('sensor.irrigation_service_status') != 'unavailable' else 'Disconnected' }}
      - ⏱️ Last Check: {{ as_timestamp(states.sensor.irrigation_recommendation.last_updated) | timestamp_custom('%H:%M') }}
      - 🔄 Auto Mode: {{ states('input_boolean.irrigation_auto_mode') | title }}
      
      {% if states('binary_sensor.garden_needs_watering') == 'on' %}
      **💧 Irrigation Needed:** {{ states('sensor.water_amount') }}L/m²
      {% endif %}
```

## 4. Modern Input Helpers & Configuration

```yaml
# Modern input helpers for HA OS 2025
input_number:
  manual_irrigation_amount:
    name: "Manual Irrigation Amount"
    min: 0
    max: 50
    step: 0.5
    unit_of_measurement: "L/m²"
    icon: mdi:water
    mode: slider  # HA OS 2025 modern slider
    
  irrigation_flow_rate:
    name: "Irrigation Flow Rate"
    min: 0.5
    max: 10.0
    step: 0.1
    unit_of_measurement: "L/min/m²"
    icon: mdi:water-pump
    mode: box

input_boolean:
  irrigation_system_enabled:
    name: "Irrigation System Enabled"
    icon: mdi:power
    
  irrigation_auto_mode:
    name: "Automatic Irrigation"
    icon: mdi:auto-mode
    
  irrigation_notifications:
    name: "Irrigation Notifications"
    icon: mdi:bell-ring
    
  irrigation_weather_hold:
    name: "Weather Hold (Manual Override)"
    icon: mdi:weather-rainy-off

input_datetime:
  last_irrigation:
    name: "Last Irrigation Time"
    has_date: true
    has_time: true
    icon: mdi:calendar-clock
    
  next_scheduled_irrigation:
    name: "Next Scheduled Check"
    has_date: true
    has_time: true
    icon: mdi:calendar-arrow-right

input_select:
  irrigation_mode:
    name: "Irrigation Mode"
    options:
      - "Automatic"
      - "Semi-Automatic" 
      - "Manual Only"
      - "Weather Override"
      - "Maintenance Mode"
    initial: "Automatic"
    icon: mdi:cog-outline
    
  irrigation_season:
    name: "Irrigation Season Profile"
    options:
      - "Spring (Moderate)"
      - "Summer (Intensive)"
      - "Autumn (Reduced)"
      - "Winter (Minimal)"
    initial: "Summer (Intensive)"
    icon: mdi:weather-sunny

# Modern counter for tracking
counter:
  daily_irrigation_count:
    name: "Daily Irrigation Count"
    initial: 0
    step: 1
    icon: mdi:counter
    
  weekly_irrigation_amount:
    name: "Weekly Water Usage"
    initial: 0
    step: 1
    icon: mdi:water-percent

# Template sensors for advanced logic
template:
  sensor:
    - name: "Irrigation Efficiency Score"
      unique_id: "irrigation_efficiency_score"
      state: >
        {% set executed = states('counter.daily_irrigation_count') | int %}
        {% set recommended = states('sensor.irrigation_service_status') | int %}
        {% if recommended > 0 %}
          {{ ((executed / recommended) * 100) | round(1) }}
        {% else %}
          100
        {% endif %}
      unit_of_measurement: "%"
      icon: mdi:chart-line
      
    - name: "Next Irrigation Window"
      unique_id: "next_irrigation_window"
      state: >
        {% set now = now() %}
        {% set morning = today_at("06:00") %}
        {% set evening = today_at("18:00") %}
        {% if now.hour < 6 %}
          Today 06:00-09:00
        {% elif now.hour < 18 %}
          Today 18:00-21:00
        {% else %}
          Tomorrow 06:00-09:00
        {% endif %}
      icon: mdi:clock-time-four
      
    - name: "Weather Irrigation Risk"
      unique_id: "weather_irrigation_risk"
      state: >
        {% set temp = states('sensor.current_temperature') | float(20) %}
        {% set rain = states('sensor.rain_forecast') | float(0) %}
        {% set wind = states('sensor.wind_speed') | float(0) %}
        
        {% if rain > 5 %}
          Low (Rain Expected)
        {% elif temp > 35 or wind > 30 %}
          High (Extreme Conditions)
        {% elif temp > 30 %}
          Medium (Hot Weather)
        {% else %}
          Low (Good Conditions)
        {% endif %}
      icon: mdi:alert-circle-outline

  binary_sensor:
    - name: "Irrigation Time Window"
      unique_id: "irrigation_time_window"
      state: >
        {% set now = now() %}
        {{ (now.hour >= 5 and now.hour <= 9) or (now.hour >= 17 and now.hour <= 21) }}
      device_class: window
      
    - name: "Weather Suitable for Irrigation"
      unique_id: "weather_suitable_irrigation"
      state: >
        {% set temp = states('sensor.current_temperature') | float(20) %}
        {% set rain = states('binary_sensor.rain_detected') %}
        {% set wind = states('sensor.wind_speed') | float(0) %}
        {{ temp < 35 and rain == 'off' and wind < 25 }}
      device_class: safety
```

## 5. Shell Commands & Services (HA OS 2025)

```yaml
# Modern shell commands with enhanced error handling
shell_command:
  # Primary irrigation commands
  irrigation_check: >
    timeout 30 docker exec addon_local_irrigation_advisor_simple 
    python3 /usr/bin/mqtt_simple.py
    
  irrigation_force_update: >
    timeout 30 docker exec addon_local_irrigation_advisor_simple 
    python3 /usr/bin/mqtt_simple.py --force
  
  # System management commands
  debug_irrigation_config: >
    timeout 15 docker exec addon_local_irrigation_advisor_simple 
    python3 /usr/bin/debug_config.py
    
  irrigation_system_status: >
    timeout 15 docker exec addon_local_irrigation_advisor_simple 
    python3 /usr/bin/irrigation_cli.py status
    
  irrigation_clear_state: >
    timeout 15 docker exec addon_local_irrigation_advisor_simple 
    python3 /usr/bin/irrigation_cli.py clear
    
  irrigation_mark_executed: >
    timeout 15 docker exec addon_local_irrigation_advisor_simple 
    python3 /usr/bin/irrigation_cli.py mark
  
  # Container management
  restart_irrigation_addon: >
    docker restart addon_local_irrigation_advisor_simple
    
  irrigation_addon_logs: >
    docker logs --tail 50 addon_local_irrigation_advisor_simple

# Modern REST commands for direct API access
rest_command:
  # Health check endpoint
  irrigation_health_check:
    url: "http://addon-irrigation-advisor:8099/health"
    method: GET
    timeout: 10
    
  # Advanced irrigation execution logging
  log_irrigation_execution:
    url: "http://addon-irrigation-advisor:8080/api/execute"
    method: POST
    headers:
      content-type: "application/json"
      authorization: "Bearer {{ states('input_text.addon_api_token') }}"
    payload: >
      {
        "executed": true,
        "amount": {{ amount | default(0) }},
        "duration_seconds": {{ duration | default(0) }},
        "method": "{{ method | default('automatic') }}",
        "weather_conditions": {
          "temperature": {{ states('sensor.current_temperature') | float(0) }},
          "humidity": {{ states('sensor.humidity') | float(0) }},
          "wind_speed": {{ states('sensor.wind_speed') | float(0) }},
          "pressure": {{ states('sensor.pressure') | float(0) }}
        },
        "soil_conditions": {
          "deficit": {{ states('sensor.soil_deficit') | float(0) }},
          "moisture": {{ states('sensor.soil_moisture_percent') | float(0) }}
        },
        "timestamp": "{{ now().isoformat() }}",
        "notes": "{{ notes | default('HA OS 2025 execution') }}"
      }
    verify_ssl: true
```

## 6. Advanced Scripts & Sequences (HA OS 2025)

```yaml
# Modern script configuration with enhanced features
script:
  # Smart irrigation forecast refresh
  refresh_irrigation_forecast:
    alias: "🔄 Refresh Irrigation Forecast"
    description: "Update irrigation recommendations with current weather data"
    icon: mdi:refresh-circle
    mode: single
    max_exceeded: silent
    
    variables:
      notification_enabled: "{{ states('input_boolean.irrigation_notifications') }}"
      
    sequence:
      # Pre-check conditions
      - condition: state
        entity_id: input_boolean.irrigation_system_enabled
        state: "on"
        
      # Execute update with timeout
      - timeout: "00:01:00"
        service: shell_command.irrigation_check
        
      # Wait for MQTT response
      - wait_template: >
          {{ as_timestamp(now()) - as_timestamp(states.sensor.irrigation_recommendation.last_updated) < 30 }}
        timeout: "00:00:30"
        
      # Conditional notification
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ notification_enabled == 'on' }}"
            sequence:
              - service: notify.persistent_notification
                data:
                  title: "🌱 Irrigation Forecast Updated"
                  message: >
                    Recommendation: {{ states('sensor.irrigation_reason') }}
                    {% if states('binary_sensor.garden_needs_watering') == 'on' %}
                    💧 Water needed: {{ states('sensor.water_amount') }}L/m²
                    {% else %}
                    ✅ No irrigation needed
                    {% endif %}
                  notification_id: "irrigation_forecast_update"

  # Intelligent irrigation execution
  execute_smart_irrigation:
    alias: "💧 Execute Smart Irrigation"
    description: "Execute irrigation with intelligent duration and monitoring"
    icon: mdi:sprinkler
    mode: single
    
    fields:
      override_amount:
        description: "Override recommended amount (L/m²)"
        example: "8.5"
        default: null
        selector:
          number:
            min: 0
            max: 50
            step: 0.5
            unit_of_measurement: "L/m²"
    
    variables:
      water_amount: >
        {{ override_amount | default(states('sensor.water_amount') | float(0)) }}
      flow_rate: "{{ states('input_number.irrigation_flow_rate') | float(2.0) }}"
      irrigation_duration: "{{ ((water_amount / flow_rate) * 60) | int }}"
      max_duration: 1800  # 30 minutes safety limit
      actual_duration: "{{ [irrigation_duration, max_duration] | min }}"
      
    sequence:
      # Safety checks
      - condition: and
        conditions:
          - condition: state
            entity_id: input_boolean.irrigation_system_enabled
            state: "on"
          - condition: template
            value_template: "{{ water_amount > 0 }}"
          - condition: state
            entity_id: binary_sensor.weather_suitable_irrigation
            state: "on"
            
      # Pre-irrigation setup
      - service: counter.increment
        entity_id: counter.daily_irrigation_count
        
      - service: input_datetime.set_datetime
        entity_id: input_datetime.last_irrigation
        data:
          timestamp: "{{ now().timestamp() }}"
          
      # Irrigation sequence with monitoring
      - parallel:
          # Main irrigation control
          - sequence:
              # Start pump system
              - service: switch.turn_on
                entity_id: switch.irrigation_pump
                
              - delay: "00:00:05"  # Pump startup
              
              # Open irrigation valves
              - service: switch.turn_on
                entity_id: 
                  - switch.irrigation_valve_zone_1
                  - switch.irrigation_valve_zone_2
                
              # Main irrigation duration
              - delay: "{{ actual_duration }}"
              
              # Shutdown sequence
              - service: switch.turn_off
                entity_id:
                  - switch.irrigation_valve_zone_1 
                  - switch.irrigation_valve_zone_2
                  
              - delay: "00:00:10"  # Drain time
              
              - service: switch.turn_off
                entity_id: switch.irrigation_pump
                
          # Monitoring sequence
          - sequence:
              - repeat:
                  while:
                    - condition: state
                      entity_id: switch.irrigation_pump
                      state: "on"
                  sequence:
                    - delay: "00:00:30"
                    # Log system status every 30 seconds
                    - service: logbook.log
                      data:
                        name: "Irrigation Monitor"
                        message: >
                          Irrigation active - Pressure: {{ states('sensor.water_pressure') }}bar,
                          Flow: {{ states('sensor.water_flow_rate') }}L/min
                        entity_id: switch.irrigation_pump
      
      # Post-irrigation logging
      - service: mqtt.publish
        data:
          topic: "irrigation/scheduler/execute"
          retain: false
          payload: >
            {
              "executed": true,
              "amount": {{ water_amount }},
              "planned_duration": {{ irrigation_duration }},
              "actual_duration": {{ actual_duration }},
              "flow_rate": {{ flow_rate }},
              "method": "smart_execution",
              "override_used": {{ override_amount is not none }},
              "weather_temp": {{ states('sensor.current_temperature') | float(0) }},
              "soil_deficit_before": {{ states('sensor.soil_deficit') | float(0) }},
              "timestamp": "{{ now().isoformat() }}",
              "notes": "HA OS 2025 smart irrigation execution"
            }
            
      # Success notification with rich data
      - service: notify.mobile_app_your_phone
        data:
          title: "💧 Smart Irrigation Complete"
          message: >
            Garden irrigated: {{ water_amount }}L/m² 
            Duration: {{ actual_duration // 60 }}m {{ actual_duration % 60 }}s
          data:
            tag: "irrigation_complete"
            group: "irrigation"
            icon: "mdi:sprinkler"
            color: "green"
            actions:
              - action: "VIEW_GARDEN"
                title: "View Garden"
              - action: "IRRIGATION_STATS"
                title: "View Stats"
            image: "/local/images/garden_irrigation.jpg"

  # Manual irrigation with confirmation
  manual_irrigation_with_confirmation:
    alias: "🚿 Manual Irrigation (Confirmed)"
    description: "Manual irrigation with user confirmation dialog"
    icon: mdi:sprinkler-variant
    mode: single
    
    fields:
      amount:
        description: "Water amount in L/m²"
        example: "10.5"
        required: true
        selector:
          number:
            min: 1
            max: 30
            step: 0.5
            unit_of_measurement: "L/m²"
      confirmation_required:
        description: "Require user confirmation"
        default: true
        selector:
          boolean:
    
    sequence:
      # Optional confirmation step
      - choose:
          - conditions:
              - condition: template
                value_template: "{{ confirmation_required | default(true) }}"
            sequence:
              - service: notify.mobile_app_your_phone
                data:
                  title: "Manual Irrigation Confirmation"
                  message: >
                    Confirm manual irrigation of {{ amount }}L/m²?
                    Current recommendation: {{ states('sensor.irrigation_reason') }}
                  data:
                    tag: "irrigation_confirm"
                    actions:
                      - action: "CONFIRM_IRRIGATION"
                        title: "✅ Confirm"
                      - action: "CANCEL_IRRIGATION" 
                        title: "❌ Cancel"
                        
              # Wait for confirmation
              - wait_for_trigger:
                  - platform: event
                    event_type: mobile_app_notification_action
                    event_data:
                      action: "CONFIRM_IRRIGATION"
                timeout: "00:05:00"
                
              - condition: template
                value_template: "{{ wait.trigger is not none }}"
                
      # Execute manual irrigation
      - service: script.execute_smart_irrigation
        data:
          override_amount: "{{ amount }}"
          
      # Log manual execution
      - service: logbook.log
        data:
          name: "Manual Irrigation"
          message: "User executed manual irrigation: {{ amount }}L/m²"
          entity_id: switch.irrigation_valve_zone_1
```

```yaml
rest_command:
  # Get irrigation status from addon
  irrigation_status:
    url: "http://a0d7b954-irrigation-advisor:8080/status"
    method: GET
## 9. Modern Dashboard Configuration (HA OS 2025)

### Rich Dashboard Cards with Enhanced Features

```yaml
# Complete irrigation dashboard with modern card types
type: vertical-stack
cards:
  # Header card with system status
  - type: custom:mushroom-entity-card
    entity: binary_sensor.garden_needs_watering
    name: "Smart Irrigation System"
    icon_color: |
      {% if is_state('binary_sensor.garden_needs_watering', 'on') %}
        blue
      {% elif is_state('input_boolean.irrigation_system_enabled', 'off') %}
        red
      {% else %}
        green
      {% endif %}
    secondary_info: |
      {% if is_state('binary_sensor.garden_needs_watering', 'on') %}
        💧 {{ states('sensor.water_amount') }}L/m² needed
      {% else %}
        ✅ No irrigation required
      {% endif %}
    tap_action:
      action: more-info
    hold_action:
      action: call-service
      service: script.refresh_irrigation_forecast
      
  # Current conditions overview
  - type: custom:mushroom-chips-card
    chips:
      - type: template
        content: "{{ states('sensor.current_temperature') }}°C"
        icon: mdi:thermometer
        icon_color: |
          {% set temp = states('sensor.current_temperature') | float %}
          {% if temp > 30 %} red
          {% elif temp > 20 %} orange
          {% elif temp > 10 %} green
          {% else %} blue
          {% endif %}
      - type: template
        content: "{{ states('sensor.humidity') }}%"
        icon: mdi:water-percent
        icon_color: blue
      - type: template
        content: "{{ states('sensor.wind_speed') }}km/h"
        icon: mdi:weather-windy
        icon_color: |
          {% if states('sensor.wind_speed') | float > 20 %} red
          {% else %} gray
          {% endif %}
      - type: template
        content: "{{ states('sensor.precipitation_today') }}mm"
        icon: mdi:weather-rainy
        icon_color: |
          {% if states('sensor.precipitation_today') | float > 5 %} blue
          {% else %} gray
          {% endif %}
        
  # Weather forecast mini card
  - type: weather-forecast
    entity: weather.openweathermap
    forecast_type: daily
    show_forecast: true
    
  # Main irrigation recommendation card
  - type: custom:mushroom-template-card
    primary: "{{ states('sensor.irrigation_reason') }}"
    secondary: |
      {% if is_state('binary_sensor.garden_needs_watering', 'on') %}
        Water Amount: {{ states('sensor.water_amount') }}L/m²
        Soil Deficit: {{ states('sensor.soil_deficit') }}mm
        Next Check: {{ state_attr('sensor.next_irrigation_check', 'formatted_time') }}
      {% else %}
        Soil Moisture: {{ states('sensor.soil_moisture_percent') }}%
        Last Updated: {{ as_timestamp(states.sensor.irrigation_recommendation.last_updated) | timestamp_custom('%H:%M') }}
      {% endif %}
    icon: |
      {% if is_state('binary_sensor.garden_needs_watering', 'on') %}
        mdi:sprinkler
      {% else %}
        mdi:leaf
      {% endif %}
    icon_color: |
      {% if is_state('binary_sensor.garden_needs_watering', 'on') %}
        blue
      {% else %}
        green
      {% endif %}
    multiline_secondary: true
    
  # Action buttons row
  - type: custom:mushroom-chips-card
    chips:
      # Refresh forecast
      - type: action
        icon: mdi:refresh
        icon_color: blue
        tap_action:
          action: call-service
          service: script.refresh_irrigation_forecast
          
      # Manual irrigation
      - type: action
        icon: mdi:sprinkler-variant
        icon_color: orange
        tap_action:
          action: call-service
          service: script.manual_irrigation_with_confirmation
          service_data:
            amount: 10
            confirmation_required: true
            
      # System settings
      - type: action
        icon: mdi:cog
        icon_color: gray
        tap_action:
          action: navigate
          navigation_path: /config/helpers
          
      # View statistics
      - type: action
        icon: mdi:chart-line
        icon_color: green
        tap_action:
          action: navigate
          navigation_path: /history?entity_id=sensor.water_amount
          
  # Historical data mini-graph
  - type: custom:mini-graph-card
    entities:
      - entity: sensor.water_amount
        name: Water Amount
        color: blue
        show_state: true
      - entity: sensor.soil_deficit
        name: Soil Deficit
        color: brown
        show_state: true
      - entity: sensor.current_temperature
        name: Temperature
        color: red
        show_state: true
        y_axis: secondary
    name: "Irrigation Trends"
    height: 150
    hours_to_show: 72
    group_by: hour
    show:
      name: true
      icon: true
      state: true
      legend: true
      fill: fade
    tap_action:
      action: more-info

  # System status and controls
  - type: entities
    title: "System Controls"
    show_header_toggle: false
    entities:
      - entity: input_boolean.irrigation_system_enabled
        name: "System Enabled"
        icon: mdi:power
        
      - entity: input_boolean.irrigation_notifications
        name: "Notifications"
        icon: mdi:bell
        
      - entity: input_number.irrigation_flow_rate
        name: "Flow Rate (L/min/m²)"
        icon: mdi:water-pump
        
      - type: divider
      
      - entity: counter.daily_irrigation_count
        name: "Today's Irrigations"
        icon: mdi:counter
        
      - entity: input_datetime.last_irrigation
        name: "Last Irrigation"
        icon: mdi:clock
        
      - entity: sensor.water_usage_today
        name: "Water Used Today"
        icon: mdi:water
        
      - type: section
        label: "Quick Actions"
        
      - entity: script.refresh_irrigation_forecast
        name: "🔄 Refresh Forecast"
        icon: mdi:refresh-circle
        
      - entity: script.execute_smart_irrigation
        name: "💧 Smart Irrigation"
        icon: mdi:sprinkler

  # Debug information (collapsible)
  - type: custom:fold-entity-row
    head:
      type: section
      label: "Debug Information"
    entities:
      - entity: sensor.irrigation_recommendation
        name: "Raw Recommendation Data"
        icon: mdi:code-json
        
      - entity: sensor.weather_data_age
        name: "Weather Data Age"
        icon: mdi:clock-alert
        
      - entity: binary_sensor.weather_suitable_irrigation
        name: "Weather Suitable"
        icon: mdi:weather-partly-cloudy
        
      - entity: sensor.addon_last_run
        name: "Addon Last Run"
        icon: mdi:docker
```

### Advanced Template Cards

```yaml
# Irrigation efficiency analytics card
- type: custom:apexcharts-card
  header:
    title: "Weekly Irrigation Efficiency"
    show: true
  graph_span: 7d
  span:
    end: day
  yaxis:
    - id: water
      min: 0
      max: 30
      apex_config:
        title:
          text: "Water (L/m²)"
    - id: temp
      opposite: true
      min: 0
      max: 40
      apex_config:
        title:
          text: "Temperature (°C)"
  series:
    - entity: sensor.water_amount
      yaxis_id: water
      name: "Water Applied"
      type: column
      color: blue
      group_by:
        func: max
        duration: 1d
    - entity: sensor.current_temperature
      yaxis_id: temp
      name: "Max Temperature"
      type: line
      color: red
      stroke_width: 2
      group_by:
        func: max
        duration: 1d
    - entity: sensor.precipitation_today
      yaxis_id: water
      name: "Rainfall"
      type: column
      color: lightblue
      group_by:
        func: sum
        duration: 1d
```

### Mobile-Optimized Quick Actions Card

```yaml
# Mobile quick actions for irrigation control
- type: custom:mushroom-chips-card
  chips:
    - type: template
      icon: mdi:sprinkler
      icon_color: |
        {% if is_state('binary_sensor.garden_needs_watering', 'on') %}
          blue
        {% else %}
          gray
        {% endif %}
      content: |
        {% if is_state('binary_sensor.garden_needs_watering', 'on') %}
          Water {{ states('sensor.water_amount') }}L/m²
        {% else %}
          No Water Needed
        {% endif %}
      tap_action:
        action: |
          {% if is_state('binary_sensor.garden_needs_watering', 'on') %}
            call-service
          {% else %}
            none
          {% endif %}
        service: script.execute_smart_irrigation
      hold_action:
        action: call-service
        service: script.manual_irrigation_with_confirmation
        service_data:
          amount: 15
          
    - type: template
      icon: mdi:weather-partly-cloudy
      icon_color: |
        {% if is_state('binary_sensor.weather_suitable_irrigation', 'on') %}
          green
        {% else %}
          red
        {% endif %}
      content: |
        {{ states('sensor.current_temperature') }}°C
        {{ states('sensor.wind_speed') }}km/h
      tap_action:
        action: more-info
        entity: weather.openweathermap
        
    - type: template
      icon: mdi:chart-timeline-variant
      icon_color: purple
      content: |
        {{ states('sensor.next_irrigation_check') }}
      tap_action:
        action: navigate
        navigation_path: /history?entity_id=sensor.irrigation_recommendation
```

## 10. Testing & Validation (HA OS 2025)

### System Health Checks

```yaml
# Add to configuration.yaml for system monitoring
template:
  sensor:
    - name: "Irrigation System Health"
      unique_id: "irrigation_system_health"
      state: >
        {% set addon_running = states('binary_sensor.irrigation_addon_running') == 'on' %}
        {% set mqtt_connected = states('sensor.irrigation_service_status') != 'unavailable' %}
        {% set data_fresh = (as_timestamp(now()) - as_timestamp(states.sensor.irrigation_recommendation.last_updated)) < 3600 %}
        
        {% if addon_running and mqtt_connected and data_fresh %}
          Healthy
        {% elif not addon_running %}
          Addon Offline
        {% elif not mqtt_connected %}
          MQTT Disconnected
        {% elif not data_fresh %}
          Data Stale
        {% else %}
          Unknown Issue
        {% endif %}
      icon: >
        {% set health = states('sensor.irrigation_system_health') %}
        {% if health == 'Healthy' %}
          mdi:check-circle
        {% else %}
          mdi:alert-circle
        {% endif %}
        
    - name: "Irrigation Data Age"
      unique_id: "irrigation_data_age"
      state: >
        {{ ((as_timestamp(now()) - as_timestamp(states.sensor.irrigation_recommendation.last_updated)) / 60) | round(0) }}
      unit_of_measurement: "minutes"
      icon: mdi:clock-alert
```

### Manual Testing Commands

```bash
# Test addon installation and configuration
docker logs addon_local_irrigation_advisor_simple

# Test MQTT connectivity
docker exec addon_local_irrigation_advisor_simple python3 /usr/bin/mqtt_simple.py

# Test configuration loading
docker exec addon_local_irrigation_advisor_simple python3 /usr/bin/debug_config.py

# Verify weather API connectivity
docker exec addon_local_irrigation_advisor_simple python3 -c "
from irrigation_advisor import WeatherAPI
import json
weather = WeatherAPI()
data = weather.get_current_weather()
print(json.dumps(data, indent=2))
"
```

### Validation Checklist

- [ ] Addon successfully installed and started
- [ ] MQTT broker connection established
- [ ] Weather data fetching successfully
- [ ] Irrigation recommendations updating every 30 minutes
- [ ] Binary sensor `garden_needs_watering` responding correctly
- [ ] Mobile notifications working (if enabled)
- [ ] Dashboard cards displaying current data
- [ ] Automations triggering at correct times
- [ ] Manual irrigation controls functional
- [ ] State persistence across restarts

### Modern HA OS 2025 Features Used

✅ **Modern Sensor Configuration**: `unique_id`, `device_class`, `state_class` attributes
✅ **Enhanced Automations**: `mode`, advanced `conditions`, `variables`, `timeout`
✅ **Rich Templates**: Multi-line templates with advanced logic
✅ **Mobile Integration**: Notification actions, rich data payloads
✅ **Custom Cards**: Mushroom cards, ApexCharts, enhanced dashboard
✅ **Modern Input Helpers**: Slider mode, enhanced selectors
✅ **Advanced Scripts**: Field validation, parallel execution, error handling

This integration provides a complete modern irrigation system fully compatible with Home Assistant OS 2025! 🌱💧
