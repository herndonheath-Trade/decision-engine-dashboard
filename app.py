from flask import Flask, request, jsonify
from datetime import datetime, timezone
from collections import deque

app = Flask(__name__)

# -------------------------------------------------
# DECISION ENGINE STATE
# -------------------------------------------------

last_event = {
    "event": "WAITING",
    "time": None,
    "data": {}
}

event_history = deque(maxlen=25)


# -------------------------------------------------
# DASHBOARD
# -------------------------------------------------

@app.route("/")
def home():
    return """
<!DOCTYPE html>
<html>
<head>
    <title>Decision Engine</title>

    <style>
        body {
            background: #0b0f14;
            color: #e8edf2;
            font-family: Arial, sans-serif;
            margin: 0;
        }

        .header {
            background: #111820;
            border-bottom: 1px solid #26313d;
            padding: 20px 30px;
        }

        .title {
            font-size: 30px;
            font-weight: bold;
        }

        .subtitle {
            color: #8e9aa7;
            margin-top: 5px;
        }

        .container {
            padding: 25px 30px;
            max-width: 1100px;
            margin: auto;
        }

        .status-row {
            display: grid;
            grid-template-columns: repeat(3, 1fr);
            gap: 15px;
            margin-bottom: 20px;
        }

        .card {
            background: #111820;
            border: 1px solid #26313d;
            border-radius: 8px;
            padding: 20px;
        }

        .label {
            color: #8e9aa7;
            font-size: 13px;
            text-transform: uppercase;
            margin-bottom: 10px;
        }

        .value {
            font-size: 24px;
            font-weight: bold;
        }

        .online {
            color: #49d17d;
        }

        .event {
            color: #f1c84b;
        }

        button {
            background: #1f6feb;
            color: white;
            border: none;
            border-radius: 6px;
            padding: 12px 20px;
            font-size: 15px;
            cursor: pointer;
        }

        button:hover {
            background: #388bfd;
        }

        table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 10px;
        }

        th {
            text-align: left;
            color: #8e9aa7;
            border-bottom: 1px solid #26313d;
            padding: 10px;
        }

        td {
            padding: 10px;
            border-bottom: 1px solid #1d2630;
        }

        .footer {
            color: #596673;
            text-align: center;
            margin-top: 30px;
            font-size: 12px;
        }

        @media (max-width: 750px) {
            .status-row {
                grid-template-columns: 1fr;
            }
        }
    </style>
</head>

<body>

<div class="header">
    <div class="title">DECISION ENGINE</div>
    <div class="subtitle">MNQ Market Event Receiver</div>
</div>

<div class="container">

    <div class="status-row">

        <div class="card">
            <div class="label">Receiver</div>
            <div class="value online">ONLINE</div>
        </div>

        <div class="card">
            <div class="label">Latest Event</div>
            <div id="event" class="value event">WAITING</div>
        </div>

        <div class="card">
            <div class="label">Event Time</div>
            <div id="eventTime" class="value">--</div>
        </div>

    </div>

    <div class="card">
        <div class="label">Audio System</div>

        <button id="audioButton" onclick="enableAudio()">
            Enable Audio
        </button>

        <span id="audioStatus" style="margin-left:15px;color:#8e9aa7;">
            Audio disabled
        </span>
    </div>

    <br>

    <div class="card">
        <div class="label">Event Log</div>

        <table>
            <thead>
                <tr>
                    <th>Time</th>
                    <th>Event</th>
                </tr>
            </thead>

            <tbody id="eventLog">
            </tbody>
        </table>
    </div>

    <div class="footer">
        Decision Engine | TradingView Webhook Receiver
    </div>

</div>


<script>

let audioEnabled = false;
let lastSeenTime = null;
let audioContext = null;


function enableAudio() {

    audioContext = new (window.AudioContext ||
                        window.webkitAudioContext)();

    audioEnabled = true;

    document.getElementById("audioStatus").innerText =
        "Audio armed";

    document.getElementById("audioStatus").style.color =
        "#49d17d";

    document.getElementById("audioButton").innerText =
        "Audio Enabled";

    playTone(660, 0.12);
}


function playTone(frequency, duration) {

    if (!audioEnabled || !audioContext) {
        return;
    }

    const oscillator = audioContext.createOscillator();
    const gain = audioContext.createGain();

    oscillator.connect(gain);
    gain.connect(audioContext.destination);

    oscillator.frequency.value = frequency;
    oscillator.type = "sine";

    gain.gain.setValueAtTime(
        0.18,
        audioContext.currentTime
    );

    oscillator.start();

    oscillator.stop(
        audioContext.currentTime + duration
    );
}


function playEventSound(eventName) {

    const sounds = {

        "TEST_ALERT": 880,

        "R3_REACHED": 740,
        "R4_REACHED": 820,
        "R6_REACHED": 980,

        "S3_REACHED": 440,
        "S4_REACHED": 370,
        "S6_REACHED": 280,

        "PIVOT_REACHED": 620,

        "SHADOW_CONSUMED": 1050,

        "UP": 900,
        "DOWN": 320
    };

    const frequency = sounds[eventName] || 550;

    playTone(frequency, 0.30);
}


async function updateDashboard() {

    try {

        const response = await fetch(
            "/latest?ts=" + Date.now(),
            { cache: "no-store" }
        );

        const data = await response.json();

        document.getElementById("event").innerText =
            data.event || "WAITING";

        document.getElementById("eventTime").innerText =
            data.time || "--";


        if (
            data.time &&
            data.time !== lastSeenTime
        ) {

            if (lastSeenTime !== null) {
                playEventSound(data.event);
            }

            lastSeenTime = data.time;
        }


        const historyResponse = await fetch(
            "/history?ts=" + Date.now(),
            { cache: "no-store" }
        );

        const history =
            await historyResponse.json();

        const log =
            document.getElementById("eventLog");

        log.innerHTML = "";

        history.forEach(item => {

            const row =
                document.createElement("tr");

            const timeCell =
                document.createElement("td");

            const eventCell =
                document.createElement("td");

            timeCell.innerText =
                item.time || "--";

            eventCell.innerText =
                item.event || "UNKNOWN";

            row.appendChild(timeCell);
            row.appendChild(eventCell);

            log.appendChild(row);
        });

    }

    catch (error) {

        document.getElementById("event").innerText =
            "CONNECTION ERROR";
    }
}


setInterval(updateDashboard, 1000);

updateDashboard();

</script>

</body>
</html>
"""


