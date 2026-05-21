import os
import sys
import threading
import uuid
import traceback
import math
from datetime import date, datetime
from flask import Flask, render_template, request, jsonify

app = Flask(__name__)

jobs: dict = {}
jobs_lock = threading.Lock()

# path resolution
WEBAPP_DIR = os.path.dirname(os.path.abspath(__file__))
# Support both layouts:
#   AI2/webapp/simulator.py  +  AI2/data/generator.py   → ../data
#   webapp/simulator.py      +  webapp/data/generator.py → ./data
PROJECT_ROOT = os.path.normpath(os.path.join(WEBAPP_DIR, '..'))
_up   = os.path.normpath(os.path.join(WEBAPP_DIR, '..', 'data'))
_here = os.path.normpath(os.path.join(WEBAPP_DIR, 'data'))
DATA_DIR = _up if os.path.isfile(os.path.join(_up, 'generator.py')) else _here

if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
if DATA_DIR not in sys.path:
    sys.path.insert(0, DATA_DIR)

try:
    import generator_testing as gen
    print(f"[OK] benchmark generator loaded from {gen.__file__}")
except ImportError:
    try:
        import generator as gen
        print(f"[OK] generator loaded from {gen.__file__}")
    except ImportError as e:
        print(f"[ERROR] generator not found in {DATA_DIR}: {e}")
        raise

try:
    import model as ml_model
    print(f"[OK] model module loaded from {ml_model.__file__}")
except ImportError as e:
    print(f"[ERROR] model module not found in {PROJECT_ROOT}: {e}")
    raise

# JSON serialiser
def to_json_safe(value):
    import numpy as np
    import pandas as pd
    if isinstance(value, dict):
        return {str(k): to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_safe(v) for v in value]
    if value is None:
        return None
    if isinstance(value, float) and (math.isnan(value) or math.isinf(value)):
        return None
    if isinstance(value, np.generic):
        item = value.item()
        if isinstance(item, float) and (math.isnan(item) or math.isinf(item)):
            return None
        return item
    if isinstance(value, np.ndarray):
        return value.tolist()
    if isinstance(value, (pd.Timestamp, datetime, date)):
        return value.isoformat()
    return value

# pipeline 
def run_pipeline(job_id: str, params: dict):
    log_lines = []

    def log(msg: str):
        print(msg, flush=True)
        log_lines.append(str(msg))
        with jobs_lock:
            jobs[job_id]["log"] = list(log_lines)

    def finish(status: str, result=None):
        with jobs_lock:
            jobs[job_id]["status"] = status
            jobs[job_id]["result"] = to_json_safe(result or {})
            jobs[job_id]["log"] = list(log_lines)

    try:
        import numpy as np
        import pandas as pd

        log("🔧 Starting data generation...")

        active_anomalies = params.get("anomalies", [])
        if "all" in active_anomalies:
            if hasattr(gen, "ANOMALY_INJECTORS"):
                active_anomalies = list(gen.ANOMALY_INJECTORS.keys())
            elif hasattr(gen, "VALID_ANOMALIES"):
                active_anomalies = list(gen.VALID_ANOMALIES)
            else:
                active_anomalies = []

        n_chargers = int(params.get("chargers", 3))
        sessions = int(params.get("sessions", 60))
        anomaly_rate = float(params.get("anomaly_rate", 0.05))

        log(f"   Chargers: {n_chargers}  |  Sessions/charger: {sessions}  |  Anomaly rate: {anomaly_rate:.0%}")
        log(f"   Anomaly types: {active_anomalies or 'none'}")

        benchmark_meta = {}
        if hasattr(gen, "generate_benchmark_pair"):
            labeled_df, inference_df, benchmark_meta = gen.generate_benchmark_pair(
                n_chargers=n_chargers,
                sessions_per_charger=sessions,
                seed=42,
                active_anomalies=active_anomalies,
                anomaly_rate=anomaly_rate,
            )
        else:
            labeled_df = gen.generate_dataset(
                n_chargers=n_chargers,
                sessions_per_charger=sessions,
                active_anomalies=active_anomalies,
                anomaly_rate=anomaly_rate,
                seed=42,
                include_labels=True,
            )
            inference_df = gen.generate_dataset(
                n_chargers=n_chargers,
                sessions_per_charger=sessions,
                active_anomalies=active_anomalies,
                anomaly_rate=anomaly_rate,
                seed=43,
                include_labels=False,
            )
        log(f"✅ Generated {len(labeled_df):,} labeled rows for training and {len(inference_df):,} unlabeled rows for inference.")
        log(f"   Training labels present: {'is_anomaly' in labeled_df.columns and 'anomaly_type' in labeled_df.columns}")
        log(f"   Inference labels present: {'is_anomaly' in inference_df.columns or 'anomaly_type' in inference_df.columns}")
        if benchmark_meta:
            log(f"   Train chargers: {', '.join(benchmark_meta.get('train_chargers', []))}")
            log(f"   Inference chargers: {', '.join(benchmark_meta.get('inference_chargers', []))}")
            log(f"   Train anomaly types: {', '.join(benchmark_meta.get('train_anomalies', []))}")
            log(f"   Inference anomaly types: {', '.join(benchmark_meta.get('inference_anomalies', []))}")

        os.makedirs(DATA_DIR, exist_ok=True)
        train_path = os.path.join(DATA_DIR, "all_chargers_training_labeled.xlsx")
        pivot_path = os.path.join(DATA_DIR, "all_chargers_pivoted.xlsx")
        labeled_df.to_excel(train_path, index=False)
        inference_df.to_excel(pivot_path, index=False)
        log(f"   Saved labeled training data → {train_path}")
        log(f"   Saved unlabeled inference data → {pivot_path}")

        log("")
        log("🔍 Training on labeled synthetic data and scoring unlabeled synthetic data...")
        result = run_models(labeled_df, inference_df, log, active_anomalies, anomaly_rate)

        log("")
        log("✅ Pipeline complete.")
        finish("done", result)

    except Exception:
        tb = traceback.format_exc()
        log(f"❌ Error:\n{tb}")
        finish("error", {"error": tb})


def run_models(train_df, inference_df, log, active_anomalies, anomaly_rate):
    return ml_model.train_and_score(
        train_df=train_df,
        inference_df=inference_df,
        log=log,
        active_anomalies=active_anomalies,
        anomaly_rate=anomaly_rate,
    )


# routes 
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/api/run", methods=["POST"])
def api_run():
    params = request.get_json(force=True) or {}
    job_id = str(uuid.uuid4())
    with jobs_lock:
        jobs[job_id] = {"status": "running", "log": [], "result": None}
    threading.Thread(target=run_pipeline, args=(job_id, params), daemon=True).start()
    return jsonify({"job_id": job_id})

@app.route("/api/status/<job_id>")
def api_status(job_id):
    with jobs_lock:
        job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "job not found"}), 404
    return jsonify(to_json_safe(job))

if __name__ == "__main__":
    print(f"[INFO] DATA_DIR  : {DATA_DIR}")
    app.run(debug=False, port=5000, threaded=True)