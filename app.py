from flask import Flask, render_template, request, jsonify
from h615b_controller import control_light

app = Flask(__name__)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/control", methods=["POST"])
def control():
    data = request.json
    action = data.get("action", "on")
    color = data.get("color", "#ffffff")
    brightness = data.get("brightness", 255)

    try:
        control_light(action, color, int(brightness))
        return jsonify({"status": "success"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True)