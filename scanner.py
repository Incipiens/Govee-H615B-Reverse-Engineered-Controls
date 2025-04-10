import asyncio
from bleak import BleakClient, BleakScanner

# Bluetooth LE scanner
# Prints the name and address of every nearby Bluetooth LE device

async def main():
    devices = await BleakScanner.discover()

    for device in devices:
        print(device)

asyncio.run(main())