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
_up   = os.path.normpath(os.path.join(WEBAPP_DIR, '..', 'data'))
_here = os.path.normpath(os.path.join(WEBAPP_DIR, 'data'))
DATA_DIR = _up if os.path.isfile(os.path.join(_up, 'generator.py')) else _here

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
    import numpy as np
    import pandas as pd
    from sklearn.cluster import KMeans
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.metrics import (
        accuracy_score,
        average_precision_score,
        confusion_matrix,
        matthews_corrcoef,
        precision_recall_curve,
        roc_auc_score,
        f1_score,
        precision_score,
        recall_score,
        silhouette_score,
        balanced_accuracy_score,
    )
    from sklearn.pipeline import Pipeline

    ELECTRIC = [
        "Current.Import_L1", "Current.Import_L2", "Current.Import_L3",
        "Power.Active.Import", "Power.Offered",
        "Voltage_L1", "Voltage_L2", "Voltage_L3",
    ]
    INFO = ["ChargePointId", "ConnectorId", "Timestamp"]

    def engineer_features(dataset: pd.DataFrame, with_label: bool):
        frame = dataset.sort_values("Timestamp").copy()
        label_col = None
        if with_label:
            for candidate in ("is_anomaly", "true_label", "is_anomaly_label"):
                if candidate in frame.columns:
                    label_col = candidate
                    break
            if label_col is None:
                raise ValueError("No ground-truth anomaly label found in generated data.")
            frame[label_col] = frame[label_col].astype(int)

        frame["voltage_diff_l1_l2"] = (frame["Voltage_L1"] - frame["Voltage_L2"]).abs()
        frame["voltage_diff_l1_l3"] = (frame["Voltage_L1"] - frame["Voltage_L3"]).abs()
        frame["voltage_diff_l2_l3"] = (frame["Voltage_L2"] - frame["Voltage_L3"]).abs()
        frame["current_diff_l1_l2"] = (frame["Current.Import_L1"] - frame["Current.Import_L2"]).abs()
        frame["current_diff_l1_l3"] = (frame["Current.Import_L1"] - frame["Current.Import_L3"]).abs()
        frame["current_diff_l2_l3"] = (frame["Current.Import_L2"] - frame["Current.Import_L3"]).abs()
        frame["power_gap"] = frame["Power.Offered"] - frame["Power.Active.Import"]
        frame["power_gap_abs"] = frame["power_gap"].abs()
        frame["voltage_mean"] = frame[["Voltage_L1", "Voltage_L2", "Voltage_L3"]].mean(axis=1)
        frame["current_mean"] = frame[["Current.Import_L1", "Current.Import_L2", "Current.Import_L3"]].mean(axis=1)
        frame["power_calc"] = (
            frame["Voltage_L1"] * frame["Current.Import_L1"]
            + frame["Voltage_L2"] * frame["Current.Import_L2"]
            + frame["Voltage_L3"] * frame["Current.Import_L3"]
        ) / 1000
        frame["power_calc_gap_abs"] = (frame["power_calc"] - frame["Power.Active.Import"]).abs()
        frame["voltage_available"] = (~frame[["Voltage_L1", "Voltage_L2", "Voltage_L3"]].isna()).all(axis=1).astype(int)
        return frame, label_col

    feature_cols = ELECTRIC + [
        "voltage_diff_l1_l2", "voltage_diff_l1_l3", "voltage_diff_l2_l3",
        "current_diff_l1_l2", "current_diff_l1_l3", "current_diff_l2_l3",
        "power_gap", "power_gap_abs", "voltage_mean", "current_mean",
        "power_calc", "power_calc_gap_abs", "voltage_available",
    ]

    train_features, label_col = engineer_features(train_df, with_label=True)
    inference_features, _ = engineer_features(inference_df, with_label=False)

    train_features = train_features[INFO + [label_col] + feature_cols].copy().dropna(subset=[label_col])
    inference_features = inference_features[INFO + feature_cols].copy()
    n = len(train_features)
    log(f"   Rows available for ML training: {n:,}")

    if n < 20:
        log("⚠️  Too few rows for training. Increase sessions.")
        return {"error": "Not enough data for ML training."}

    split = int(n * 0.70)
    train = train_features.iloc[:split].copy()
    test = train_features.iloc[split:].copy()

    X_train = train[feature_cols]
    y_train = train[label_col]
    X_test = test[feature_cols]
    y_test = test[label_col].to_numpy()

    model = Pipeline(steps=[
        ("imputer", SimpleImputer(strategy="median")),
        ("rf", RandomForestClassifier(
            n_estimators=250,
            random_state=42,
            n_jobs=-1,
            class_weight="balanced_subsample",
            min_samples_split=8,
            min_samples_leaf=3,
        )),
    ])

    log("   Training Random Forest classifier...")
    model.fit(X_train, y_train)

    anomaly_prob = model.predict_proba(X_test)[:, 1]

    # Pick an operating threshold by maximizing F1 on the labeled validation split.
    threshold_candidates = np.linspace(0.05, 0.95, 19)
    threshold_rows = []
    best_threshold = 0.5
    best_f1 = -1.0
    for thr in threshold_candidates:
        thr_pred = (anomaly_prob >= thr).astype(int)
        thr_prec = float(precision_score(y_test, thr_pred, zero_division=0))
        thr_rec = float(recall_score(y_test, thr_pred, zero_division=0))
        thr_f1 = float(f1_score(y_test, thr_pred, zero_division=0))
        threshold_rows.append({"threshold": float(thr), "precision": thr_prec, "recall": thr_rec, "f1": thr_f1})
        if thr_f1 > best_f1:
            best_f1 = thr_f1
            best_threshold = float(thr)

    pred_label = (anomaly_prob >= best_threshold).astype(int)

    n_anom = int(pred_label.sum())
    log(f"   Validation anomalies detected: {n_anom} / {len(test)}  ({n_anom/len(test):.1%})")

    cm = confusion_matrix(y_test, pred_label, labels=[0, 1])
    tn, fp, fn, tp = cm.ravel()
    prec = float(precision_score(y_test, pred_label, zero_division=0))
    rec = float(recall_score(y_test, pred_label, zero_division=0))
    f1 = float(f1_score(y_test, pred_label, zero_division=0))
    acc = float(accuracy_score(y_test, pred_label))
    bal_acc = float(balanced_accuracy_score(y_test, pred_label))
    mcc = float(matthews_corrcoef(y_test, pred_label))
    roc_auc = float(roc_auc_score(y_test, anomaly_prob))
    pr_auc = float(average_precision_score(y_test, anomaly_prob))

    pr_precision, pr_recall, pr_thresholds = precision_recall_curve(y_test, anomaly_prob)
    roc_fpr, roc_tpr, roc_thresholds = None, None, None
    try:
        from sklearn.metrics import roc_curve
        roc_fpr, roc_tpr, roc_thresholds = roc_curve(y_test, anomaly_prob)
    except Exception:
        pass

    log(f"   Threshold selected: {best_threshold:.2f} (best validation F1={best_f1:.3f})")
    log(f"   Accuracy:  {acc:.3f}  |  Precision: {prec:.3f}  |  Recall: {rec:.3f}  |  F1: {f1:.3f}")
    log(f"   ROC-AUC: {roc_auc:.3f}  |  PR-AUC: {pr_auc:.3f}  |  Balanced Acc: {bal_acc:.3f}  |  MCC: {mcc:.3f}")
    log(f"   TP={int(tp)}  TN={int(tn)}  FP={int(fp)}  FN={int(fn)}")

    importances = model.named_steps["rf"].feature_importances_
    feature_importance = sorted(zip(feature_cols, importances), key=lambda x: x[1], reverse=True)
    top_features = feature_importance[:8]
    log("   Top features: " + ", ".join(f"{name}={score:.3f}" for name, score in top_features[:5]))

    log("   Scoring unlabeled synthetic inference data...")
    inference_prob = model.predict_proba(inference_features[feature_cols])[:, 1]
    inference_pred = (inference_prob >= best_threshold).astype(int)
    inference_n_anom = int(inference_pred.sum())
    log(f"   Inference anomalies detected: {inference_n_anom} / {len(inference_features)}  ({inference_n_anom/len(inference_features):.1%})")

    test2 = inference_features.copy()
    test2["isAnomaly"] = inference_pred
    test2["AnomScore"] = inference_prob
    anom_df = test2[test2["isAnomaly"] == 1]
    charger_counts = anom_df.groupby("ChargePointId")["isAnomaly"].count().sort_values(ascending=False)

    descriptions = []
    for cp_id in charger_counts.index:
        sub = anom_df[anom_df["ChargePointId"] == cp_id].sort_values("AnomScore", ascending=False)

        mv = sub.head(20)[["Voltage_L1", "Voltage_L2", "Voltage_L3"]].mean()
        if mv.isna().all():
            continue
        for ph in ["Voltage_L1", "Voltage_L2", "Voltage_L3"]:
            if not (220 < mv[ph] < 240):
                descriptions.append({
                    "ChargePointId": cp_id,
                    "AnomalyType": f"{ph} out of range",
                    "Voltage_L1": round(mv["Voltage_L1"], 2),
                    "Voltage_L2": round(mv["Voltage_L2"], 2),
                    "Voltage_L3": round(mv["Voltage_L3"], 2),
                })
        for pa, pb in [("Voltage_L1", "Voltage_L2"), ("Voltage_L1", "Voltage_L3"), ("Voltage_L2", "Voltage_L3")]:
            if abs(mv[pa] - mv[pb]) > 10:
                descriptions.append({
                    "ChargePointId": cp_id,
                    "AnomalyType": f"Phase diff {pa}/{pb} > 10V",
                    "Voltage_L1": round(mv["Voltage_L1"], 2),
                    "Voltage_L2": round(mv["Voltage_L2"], 2),
                    "Voltage_L3": round(mv["Voltage_L3"], 2),
                })

        top20c = sub.head(20).copy()
        cur_checks = {
            "L1 dead phase": (top20c["Current.Import_L1"] == 0) & (top20c["Current.Import_L2"] > 0) & (top20c["Current.Import_L3"] > 0),
            "L2 dead phase": (top20c["Current.Import_L2"] == 0) & (top20c["Current.Import_L1"] > 0) & (top20c["Current.Import_L3"] > 0),
            "L3 dead phase": (top20c["Current.Import_L3"] == 0) & (top20c["Current.Import_L1"] > 0) & (top20c["Current.Import_L2"] > 0),
            "L1-L2 imbalance >2A": (top20c["Current.Import_L1"] - top20c["Current.Import_L2"]).abs() > 2,
            "L1-L3 imbalance >2A": (top20c["Current.Import_L1"] - top20c["Current.Import_L3"]).abs() > 2,
            "L2-L3 imbalance >2A": (top20c["Current.Import_L2"] - top20c["Current.Import_L3"]).abs() > 2,
        }
        for label, mask in cur_checks.items():
            if mask.any():
                descriptions.append({
                    "ChargePointId": cp_id,
                    "AnomalyType": f"Current: {label}",
                    "Current.Import_L1": round(top20c["Current.Import_L1"].mean(), 2),
                    "Current.Import_L2": round(top20c["Current.Import_L2"].mean(), 2),
                    "Current.Import_L3": round(top20c["Current.Import_L3"].mean(), 2),
                })

        top50 = sub.head(50).copy()
        if (top50["power_gap_abs"] > 2).any():
            descriptions.append({
                "ChargePointId": cp_id,
                "AnomalyType": "Power offered vs import > 2kW",
                "Power_Offered": round(top50["Power.Offered"].mean(), 2),
                "Power.Active.Import": round(top50["Power.Active.Import"].mean(), 2),
            })
        if (top50["power_calc_gap_abs"] > 1).any():
            descriptions.append({
                "ChargePointId": cp_id,
                "AnomalyType": "V×I inconsistency > 1kW",
                "Power_calc": round(top50["power_calc"].mean(), 2),
                "Power.Active.Import": round(top50["Power.Active.Import"].mean(), 2),
            })

    log(f"   Rule violations: {len(descriptions)}")

    clusters = {}
    if len(descriptions) >= 4:
        adf = pd.DataFrame(descriptions).fillna(0)
        num_cols = adf.select_dtypes(include="number").columns.tolist()
        unique_points = len(adf[num_cols].drop_duplicates())
        if unique_points < 2:
            return {
                "n_test": int(len(test)),
                "n_inference": int(len(inference_features)),
                "n_anomalies": int(inference_n_anom),
                "threshold_summary": {
                    "best_threshold": round(best_threshold, 4),
                    "best_validation_f1": round(best_f1, 4),
                    "validation_thresholds": threshold_rows,
                },
                "feature_importance": [
                    {"feature": name, "importance": float(score)}
                    for name, score in feature_importance
                ],
                "curves": {
                    "precision_recall": {
                        "precision": [float(x) for x in pr_precision],
                        "recall": [float(x) for x in pr_recall],
                    },
                    "roc": {
                        "fpr": [float(x) for x in roc_fpr] if roc_fpr is not None else [],
                        "tpr": [float(x) for x in roc_tpr] if roc_tpr is not None else [],
                    },
                },
                "anomaly_descriptions": descriptions,
                "clusters": clusters,
                "charger_anomaly_counts": charger_counts.to_dict(),
                "metrics": {
                    "accuracy": round(acc, 4),
                    "precision": round(prec, 4),
                    "recall": round(rec, 4),
                    "f1": round(f1, 4),
                    "roc_auc": round(roc_auc, 4),
                    "pr_auc": round(pr_auc, 4),
                    "balanced_accuracy": round(bal_acc, 4),
                    "mcc": round(mcc, 4),
                    "threshold": round(best_threshold, 4),
                },
                "confusion_matrix": {
                    "tp": int(tp), "tn": int(tn),
                    "fp": int(fp), "fn": int(fn),
                },
            }
        best_k, best_sil = 2, -1
        for k in range(2, min(7, unique_points + 1)):
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
        clusters = {
            int(k): [d["AnomalyType"] for d in descriptions if d.get("Cluster") == k]
            for k in set(km_final.labels_)
        }

    return {
        "n_test": int(len(test)),
        "n_inference": int(len(inference_features)),
        "n_anomalies": int(inference_n_anom),
        "threshold_summary": {
            "best_threshold": round(best_threshold, 4),
            "best_validation_f1": round(best_f1, 4),
            "validation_thresholds": threshold_rows,
        },
        "feature_importance": [
            {"feature": name, "importance": float(score)}
            for name, score in feature_importance
        ],
        "curves": {
            "precision_recall": {
                "precision": [float(x) for x in pr_precision],
                "recall": [float(x) for x in pr_recall],
            },
            "roc": {
                "fpr": [float(x) for x in roc_fpr] if roc_fpr is not None else [],
                "tpr": [float(x) for x in roc_tpr] if roc_tpr is not None else [],
            },
        },
        "anomaly_descriptions": descriptions,
        "clusters": clusters,
        "charger_anomaly_counts": charger_counts.to_dict(),
        "metrics": {
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "balanced_accuracy": round(bal_acc, 4),
            "mcc": round(mcc, 4),
            "threshold": round(best_threshold, 4),
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