# -------------------------------------------------
# TRADINGVIEW WEBHOOK
# -------------------------------------------------

@app.route("/webhook", methods=["POST"])
def webhook():

    global last_event

    data = request.get_json(silent=True)

    if not isinstance(data, dict):
        data = {
            "event": request.get_data(
                as_text=True
            ).strip()
        }

    event_name = str(
        data.get("event", "UNKNOWN")
    ).upper()

    event_time = datetime.now(
        timezone.utc
    ).strftime("%Y-%m-%d %H:%M:%S UTC")

    last_event = {
        "event": event_name,
        "time": event_time,
        "data": data
    }

    event_history.appendleft({
        "event": event_name,
        "time": event_time
    })

    return jsonify({
        "status": "received",
        "event": event_name
    })


# -------------------------------------------------
# DASHBOARD DATA
# -------------------------------------------------

@app.route("/latest")
def latest():

    response = jsonify(last_event)

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate"
    )

    return response


@app.route("/history")
def history():

    response = jsonify(
        list(event_history)
    )

    response.headers["Cache-Control"] = (
        "no-store, no-cache, must-revalidate"
    )

    return response


# -------------------------------------------------
# HEALTH CHECK
# -------------------------------------------------

@app.route("/health")
def health():

    return jsonify({
        "status": "online",
        "service": "Decision Engine"
    })


if __name__ == "__main__":
    app.run(
        host="0.0.0.0",
        port=10000
    )
