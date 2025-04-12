from bleak import BleakClient, BleakScanner
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


# This function scans for nearby Bluetooth devices and looks for the one with the name "GBK".
# If found, it checks the manufacturer data to determine if the device is on or off.  
# This is dtermined by the boolean at the end of the mfr_data, which is 0x01 for on and 0x00 for off.
async def get_power_status():
    stop_event = asyncio.Event()

    STATE_NAME = None

    def callback(device, adv):
        nonlocal STATE_NAME

        if adv.local_name is None:
            return 
        # https://github.com/virtuald/Govee-Reverse-Engineering/blob/495c3a5454eff2e50d8d8f8fe182dd69e3c43fb3/Products/H5080/scan.py
        if "GBK" in adv.local_name:
            for mfr_id, mfr_data in adv.manufacturer_data.items():
                is_on = mfr_data[-1] == 0x01
                STATE_NAME = "on" if is_on else "off"
                print(f"{adv.local_name}: state={STATE_NAME} (address={device.address}, mfr_data={mfr_data.hex()}) ")
                stop_event.set()
                break
                

    async with BleakScanner(callback) as scanner:
        try:
            await asyncio.wait_for(stop_event.wait(), timeout=10.0)  # Timeout in case it's not found
        except asyncio.TimeoutError:
            print("Device not found within timeout.")
            return None

    return STATE_NAME

# This function retrieves the color and brightness of the device.
# It sends commands to the device and listens for notifications which contain the color and brightness data.
# The color is expected to be in the format "ff00cc" (hex string).
# The brightness is expected to be a single byte value (0-255).
async def get_color_brightness():
    COLOR = None
    BRIGHTNESS = None

    def handle_notify(sender, data):
        nonlocal COLOR, BRIGHTNESS
        hex_data = data.hex()
        print(f"Notification from {sender}: {hex_data}")

        # Check for color (aa05)
        if hex_data.startswith("aa05"):
            r = data[3]
            g = data[4]
            b = data[5]
            # Convert to hex string like "#ff00cc"
            COLOR = f"#{r:02x}{g:02x}{b:02x}"
            print(f"Received color: {COLOR}")

        # Check for brightness (aa04)
        elif hex_data.startswith("aa04"):
            brightness = data[2]  # brightness is one byte, from 00 to ff
            BRIGHTNESS = brightness
            print(f"Received brightness: {BRIGHTNESS}")

    async def run():
        async with BleakClient(ADDRESS) as client:
            await client.start_notify(NOTIFY_CHAR_UUID, handle_notify)

            # Request color (aa04...)
            await client.write_gatt_char(
                WRITE_CHAR_UUID,
                bytearray.fromhex("aa040000000000000000000000000000000000ae"),
                response=False
            )
            await asyncio.sleep(0.2)

            # Request brightness (aa05...)
            await client.write_gatt_char(
                WRITE_CHAR_UUID,
                bytearray.fromhex("aa050100000000000000000000000000000000ae"),
                response=False
            )
            await asyncio.sleep(0.2)

            await client.stop_notify(NOTIFY_CHAR_UUID)

    await run()
    return COLOR, BRIGHTNESS

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
def control_light(action: str = None, color: str = None, brightness: int = None):
    cmd_queue = []

    # Add power command only if it's explicitly provided
    if action == "off":
        cmd_queue.append(POWER_OFF)
    elif action == "on":
        cmd_queue.append(POWER_ON)

    # If we're turning off, ignore other commands
    if action == "off":
        pass
    else:
        if color:
            cmd_queue.append(build_color_command(color))
        if brightness is not None:
            cmd_queue.append(build_brightness_command(int(brightness)))

    async def run():
        async with BleakClient(ADDRESS) as client:
            await client.start_notify(NOTIFY_CHAR_UUID, handle_notify)
            for cmd in cmd_queue:
                await client.write_gatt_char(WRITE_CHAR_UUID, cmd, response=False)
                await asyncio.sleep(0.2)
            await client.stop_notify(NOTIFY_CHAR_UUID)

    asyncio.run(run())