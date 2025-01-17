"""
This Python script is a Bluetooth Low Energy (BLE) to MQTT bridge for monitoring BLE golf balls.
It scans for specified BLE devices, connects to them, and forwards their notifications to an
MQTT broker. The script allows for the specification of BLE devices and the MQTT broker address
through command-line arguments.

Features:
- Connects to BLE devices based on a list of device names and their friendly names.
- Monitors specified BLE characteristics and forwards notifications to MQTT.
- Manages the "Ready" characteristic to ensure the BLE device is always ready for data collection.
- Reads and publishes the battery level of connected BLE devices to MQTT.
- Utilizes asynchronous programming with asyncio for efficient handling of I/O operations.

Usage:
    python connect.py -m <MQTT_BROKER> -g <GOLF_BALL>

    Parameters:
    -m, --mqtt-broker: The address of the MQTT broker to which the data will be published.
    -g, --golf-ball: Device_name:friendly_name pair to identify and name the BLE device.

Example:
    python connect.py -m localhost -g PL2B2118:golfball1,PL2B2119:golfball2

    This command will connect to two BLE golf balls with device names PL2B2118 and PL2B2119, refer
    to them as golfball1 and golfball2 respectively, and publish their notifications to the MQTT
    broker running at localhost.
"""

import asyncio
import time
import json
import logging
import argparse
from bleak import BleakScanner, BleakClient, BleakError
from aiomqtt import Client as AsyncMqttClient, MqttError
from typing import Dict

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuration constants
CHARACTERISTIC_READY_UUID = "00000000-0000-1000-8000-00805f9b34f1"  # 'Ready' characteristic UUID
BATTERY_LEVEL_CHARACTERISTIC_UUID = "00002a19-0000-1000-8000-00805f9b34fb"  # Battery Level characteristic UUID
DATA_TO_WRITE = bytearray([0x01])  # Data to enable notifications

# Global variables
st_magnet_stop_encountered = False  # Tracks if ST_MAGNET_STOP was encountered
stroke_counter = 0  # Tracks strokes

# BLE characteristics of interest
CHARACTERISTICS = {
    "00000000-0000-1000-8000-00805f9b34f3": "ballRollCount",
    "00000000-0000-1000-8000-00805f9b34f4": "Velocity",
    "00000000-0000-1000-8000-00805f9b34f1": "Ready",
    "0d79161c-4469-4870-aceb-3e563875a0b7": "ballState"
}

# ballState enum mapping
BALL_STATE_ENUM = [
    "ST_READY",
    "ST_PUTT_STARTED",
    "ST_MAGNET_STOP",
    "ST_PUTT_STOPPING",
    "ST_BALL_STOPPED",
    "ST_PUTT_COMPLETE",
    "ST_PUTT_NOT_COUNTED",
    "ST_PUTT_CONNECT"
]

def parse_args():
    parser = argparse.ArgumentParser(description='BLE MQTT Client Application')
    parser.add_argument('-m', '--mqtt-broker', type=str, required=True, help='MQTT broker address')
    parser.add_argument('-g', '--golfball', type=str, required=True,
                        help='Device_name:friendly_name pair to identify and name the BLE device')
    return parser.parse_args()

async def send_to_mqtt(client, topic, message):
    """Publish a message to an MQTT topic."""
    try:
        await client.publish(topic, message.encode())
        logger.debug(f"Published to MQTT: {topic} - {message}")
    except MqttError as e:
        logger.error(f"MQTT error: {e}")

