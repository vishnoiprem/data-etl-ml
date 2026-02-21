import json
import time
import random
from datetime import datetime
from collections import deque
from threading import Thread
import requests
import pyarrow as pa
import pyarrow.parquet as pq
from prometheus_client import start_http_server, Counter, Histogram

# -----------------------------
# CONFIGURATION
# -----------------------------
KAFKA_TOPIC = "gpu_telemetry"
SLACK_WEBHOOK = "https://hooks.slack.com/services/YOUR/WEBHOOK/HERE"  # Replace!
PROMETHEUS_PORT = 8000
WINDOW_SEC = 60  # 1-minute sliding window
THRESHOLD_CELSIUS = 80
MAX_MEMORY = 1000  # Max entries in state (simulate bounded memory)

# -----------------------------
# PROMETHEUS METRICS
# -----------------------------
start_http_server(PROMETHEUS_PORT)
alert_counter = Counter('gpu_alerts_total', 'Total number of GPU alerts')
temperature_hist = Histogram('gpu_temperature_celsius', 'GPU temperature distribution')

# -----------------------------
# STATE: Per-GPU Tracking
# -----------------------------
# {gpu_id: {'temps': deque(), 'last_emitted': timestamp}}
state = {}
window_size = WINDOW_SEC  # seconds

# -----------------------------
# SIMULATED KAFKA PRODUCER (for demo)
# -----------------------------
def produce_gpu_events():
    gpu_ids = [f"gpu-{i}" for i in range(1, 4)]
    while True:
        for gpu_id in gpu_ids:
            temp = random.randint(50, 100)  # Simulate real temp
            event = {
                "gpu_id": gpu_id,
                "timestamp": time.time(),
                "temperature": temp
            }
            print(f"[PRODUCER] Emitting: {json.dumps(event)}")
            # Simulate Kafka send
            process_event(event)
        time.sleep(2)

# -----------------------------
# PROCESS EVENT (Simulating Flink/Spark)
# -----------------------------
def process_event(event):
    gpu_id = event["gpu_id"]
    ts = event["timestamp"]
    temp = event["temperature"]

    # Update metrics
    temperature_hist.observe(temp)

    # Initialize state for this GPU if not exists
    if gpu_id not in state:
        state[gpu_id] = {"temps": deque(), "last_emitted": None}

    # Evict old temps (older than window)
    while state[gpu_id]["temps"] and ts - state[gpu_id]["temps"][0][1] > window_size:
        state[gpu_id]["temps"].popleft()

    # Add new temp
    state[gpu_id]["temps"].append((temp, ts))

    # Calculate p95 (approximate)
    temps = [t[0] for t in state[gpu_id]["temps"]]
    if len(temps) < 3:
        return  # Not enough data

    sorted_temps = sorted(temps)
    p95_idx = int(0.95 * len(sorted_temps))
    p95_temp = sorted_temps[p95_idx]

    # Check threshold
    if p95_temp > THRESHOLD_CELSIUS:
        last_alert_time = state[gpu_id]["last_emitted"]
        now = time.time()
        if last_alert_time is None or now - last_alert_time > 300:  # No duplicate in 5 min
            alert = {
                "timestamp": now,
                "gpu_id": gpu_id,
                "p95_temperature": round(p95_temp, 2),
                "status": "ALERT",
                "message": f"GPU {gpu_id} exceeded {THRESHOLD_CELSIUS}°C (p95={p95_temp:.1f}°C)"
            }
            send_slack_alert(alert)
            state[gpu_id]["last_emitted"] = now
            alert_counter.inc()

    # Save to Parquet (simulate daily backfill)
    save_to_parquet(event)

# -----------------------------
# SLACK ALERTING (Simulated)
# -----------------------------
def send_slack_alert(alert):
    payload = {
        "text": f"*🚨 GPU ALERT* : {alert['message']}",
        "attachments": [
            {
                "color": "danger",
                "fields": [
                    {"title": "GPU ID", "value": alert["gpu_id"], "short": True},
                    {"title": "p95 Temp", "value": f"{alert['p95_temperature']}°C", "short": True},
                    {"title": "Time", "value": datetime.fromtimestamp(alert["timestamp"]).strftime("%Y-%m-%d %H:%M:%S"), "short": True}
                ]
            }
        ]
    }
    try:
        response = requests.post(SLACK_WEBHOOK, json=payload)
        if response.status_code == 200:
            print(f"[SLACK] Alert sent: {alert['message']}")
        else:
            print(f"[ERROR] Slack failed: {response.text}")
    except Exception as e:
        print(f"[ERROR] Slack connection failed: {e}")

# -----------------------------
# SAVE TO PARQUET (Raw Data Sink)
# -----------------------------
def save_to_parquet(event):
    # Simulate partitioning by date and hour
    dt = datetime.fromtimestamp(event["timestamp"])
    date_str = dt.strftime("%Y-%m-%d")
    hour_str = dt.strftime("%H")

    path = f"data/raw/gpu_telemetry/ds={date_str}/hour={hour_str}/"
    filename = f"gpu_{event['gpu_id']}_{int(event['timestamp'])}.parquet"

    # Create record
    table = pa.Table.from_pylist([{
        "gpu_id": event["gpu_id"],
        "timestamp": event["timestamp"],
        "temperature": event["temperature"]
    }])

    # Write to file
    pq.write_table(table, f"{path}/{filename}")

    # Ensure directory exists
    import os
    os.makedirs(path, exist_ok=True)

# -----------------------------
# MAIN: Start Simulation
# -----------------------------
if __name__ == "__main__":
    print("🚀 Starting NVIDIA-style GPU Telemetry Pipeline...")
    print(f"📊 Prometheus metrics available at http://localhost:{PROMETHEUS_PORT}")
    print(f"🔔 Slack alerts will be sent to {SLACK_WEBHOOK.replace('https://hooks.slack.com/services/', '...')[:30]}...")

    # Run producer in background
    Thread(target=produce_gpu_events, daemon=True).start()

    # Keep main thread alive
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n🛑 Shutting down pipeline...")