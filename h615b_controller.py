from bleak import BleakClient
import asyncio


# This script is designed to control a Govee H615B LED strip light via Bluetooth Low Energy (BLE).
# It allows you to turn the light on/off, change its color, and adjust its brightness.
# The script uses the Bleak library to communicate with the device over BLE.
# Copyright Adam Conway 2025

# Swap this address for either the UUID or the MAC address of your device
ADDRESS = "<YOUR H615B ADDRESS HERE>"


# These UUIDs are specific to the Govee H615B device and are used to identify the service and characteristics for communication.
# The SERVICE_UUID is the main service UUID for the device.
# The WRITE_CHAR_UUID is used for writing commands to the device.
# The NOTIFY_CHAR_UUID is used for receiving notifications from the device.
SERVICE_UUID = "00010203-0405-0607-0809-0a0b0c0d1910"
WRITE_CHAR_UUID = "00010203-0405-0607-0809-0a0b0c0d2b11"
NOTIFY_CHAR_UUID = "00010203-0405-0607-0809-0a0b0c0d2b10"


# These are the power on and off commands for the device.
# They are sent as bytearrays to the device to control its power state.
# The commands are in hexadecimal format and are specific to the Govee H615B device.
POWER_ON = bytearray.fromhex("3301010000000000000000000000000000000033")
POWER_OFF = bytearray.fromhex("3301000000000000000000000000000000000032")

# This function handles notifications from the device.
def handle_notify(sender, data):
    print(f"Notification from {sender}: {data.hex()}")

# This function calculates a checksum to append to the end of a given hex string.
# The checksum is calculated by XORing all the bytes in the string.
def get_checksum(hex_string: str) -> str:
    xor = bytearray.fromhex("00")
    for i in range(0, len(hex_string), 2):
        xor[0] ^= int(hex_string[i:i+2], 16)
    return xor.hex()


# This function builds a command to set the color of the light.
# It takes a hex color string (e.g., "#ff0000") and constructs a command in hexadecimal format.
def build_color_command(hex_color: str) -> bytearray:
    hex_color = hex_color.lstrip("#")
    base_cmd = f"33050d{hex_color}00000000000000000000000000"
    checksum = get_checksum(base_cmd)
    return bytearray.fromhex(base_cmd + checksum)


# This function builds a command to set the brightness of the light.
# It takes an integer value between 0 and 255 and constructs a command in hexadecimal format.
def build_brightness_command(brightness: int) -> bytearray:
    brightness_hex = f"{brightness:02x}"
    base_cmd = f"3304{brightness_hex}00000000000000000000000000000000"
    checksum = get_checksum(base_cmd)
    return bytearray.fromhex(base_cmd + checksum)


# This function sends a command to the device using the BleakClient.
# It connects to the device and writes the command to the WRITE_CHAR_UUID characteristic.
async def send_command(command: bytearray):
    async with BleakClient(ADDRESS) as client:
        await client.write_gatt_char(WRITE_CHAR_UUID, command, response=False)


# This functions controls the H615B. It builds the color and brightness command, and can toggle the on/off state.
# If an off command is sent, it will not send the color or brightness commands.
def control_light(action: str, color: str = "#ffffff", brightness: int = 255):
    cmd_queue = []

    if action == "off":
        cmd_queue.append(POWER_OFF)
    else:
        cmd_queue.append(POWER_ON)
        if color:
            cmd_queue.append(build_color_command(color))
        if brightness is not None:
            cmd_queue.append(build_brightness_command(brightness))

    async def run():
        async with BleakClient(ADDRESS) as client:
            await client.start_notify(NOTIFY_CHAR_UUID, handle_notify)
            for cmd in cmd_queue:
                await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                await asyncio.sleep(0.2)
            await client.stop_notify(NOTIFY_CHAR_UUID)

    asyncio.run(run())