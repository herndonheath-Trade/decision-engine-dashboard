from flask import Flask, request, jsonify
from datetime import datetime

app = Flask(__name__)

last_event = {
    "event": "WAITING",
    "time": None,
    "data": {}
}

@app.route("/")
def home():
    return """
    <h1>Decision Engine</h1>
    <p>Webhook receiver is ONLINE.</p>
    """

@app.route("/webhook", methods=["POST"])
def webhook():
    global last_event

    data = request.get_json(silent=True)

    if data is None:
        data = {"message": request.get_data(as_text=True)}

    event = data.get("event", data.get("message", "UNKNOWN"))

    last_event = {
        "event": event,
        "time": datetime.utcnow().isoformat(),
        "data": data
    }

    print("DECISION ENGINE EVENT:", last_event)

    return jsonify({
        "status": "received",
        "event": event
    }), 200

@app.route("/latest")
def latest():
    return jsonify(last_event)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
