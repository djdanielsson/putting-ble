# putting-demo-summit
Demo material for Red Hat Summit demonstration with BLE golf ball

`connect.py` this script is designed to connect to a BLE-enabled golf ball, write a command to activate data collection, and listen to notifications from various characteristics that provide information about the golf ball's movements and interactions.

## Diagram

```mermaid
graph LR
    BLEDevice(Golf Ball BLE Device) -- BLE --> RaspberryPi(Raspberry Pi<br>BLE App & API Server)
    RaspberryPi -- MQTT Publish --> MQTTBroker["MQTT Broker<br>(Mosquitto)"]
    MQTTBroker -- MQTT Subscribe --> RaspberryPi
    RaspberryPi -- WebSocket (WS) --> WebBrowser{Web Browser<br>(Web UI)}
    WebBrowser -. HTTP .-> RaspberryPi

    classDef default fill:#f9f,stroke:#333,stroke-width:2px;
    classDef mqtt fill:#bbf,stroke:#f66,stroke-width:2px,stroke-dasharray: 5 5;
    classDef http fill:#fbf,stroke:#393,stroke-width:2px,stroke-dasharray: 3 3;

    class MQTTBroker mqtt;
    class WebBrowser,HTTP http;

```

## Requirements

- Python 3.7+
- `bleak` library for Bluetooth Low Energy communication

## Setup

1. Ensure you have Python 3.7 or higher installed.
2. Install the `bleak` library using `pip`:
3. Configure the DEVICE_NAME in the script to match the name of your BLE golf ball.