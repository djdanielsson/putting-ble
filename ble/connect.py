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
import json
import logging
import argparse
from bleak import BleakScanner, BleakClient, BleakError
from aiomqtt import Client as AsyncMqttClient, MqttError

# Initialize logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Configuration constants
CHARACTERISTIC_READY_UUID = "00000000-0000-1000-8000-00805f9b34f1"  # 'Ready' characteristic UUID
BATTERY_LEVEL_CHARACTERISTIC_UUID = "00002a19-0000-1000-8000-00805f9b34fb"  # Battery Level characteristic UUID
DATA_TO_WRITE = bytearray([0x01])  # Data to enable notifications

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
    parser.add_argument('-g', '--golf-balls', type=str, required=True,
                        help='Comma-separated list of device_name:friendly_name pairs')
    return parser.parse_args()

async def send_to_mqtt(client, topic, message):
    """Publish a message to an MQTT topic."""
    try:
        await client.publish(topic, message.encode())
        logger.debug(f"Published to MQTT: {topic} - {message}")
    except MqttError as e:
        logger.error(f"MQTT error: {e}")

async def print_all_characteristic_values(client, friendly_name):
    for uuid, char_name in CHARACTERISTICS.items():
        try:
            value = await client.read_gatt_char(uuid)
            logger.info(f"{friendly_name} - Characteristic {char_name} ({uuid}): {value}")
        except Exception as e:
            logger.error(f"Error reading {char_name}: {e}")

async def notification_handler(sender, data, client, mqtt_client, friendly_name):
    """Handle BLE notifications, publish to MQTT, and manage the Ready characteristic."""
    characteristic_name = CHARACTERISTICS.get(sender.uuid, "Unknown")

    if characteristic_name == "ballState":
        state_index = data[0]  # Assuming the first byte is the state
        data_value = BALL_STATE_ENUM[state_index] if state_index < len(BALL_STATE_ENUM) else "UNKNOWN_STATE"
        if data_value == "ST_PUTT_COMPLETE":
            # Detected ST_PUTT_COMPLETE, attempt to "wake" the ball by toggling the Ready state
            logger.info("ST_PUTT_COMPLETE detected. Attempting to toggle Ready state to wake the ball.")
            await client.write_gatt_char(CHARACTERISTIC_READY_UUID, bytearray([0x00]))  # Set Ready to 0
            await asyncio.sleep(0.5)  # Short delay before setting Ready back to 1
            await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)  # Set Ready back to 1
    elif characteristic_name == "Velocity":
        data_value = data[1] / 10.0  # Convert to ft/sec
    else:
        data_value = data[1] if len(data) > 1 else data[0]  # Use the second value if available, else the first

    message = json.dumps({"data": data_value, "characteristic": characteristic_name})
    mqtt_topic = f"golfball/{friendly_name}/{characteristic_name}"
    
    logger.info(f"BLE Notification: {message}")
    await send_to_mqtt(mqtt_client, mqtt_topic, message)

    # # Probably not needed now that the ball is woken up by toggling Ready based on ballState
    # if characteristic_name == "Ready" and data == bytearray([0]):
    #     logger.info("Ready characteristic is 0, detected in notification handler. Setting it back to 1.")
    #     await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)


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

# # Troubleshooting bit, probably not needed 1/3
# async def periodic_read_ready(client, interval=2):
#     """Periodically reads the Ready characteristic."""
#     while True:
#         try:
#             ready_value = await client.read_gatt_char(CHARACTERISTIC_READY_UUID)
#             logger.info(f"Periodic Ready Check: {ready_value}")
#         except Exception as e:
#             logger.error(f"Error during periodic ready check: {e}")
#         await asyncio.sleep(interval)


async def main():
    args = parse_args()
    mqtt_broker = args.mqtt_broker
    golf_balls_list = args.golf_balls.split(',')
    golf_balls = {item.split(':')[0]: item.split(':')[1] for item in golf_balls_list}

    for device_name, friendly_name in golf_balls.items():
        device = await find_device_by_name(device_name)
        if not device:
            logger.error(f"Device with name {device_name} not found.")
            continue

        try:
            async with BleakClient(device.address) as client, AsyncMqttClient(mqtt_broker) as mqtt_client:
                logger.info(f"Connected to: {device.name} (Address: {device.address})")

                await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)
                await read_battery_level(client, mqtt_client, friendly_name)

                for uuid in CHARACTERISTICS:
                    await client.start_notify(uuid, lambda s, d: notification_callback(s, d, client, mqtt_client, friendly_name))

                # # Troubleshooting bit, probably not needed 2/3
                # # Start the periodic read task
                # periodic_task = asyncio.create_task(periodic_read_ready(client))

                logger.info(f"{friendly_name} application is running. Press Ctrl+C to exit...")
                await asyncio.Event().wait()

                # # Troubleshooting bit, probably not needed 3/3
                # # Cancel the periodic task when the application is stopping
                # periodic_task.cancel()
                # try:
                #     await periodic_task
                # except asyncio.CancelledError:
                #     logger.info("Periodic ready check task cancelled.")

        except BleakError as e:
            logger.error(f"BLE error with {friendly_name}: {e}")
        except MqttError as e:
            logger.error(f"MQTT error with {friendly_name}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error with {friendly_name}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
