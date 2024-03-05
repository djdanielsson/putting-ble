import asyncio
from bleak import BleakScanner, BleakClient

DEVICE_NAME = "PL2B2118"  # The name of the BLE golf ball
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

def notification_handler(sender, data):
    """Simple notification handler which prints the data received."""
    uuid = sender.uuid if hasattr(sender, 'uuid') else str(sender)
    name = CHARACTERISTICS.get(uuid, "Unknown")
    print(f"Notification from {name}: {data}")

async def find_device_by_name(device_name):
    devices = await BleakScanner.discover()
    for device in devices:
        if device.name == device_name:
            return device
    return None

async def main():
    device = await find_device_by_name(DEVICE_NAME)
    if not device:
        print(f"Device with name {DEVICE_NAME} not found.")
        return

    async with BleakClient(device.address) as client:
        # Connect to the device
        connected = await client.connect()
        if connected:
            print(f"Connected to {device.name} with address {device.address}")

            # Write to 'Ready' characteristic to enable notifications
            await client.write_gatt_char(CHARACTERISTIC_READY_UUID, DATA_TO_WRITE)
            print(f"Written to 'Ready' characteristic to enable data collection.")

            # Subscribe to other characteristics for notifications
            for uuid, name in CHARACTERISTICS.items():
                if uuid != CHARACTERISTIC_READY_UUID:  # Skip 'Ready' characteristic for notification subscription
                    await client.start_notify(uuid, notification_handler)
                    print(f"Subscribed to characteristic {name}")

            print("Listening for notifications, press Ctrl+C to exit...")
            await asyncio.Event().wait()  # Wait indefinitely until Ctrl+C is pressed

            # Unsubscribe from all characteristics before disconnecting
            for uuid in CHARACTERISTICS.keys():
                if uuid != CHARACTERISTIC_READY_UUID:  # Skip 'Ready' characteristic for unsubscribing notifications
                    await client.stop_notify(uuid)
                    print(f"Unsubscribed from characteristic {uuid}")

        else:
            print(f"Failed to connect to {device.name}")

# Run the main function
loop = asyncio.get_event_loop()
loop.run_until_complete(main())
