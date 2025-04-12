from flask import Flask, render_template, request, jsonify
from h615b_controller import control_light, get_power_status, get_color_brightness
import time

app = Flask(__name__)

# Cache for light status
light_cache = {
    "STATUS": None,
    "COLOR": None,
    "BRIGHTNESS": None,
    "LU": 0
}

# Capture light status before rendering page
@app.route("/")
async def index():
    now = time.time()
    cache_lifetime = 30  # Cache lasts seconds, and is updated when the status is modified

    # Check if cache is expired
    if now - light_cache["LU"] > cache_lifetime:
        print("Cache expired — refreshing light status...")
        light_cache["STATUS"] = await get_power_status()
        light_cache["COLOR"], light_cache["BRIGHTNESS"] = await get_color_brightness()
        light_cache["LU"] = now
    else:
        print("Using cached light status")

    
    return render_template("index.html", status = light_cache["STATUS"], color = light_cache["COLOR"], brightness = light_cache["BRIGHTNESS"]) 

# API returning status, color, and brightness. 
# This is used by the frontend to update the UI, and can be called by external tools built to control the H615B
@app.route("/api/light/status", methods=["GET"])
async def get_status():
    now = time.time()
    cache_lifetime = 30
    if now - light_cache["LU"] > cache_lifetime:
        light_cache["STATUS"] = await get_power_status()
        light_cache["COLOR"], light_cache["BRIGHTNESS"] = await get_color_brightness()
        light_cache["LU"] = now

    if light_cache["STATUS"] is None:
        return jsonify({"status": "error", "message": "Device not found"}), 404
    
    return jsonify({"status": "success", "power": light_cache["STATUS"], "color": light_cache["COLOR"], "brightness": light_cache["BRIGHTNESS"]})

# API to set power status of on or off, we update light cache if this is called
@app.route("/api/light/power", methods=["POST"])
def set_power():
    data = request.get_json()
    action = data.get("action")

    if action not in ["on", "off"]:
        return jsonify({"status": "error", "message": "Invalid action"}), 400

    try:
        control_light(action=action)
        light_cache["STATUS"] = action
        return jsonify({"status": "success", "action": action})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# API to set color, we update light cache if this is called
@app.route("/api/light/color", methods=["POST"])
def set_color():
    data = request.get_json()
    color = data.get("color")

    # Support rgb_color: [255, 0, 0]
    if not color and "rgb_color" in data:
        r, g, b = data["rgb_color"]
        color = "#{:02x}{:02x}{:02x}".format(r, g, b)

    if not color:
        return jsonify({"status": "error", "message": "No color provided"}), 400

    try:
        control_light(color=color)
        light_cache["COLOR"] = color
        return jsonify({"status": "success", "color": color})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# API to set brightness, we update light cache if this is called
@app.route("/api/light/brightness", methods=["POST"])
def set_brightness():
    data = request.get_json()
    brightness = data.get("brightness")

    if brightness is None:
        return jsonify({"status": "error", "message": "No brightness provided"}), 400

    try:
        control_light(brightness=int(brightness))
        light_cache["BRIGHTNESS"] = brightness
        return jsonify({"status": "success", "brightness": brightness})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/control", methods=["POST"])
def control():
    data = request.json
    action = data.get("action", "on")
    color = data.get("color", "#ffffff")
    brightness = data.get("brightness", 255)

    try:
        control_light(action, color, int(brightness))
        light_cache["STATUS"] = action
        light_cache["COLOR"] = color
        light_cache["BRIGHTNESS"] = brightness
        light_cache["LU"] = time.time()  # Update last update time
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)

