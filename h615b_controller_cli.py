from bleak import BleakClient
import asyncio

ADDRESS = "<YOUR H615B ADDRESS HERE>"

SERVICE_UUID = "00010203-0405-0607-0809-0a0b0c0d1910"
WRITE_CHAR_UUID = "00010203-0405-0607-0809-0a0b0c0d2b11"
NOTIFY_CHAR_UUID = "00010203-0405-0607-0809-0a0b0c0d2b10"

POWER_ON = bytearray.fromhex("3301010000000000000000000000000000000033")
POWER_OFF = bytearray.fromhex("3301000000000000000000000000000000000032")


def handle_notify(sender, data):
    print(f"Notification from {sender}: {data.hex()}")

def get_checksum(hex_string: str) -> str:
    xor = bytearray.fromhex("00")
    for i in range(0, len(hex_string), 2):
        chunk = hex_string[i:i+2]
        chunk_bytes = bytearray.fromhex(chunk)
        xor = bytearray([b1 ^ b2 for b1, b2 in zip(xor, chunk_bytes)])
    return xor.hex()

def build_color_command(hex_color: str) -> bytearray:
    hex_color = hex_color.lstrip("#")
    base_cmd = f"33050d{hex_color}00000000000000000000000000"
    checksum = get_checksum(base_cmd)
    full_cmd = base_cmd + checksum
    print(f"Final hex command: {full_cmd}")
    return bytearray.fromhex(full_cmd)

def build_brightness_command(brightness: int) -> bytearray:
    if not (0 <= brightness <= 255):
        raise ValueError("Brightness must be between 0 and 255.")

    brightness_hex = f"{brightness:02x}"
    base_cmd = f"3304{brightness_hex}00000000000000000000000000000000"
    checksum = get_checksum(base_cmd)
    full_cmd = base_cmd + checksum
    print(f"Final hex command: {full_cmd}")
    return bytearray.fromhex(full_cmd)


async def main():
    async with BleakClient(ADDRESS) as client:
        print("Connected")

        # Start notifications first
        await asyncio.sleep(0.1)
        await client.start_notify(NOTIFY_CHAR_UUID, handle_notify)

        # Send power-on command
        print("Sending power-on command...")
        await client.write_gatt_char(WRITE_CHAR_UUID, POWER_ON, response=False)

        # Build command to set color to magenta (#ff00ff)
        rgb = build_color_command("#ff00ff")

        # Build command to set brightness to 100
        brightness = build_brightness_command(255)
    
        # Sending brightness command
        await client.write_gatt_char(WRITE_CHAR_UUID, brightness, response=False)
        print("Brightness set!")

        # Sending color command
        await client.write_gatt_char(WRITE_CHAR_UUID, rgb, response=False)
        print("Color set!")

        await asyncio.sleep(5) 
        # Send power-off command
        print("Sending power-off command...")
        await client.write_gatt_char(WRITE_CHAR_UUID, POWER_OFF, response=False)

        await client.stop_notify(NOTIFY_CHAR_UUID)

asyncio.run(main())