import asyncio
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "PL2B2118"  # The name of the BLE golf ball device
CHARACTERISTIC_READY_UUID = "00000000-0000-1000-8000-00805f9b34f1"  # UUID for 'Ready' characteristic
DATA_TO_WRITE = bytearray([0x01])  # The data to write to 'Ready' characteristic; update as needed beacuse I'm guessing

# Mapping of characteristic UUIDs to their friendly names
CHARACTERISTICS = {
    "00000000-0000-1000-8000-00805f9b34f3": "RollCount",
    "00000000-0000-1000-8000-00805f9b34f8": "PuttMade",
    "00000000-0000-1000-8000-00805f9b34f4": "Velocity",
    "00000000-0000-1000-8000-00805f9b34f6": "Stimp",
    "00000000-0000-1000-8000-00805f9b34f2": "BallStopped",
    # "00000000-0000-1000-8000-00805f9b34f1": "Ready", # 'Ready' is used for writing, not notifying
    # "D079161C-4469-4870-ACEB-3E563875A0B7": "BallState", # IDK what this yet but it's there
}

def on_disconnect(client):
    print("Disconnected from the device!")
    loop.stop()

async def notification_handler(sender, data, client):
    """Simple notification handler which prints the data received."""
    name = CHARACTERISTICS.get(sender.uuid, "Unknown")
    print(f"Notification from {name}: {data}")

    # If 'PuttMade' notification is received, read the 'Ready' characteristic
    if name == "PuttMade":
        ready_value = await client.read_gatt_char(CHARACTERISTIC_READY_UUID)
        print(f"'Ready' characteristic value: {ready_value}")

def notification_wrapper(sender, data):
    """Wrapper function to handle notifications."""
    asyncio.create_task(notification_handler(sender, data, client))

async def find_device_by_name(device_name):
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == device_name:
            return device
    return None

async def main():
    global client
    device = await find_device_by_name(DEVICE_NAME)
    if not device:
        print(f"Device with name {DEVICE_NAME} not found.")
        return

    client = BleakClient(device.address, disconnected_callback=on_disconnect)
    try:
        await client.connect()
        if client.is_connected:
            print(f"Connected to {device.name} with address {device.address}")

            # Write to 'Ready' characteristic to enable notifications
            await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)
            print(f"Written to 'Ready' characteristic to enable data collection.")

            # Subscribe to other characteristics for notifications
            for uuid, name in CHARACTERISTICS.items():
                await client.start_notify(uuid, notification_wrapper)
                print(f"Subscribed to characteristic {name}")

            print("Listening for notifications, press Ctrl+C to exit...")
            await asyncio.Event().wait()  # Wait indefinitely until Ctrl+C is pressed

    except KeyboardInterrupt:
        print("Disconnected by user interruption...")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if client.is_connected:
            await client.disconnect()
            print("Disconnected from the device.")

# Run the main function
loop = asyncio.get_event_loop()
try:
    loop.run_until_complete(main())
finally:
    loop.close()
