"""
This script scans for Bluetooth Low Energy (BLE) devices that match a given name pattern and lists their characteristics, properties, and descriptors.

Usage:
    python scan.py [device_name_pattern]

Parameters:
    device_name_pattern (optional): A regular expression pattern to match the BLE device names. Defaults to "^PL2B" if not provided.

The script attempts to find a device matching the pattern within a set number of attempts. Upon successful connection, it lists all services, characteristics (along with their properties), and descriptors (including their values) for the discovered device.

Examples:
    python scan.py "^PL2B"  # Scans for devices whose names start with 'PL2B'
"""

import asyncio
import re
from bleak import BleakScanner, BleakClient

async def list_characteristics(device_pattern, attempts=5):
    found_device = None

    # Scan for devices and attempt to match with the pattern
    for attempt in range(1, attempts + 1):
        devices = await BleakScanner.discover()
        for device in devices:
            if re.match(device_pattern, device.name or ""):
                found_device = device
                break
        if found_device:
            break
        else:
            print(f"No devices found on attempt {attempt}/{attempts}. Retrying in 3 seconds...")
            await asyncio.sleep(3)

    # Exit if no devices were found after all attempts
    if not found_device:
        print(f"No devices found with pattern {device_pattern} after {attempts} attempts.")
        return

    # Connect to the device and list characteristics
    async with BleakClient(found_device.address) as client:
        await client.connect()
        print(f"Connecting to device: {found_device.name} with address {found_device.address}")
        
        # Access services directly from the client instance
        for service in client.services:
            print(f"\nService: {service}")
            for char in service.characteristics:
                properties = ', '.join(char.properties)
                print(f"  Characteristic: {char.uuid} - Properties: {properties}")
                for descriptor in char.descriptors:
                    try:
                        value = await client.read_gatt_descriptor(descriptor.handle)
                        print(f"    Descriptor: {descriptor.uuid} - Value: {value}")
                    except Exception as e:
                        print(f"    Error reading descriptor {descriptor.uuid}: {e}")

# Main entry point
if __name__ == "__main__":
    import sys
    device_pattern = sys.argv[1] if len(sys.argv) > 1 else "^PL2B"
    asyncio.run(list_characteristics(device_pattern))
