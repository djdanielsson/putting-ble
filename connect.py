import asyncio
import json
import logging
from bleak import BleakScanner, BleakClient
from aiomqtt import Client as AsyncMqttClient, MqttError

# Initialize logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration constants
MQTT_BROKER = "localhost"  # MQTT broker address
CHARACTERISTIC_READY_UUID = "00000000-0000-1000-8000-00805f9b34f1"  # 'Ready' characteristic UUID
DATA_TO_WRITE = bytearray([0x01])  # Data to enable notifications

# Mapping of BLE device names to friendly names
GOLF_BALLS = {
    "PL2B2118": "golfball1",
    # Add additional golf balls here as "DEVICE_NAME": "friendly_name"
}

# BLE characteristics of interest
CHARACTERISTICS = {
    "00000000-0000-1000-8000-00805f9b34f3": "RollCount",
    "00000000-0000-1000-8000-00805f9b34f8": "PuttMade",
    "00000000-0000-1000-8000-00805f9b34f4": "Velocity",
    "00000000-0000-1000-8000-00805f9b34f6": "Stimp",
    "00000000-0000-1000-8000-00805f9b34f2": "BallStopped",
    "00000000-0000-1000-8000-00805f9b34f1": "Ready"
}

async def send_to_mqtt(client, topic, message):
    """Publish a message to an MQTT topic."""
    try:
        await client.publish(topic, message)
        logger.debug(f"Published to MQTT: {topic} - {message}")
    except MqttError as e:
        logger.error(f"MQTT error: {e}")

async def notification_handler(sender, data, client, mqtt_client, friendly_name):
    """Handle BLE notifications, publish to MQTT, and manage the Ready characteristic."""
    characteristic_name = CHARACTERISTICS.get(sender.uuid, "Unknown")
    message = json.dumps({"characteristic": characteristic_name, "data": list(data)})
    mqtt_topic = f"golfball/{friendly_name}/{characteristic_name}"
    
    logger.info(f"BLE Notification: {message}")
    await send_to_mqtt(mqtt_client, mqtt_topic, message)

    if characteristic_name == "Ready" and data == bytearray([0]):
        logger.info("Ready characteristic is 0, setting it back to 1.")
        await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)

def notification_callback(sender, data, client, mqtt_client, friendly_name):
    """Wrapper for the notification handler to enable asyncio task creation."""
    asyncio.create_task(notification_handler(sender, data, client, mqtt_client, friendly_name))

async def read_ready_characteristic_periodically(client, interval=5):
    """Periodically read the Ready characteristic and log its value."""
    while client.is_connected:
        value = await client.read_gatt_char(CHARACTERISTIC_READY_UUID)
        logger.info(f"Ready characteristic value: {value}")
        await asyncio.sleep(interval)

async def find_device_by_name(device_name):
    """Discover BLE devices and return the one matching the given name."""
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == device_name:
            return device
    return None

async def main():
    """Main function to manage BLE connections and handle notifications."""
    for device_name, friendly_name in GOLF_BALLS.items():
        device = await find_device_by_name(device_name)
        if not device:
            logger.error(f"Device with name {device_name} not found.")
            continue

        async with BleakClient(device.address) as client, AsyncMqttClient(MQTT_BROKER) as mqtt_client:
            await client.connect()
            await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)
            initial_ready_value = await client.read_gatt_char(CHARACTERISTIC_READY_UUID)
            logger.info(f"Initial Ready characteristic value: {initial_ready_value}")

            for uuid in CHARACTERISTICS:
                await client.start_notify(uuid, lambda s, d: notification_callback(s, d, client, mqtt_client, friendly_name))

            asyncio.create_task(read_ready_characteristic_periodically(client))
            logger.info(f"{friendly_name} application is running. Press Ctrl+C to exit...")
            await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