async def notification_handler(sender, data, client, mqtt_client, friendly_name):
    global st_magnet_stop_encountered, stroke_counter
    characteristic_name = CHARACTERISTICS.get(sender.uuid, "Unknown")

    # Default handling for characteristics other than ballState
    if characteristic_name == "Velocity":
        data_value = data[1] / 10.0  # Convert to ft/sec
    else:
        data_value = data[1] if len(data) > 1 else data[0]

    try:
        if characteristic_name == "ballState":
            state_index = data[0]
            data_value = BALL_STATE_ENUM[state_index] if state_index < len(BALL_STATE_ENUM) else "UNKNOWN_STATE"
            
            if data_value == "ST_PUTT_STARTED":
                stroke_counter += 1
            elif data_value == "ST_PUTT_NOT_COUNTED":
                stroke_counter = max(stroke_counter - 1, 0)  # Ensure counter doesn't go below 0
            
            if data_value == "ST_MAGNET_STOP":
                logger.info("ST_MAGNET_STOP detected. The golf ball has landed in the cup.")
                st_magnet_stop_encountered = True
            elif data_value == "ST_PUTT_COMPLETE" and not st_magnet_stop_encountered:
                logger.info("ST_PUTT_COMPLETE detected without ST_MAGNET_STOP. Toggling Ready state to wake the ball.")
                await client.write_gatt_char(CHARACTERISTIC_READY_UUID, bytearray([0x00]))  # Set Ready to 0
                await asyncio.sleep(0.5)
                await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)  # Set Ready back to 1

        # Construct and send the MQTT message
        if characteristic_name in ["ballState", "ballRollCount", "Velocity"]:
            message = json.dumps({"data": data_value, "stroke": stroke_counter})
        else:
            message = json.dumps({"data": data_value})

        mqtt_topic = f"golfball/{friendly_name}/{characteristic_name}"
        await send_to_mqtt(mqtt_client, mqtt_topic, message)

        # Log the message
        logger.info(f"BLE Notification: {characteristic_name} - {message}")

        # Reset the stroke counter and flag after sending the ST_MAGNET_STOP message
        if data_value == "ST_MAGNET_STOP":
            stroke_counter = 0
            st_magnet_stop_encountered = False

    except Exception as e:
        logger.error(f"Error handling BLE notification for {characteristic_name}: {e}")


def notification_callback(sender, data, client, mqtt_client, friendly_name):
    """Wrapper for the notification handler to enable asyncio task creation."""
    asyncio.create_task(notification_handler(sender, data, client, mqtt_client, friendly_name))

async def read_battery_level(client, mqtt_client, friendly_name):
    """Read the battery level of the connected BLE device and send to MQTT."""
    try:
        battery_level = await client.read_gatt_char(BATTERY_LEVEL_CHARACTERISTIC_UUID)
        battery_percentage = int(battery_level[0])
        logger.info(f"Battery Level: {battery_percentage}%")

        # Publish battery level to MQTT
        battery_message = json.dumps({"battery_level": battery_percentage})
        mqtt_topic = f"golfball/{friendly_name}/battery"
        await send_to_mqtt(mqtt_client, mqtt_topic, battery_message)
    except Exception as e:
        logger.error(f"Error reading battery level: {e}")

async def find_device_by_name(device_name):
    """Discover BLE devices and return the one matching the given name."""
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == device_name:
            return device
    return None

async def handle_new_player_command(mqtt_client, client, friendly_name):
    """Handle new player commands from MQTT."""
    command_topic = f"golfball/{friendly_name}/command"
    await mqtt_client.subscribe(command_topic)

    async for message in mqtt_client.messages:
        # Break the loop if the client is disconnected
        if not client.is_connected:
            break

        # Decode the message payload as JSON
        try:
            message_content = json.loads(message.payload.decode('utf-8'))
        except json.JSONDecodeError:
            logger.error(f"Received non-JSON message on {command_topic}")
            continue  # Skip to the next message if the current one isn't JSON

        # Check if the message contains the command "new_player"
        if message_content.get("command") == "new_player":
            logger.info(f"New player command received for {friendly_name}.")
            # Set the Ready characteristic to signal the next player's turn
            await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)
            logger.info(f"Set Ready for {friendly_name} for next player.")


async def main():
    args = parse_args()
    mqtt_broker: str = args.mqtt_broker
    device_name, friendly_name = args.golfball.split(':')

    start_time = time.time()
    while time.time() - start_time < 30 * 60:  # Retry for up to 30 minutes
        device = await find_device_by_name(device_name)
        if device:
            try:
                async with BleakClient(device.address) as client, AsyncMqttClient(mqtt_broker) as mqtt_client:
                    logger.info(f"Connected to: {device.name} (Address: {device.address})")

                    await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)
                    await read_battery_level(client, mqtt_client, friendly_name)

                    for uuid in CHARACTERISTICS.keys():
                        await client.start_notify(uuid, lambda s, d: notification_callback(s, d, client, mqtt_client, friendly_name))

                    await handle_new_player_command(mqtt_client, client, friendly_name)

                    logger.info(f"{friendly_name} application is running. Press Ctrl+C to exit...")

                    while client.is_connected:  # Check the connection status
                        await asyncio.sleep(1)  # Check every second

            except BleakError as e:
                logger.error(f"BLE error with {friendly_name}: {e}")
            except MqttError as e:
                logger.error(f"MQTT error with {friendly_name}: {e}")
            except Exception as e:
                logger.error(f"Unexpected error with {friendly_name}: {e}")
        else:
            logger.error(f"Device with name {device_name} not found. Retrying in 15 seconds...")
            await asyncio.sleep(15)

if __name__ == "__main__":
    asyncio.run(main())
