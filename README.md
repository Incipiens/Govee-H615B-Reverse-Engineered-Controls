# Govee H615B Website POC

This project is a Proof of Concept (POC) for integrating and interacting with the Govee H615B BLE (Bluetooth Low Energy) device through a web-based interface. This was built by reverse engineering the connection from a smartphone to the device, and is documented on [XDA](https://www.xda-developers.com/reverse-engineered-govee-smart-lights-smart-home/).

h615b_controller_cli.py is included so that you can see how this would be implemented in simple code, outside of a Flask app. It switches on the lights, sets them to magenta, sets the brightness to 100%, and then turns them off. It is essentially a template.

## Features

- Scan for nearby Govee H615B devices (using scanner.py, separate to the Flask app).
- Connect and interact with the device via BLE.
- Control device settings and retrieve data.

## Prerequisites

- Python
- Flask[async]
- Bleak

## Installation

1. Clone the repository:
    ```bash
    git clone https://github.com/Incipiens/Govee-H615B-Reverse-Engineered-Controls.git
    cd Govee-H615B-Reverse-Engineered-Controls
    ```

2. Start the server:
    ```bash
    flask run --host=0.0.0.0
    ```

3. Open your browser and navigate to `http://localhost:5000`.

## Usage

1. Ensure your host device is compatible with Bluetooth LE.
2. Get the MAC address of your Govee H615B using a tool like nRF Connect, or scan using scanner.py.
3. Replace the ADDRESS field in h615b_controller.py with the MAC or UUID of the device.
4. Control the device from your browser

## Technologies Used

- **Bleak**: For BLE communication.
- **Flask**: Web client

## License

This project is licensed under the [MIT License](LICENSE).

## Acknowledgments

This project and the reverse engineering process is documented on XDA.

- [reydanro](https://github.com/virtuald/Govee-Reverse-Engineering/blob/495c3a5454eff2e50d8d8f8fe182dd69e3c43fb3/Products/H5080/pair.py) for their work reverse engineering the H5080.
- [BeauJBurroughs](https://github.com/BeauJBurroughs/Govee-H6127-Reverse-Engineering) for their work reverse engineering the H6127.
