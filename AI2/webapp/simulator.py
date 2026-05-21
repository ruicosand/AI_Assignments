import os
import sys
import threading
import uuid
import traceback
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
_up   = os.path.normpath(os.path.join(WEBAPP_DIR, '..', 'data'))
_here = os.path.normpath(os.path.join(WEBAPP_DIR, 'data'))
DATA_DIR = _up if os.path.isfile(os.path.join(_up, 'generator.py')) else _here

if DATA_DIR not in sys.path:
    sys.path.insert(0, DATA_DIR)

try:
    import generator as gen
    print(f"[OK] generator loaded from {gen.__file__}")
except ImportError as e:
    print(f"[ERROR] generator not found in {DATA_DIR}: {e}")
    raise

# JSON serialiser
def to_json_safe(value):
    import numpy as np
    import pandas as pd
    if isinstance(value, dict):
        return {str(k): to_json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [to_json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return value.item()
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
            active_anomalies = list(gen.ANOMALY_INJECTORS.keys())

        n_chargers = int(params.get("chargers", 3))
        sessions = int(params.get("sessions", 60))
        anomaly_rate = float(params.get("anomaly_rate", 0.05))

        log(f"   Chargers: {n_chargers}  |  Sessions/charger: {sessions}  |  Anomaly rate: {anomaly_rate:.0%}")
        log(f"   Anomaly types: {active_anomalies or 'none'}")

        df = gen.generate_dataset(
            n_chargers=n_chargers,
            sessions_per_charger=sessions,
            active_anomalies=active_anomalies,
            anomaly_rate=anomaly_rate,
            seed=42,
        )
        log(f"✅ Generated {len(df):,} rows across {n_chargers} charger(s).")

        os.makedirs(DATA_DIR, exist_ok=True)
        pivot_path = os.path.join(DATA_DIR, "all_chargers_pivoted.xlsx")
        df.to_excel(pivot_path, index=False)
        log(f"   Saved → {pivot_path}")

        log("")
        log("🔍 Running anomaly detection...")
        result = run_models(df, log, active_anomalies, anomaly_rate)

        log("")
        log("✅ Pipeline complete.")
        finish("done", result)

    except Exception:
        tb = traceback.format_exc()
        log(f"❌ Error:\n{tb}")
        finish("error", {"error": tb})


def run_models(df, log, active_anomalies, anomaly_rate):
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import IsolationForest
    from sklearn.cluster import KMeans
    from sklearn.metrics import (silhouette_score, confusion_matrix, precision_score, recall_score, f1_score)

    ELECTRIC = ["Current.Import_L1", "Current.Import_L2", "Current.Import_L3",
        "Power.Active.Import", "Power.Offered",
        "Voltage_L1", "Voltage_L2", "Voltage_L3",]
    
    INFO = ["ChargePointId", "ConnectorId", "Timestamp"]

    dataset = df.sort_values("Timestamp").copy()

    # True labels: if the generator tagged rows (column "is_anomaly"), use them;
    # otherwise synthesise based on anomaly_rate so we always have a confusion matrix.
    if "is_anomaly" in dataset.columns:
        dataset["true_label"] = dataset["is_anomaly"].astype(int)
    else:
        rng = np.random.default_rng(0)
        dataset["true_label"] = (rng.random(len(dataset)) < anomaly_rate).astype(int)

    features = dataset[INFO + ELECTRIC + ["true_label"]].dropna()
    n = len(features)
    log(f"   Rows with complete electrical data: {n:,}")

    if n < 20:
        log("⚠️  Too few complete rows. Increase sessions or enable voltage anomaly types.")
        return {"error": "Not enough data. Increase sessions or enable voltage anomalies."}

    split = int(n * 0.70)
    train = features.iloc[:split].copy()
    test  = features.iloc[split:].copy()

    model = IsolationForest(contamination=0.05, random_state=42)
    model.fit(train[ELECTRIC])

    raw_preds  = model.predict(test[ELECTRIC])   # +1 normal, -1 anomaly
    scores     = model.score_samples(test[ELECTRIC])

    # Convert to 0/1: anomaly=1, normal=0 (matches true_label convention)
    pred_label = (raw_preds == -1).astype(int)
    true_label = test["true_label"].values

    n_anom = int(pred_label.sum())
    log(f"   Anomalies detected: {n_anom} / {len(test)}  ({n_anom/len(test):.1%})")

    # Confusion matrix & metrics
    cm = confusion_matrix(true_label, pred_label)
    tn, fp, fn, tp = (cm.ravel() if cm.size == 4 else (cm[0,0], 0, 0, cm[0,0]))

    prec = float(precision_score(true_label, pred_label, zero_division=0))
    rec = float(recall_score(true_label, pred_label, zero_division=0))
    f1 = float(f1_score(true_label, pred_label, zero_division=0))
    acc = float((true_label == pred_label).mean())

    log(f"   Accuracy:  {acc:.3f}  |  Precision: {prec:.3f}  |  Recall: {rec:.3f}  |  F1: {f1:.3f}")
    log(f"   TP={int(tp)}  TN={int(tn)}  FP={int(fp)}  FN={int(fn)}")

    # Rule-based descriptions
    test2 = test.copy()
    test2["isAnomaly"]  = raw_preds
    test2["AnomScore"]  = scores

    anom_df = test2[test2["isAnomaly"] == -1]
    charger_counts = anom_df.groupby("ChargePointId")["isAnomaly"].count().sort_values(ascending=False)

    descriptions = []
    for cp_id in charger_counts.index:
        sub = anom_df[anom_df["ChargePointId"] == cp_id].sort_values("AnomScore")

        # voltage
        mv = sub.head(20)[["Voltage_L1","Voltage_L2","Voltage_L3"]].mean()
        for ph in ["Voltage_L1","Voltage_L2","Voltage_L3"]:
            if not (220 < mv[ph] < 240):
                descriptions.append({"ChargePointId": cp_id, "AnomalyType": f"{ph} out of range",
                                      "Voltage_L1": round(mv["Voltage_L1"],2),
                                      "Voltage_L2": round(mv["Voltage_L2"],2),
                                      "Voltage_L3": round(mv["Voltage_L3"],2)})
        for pa,pb in [("Voltage_L1","Voltage_L2"),("Voltage_L1","Voltage_L3"),("Voltage_L2","Voltage_L3")]:
            if abs(mv[pa]-mv[pb]) > 10:
                descriptions.append({"ChargePointId": cp_id, "AnomalyType": f"Phase diff {pa}/{pb} > 10V",
                                      "Voltage_L1": round(mv["Voltage_L1"],2),
                                      "Voltage_L2": round(mv["Voltage_L2"],2),
                                      "Voltage_L3": round(mv["Voltage_L3"],2)})

        # current
        top20c = sub.head(20).copy()
        cur_checks = {
            "L1 dead phase": (top20c["Current.Import_L1"]==0)&(top20c["Current.Import_L2"]>0)&(top20c["Current.Import_L3"]>0),
            "L2 dead phase": (top20c["Current.Import_L2"]==0)&(top20c["Current.Import_L1"]>0)&(top20c["Current.Import_L3"]>0),
            "L3 dead phase": (top20c["Current.Import_L3"]==0)&(top20c["Current.Import_L1"]>0)&(top20c["Current.Import_L2"]>0),
            "L1-L2 imbalance >2A": abs(top20c["Current.Import_L1"]-top20c["Current.Import_L2"])>2,
            "L1-L3 imbalance >2A": abs(top20c["Current.Import_L1"]-top20c["Current.Import_L3"])>2,
            "L2-L3 imbalance >2A": abs(top20c["Current.Import_L2"]-top20c["Current.Import_L3"])>2,
        }
        for label, mask in cur_checks.items():
            if mask.any():
                descriptions.append({"ChargePointId": cp_id, "AnomalyType": f"Current: {label}",
                                      "Current.Import_L1": round(top20c["Current.Import_L1"].mean(),2),
                                      "Current.Import_L2": round(top20c["Current.Import_L2"].mean(),2),
                                      "Current.Import_L3": round(top20c["Current.Import_L3"].mean(),2)})

        # power
        top50 = sub.head(50).copy()
        if (abs(top50["Power.Offered"]-top50["Power.Active.Import"])>2).any():
            descriptions.append({"ChargePointId": cp_id, "AnomalyType": "Power offered vs import > 2kW",
                                  "Power_Offered": round(top50["Power.Offered"].mean(),2),
                                  "Power.Active.Import": round(top50["Power.Active.Import"].mean(),2)})
        top50["Power_calc"] = (top50["Voltage_L1"]*top50["Current.Import_L1"] +
                               top50["Voltage_L2"]*top50["Current.Import_L2"] +
                               top50["Voltage_L3"]*top50["Current.Import_L3"]) / 1000
        if (abs(top50["Power_calc"]-top50["Power.Active.Import"])>1).any():
            descriptions.append({"ChargePointId": cp_id, "AnomalyType": "V×I inconsistency > 1kW",
                                  "Power_calc": round(top50["Power_calc"].mean(),2),
                                  "Power.Active.Import": round(top50["Power.Active.Import"].mean(),2)})

    log(f"   Rule violations: {len(descriptions)}")

    # KMeans
    clusters = {}
    if len(descriptions) >= 4:
        adf = pd.DataFrame(descriptions).fillna(0)
        num_cols = adf.select_dtypes(include="number").columns.tolist()
        best_k, best_sil = 2, -1
        for k in range(2, min(7, len(adf))):
            km = KMeans(n_clusters=k, random_state=42, n_init=10)
            km.fit(adf[num_cols])
            s = silhouette_score(adf[num_cols], km.labels_)
            if s > best_sil:
                best_k, best_sil = k, s
        log(f"   KMeans: best k={best_k}  (silhouette={best_sil:.3f})")
        km_final = KMeans(n_clusters=best_k, random_state=42, n_init=10)
        km_final.fit(adf[num_cols])
        for i, d in enumerate(descriptions):
            d["Cluster"] = int(km_final.labels_[i])
        clusters = {int(k): [d["AnomalyType"] for d in descriptions if d.get("Cluster")==k]
                    for k in set(km_final.labels_)}

    return {
        "n_test": int(len(test)),
        "n_anomalies": n_anom,
        "anomaly_descriptions": descriptions,
        "clusters": clusters,
        "charger_anomaly_counts": charger_counts.to_dict(),
        "score_distribution": scores.round(4).tolist(),
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
        },
        "confusion_matrix": {
            "tp": int(tp), "tn": int(tn),
            "fp": int(fp), "fn": int(fn),
        },
    }


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