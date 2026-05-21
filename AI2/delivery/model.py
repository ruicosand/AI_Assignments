"""Model training and inference logic for charger fault detection.

This module contains the auditable ML pipeline used by the simulator.
It accepts a labeled training dataset and an unlabeled inference dataset,
trains a Random Forest classifier, selects a decision threshold on the
validation split, and returns metrics plus anomaly summaries.
"""

from __future__ import annotations

from typing import Callable

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    balanced_accuracy_score,
    confusion_matrix,
    f1_score,
    matthews_corrcoef,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    silhouette_score,
)
from sklearn.pipeline import Pipeline


ELECTRIC = [
    "Current.Import_L1",
    "Current.Import_L2",
    "Current.Import_L3",
    "Power.Active.Import",
    "Power.Offered",
    "Voltage_L1",
    "Voltage_L2",
    "Voltage_L3",
]
INFO = ["ChargePointId", "ConnectorId", "Timestamp"]


def _default_log(message: str) -> None:
    print(message, flush=True)


def engineer_features(dataset: pd.DataFrame, with_label: bool) -> tuple[pd.DataFrame, str | None]:
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


def _make_feature_frame(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[INFO + ELECTRIC + [
        "voltage_diff_l1_l2",
        "voltage_diff_l1_l3",
        "voltage_diff_l2_l3",
        "current_diff_l1_l2",
        "current_diff_l1_l3",
        "current_diff_l2_l3",
        "power_gap",
        "power_gap_abs",
        "voltage_mean",
        "current_mean",
        "power_calc",
        "power_calc_gap_abs",
        "voltage_available",
    ]].copy()


FEATURE_COLS = ELECTRIC + [
    "voltage_diff_l1_l2",
    "voltage_diff_l1_l3",
    "voltage_diff_l2_l3",
    "current_diff_l1_l2",
    "current_diff_l1_l3",
    "current_diff_l2_l3",
    "power_gap",
    "power_gap_abs",
    "voltage_mean",
    "current_mean",
    "power_calc",
    "power_calc_gap_abs",
    "voltage_available",
]


def _safe_roc_curve(y_true: np.ndarray, scores: np.ndarray):
    try:
        from sklearn.metrics import roc_curve
        return roc_curve(y_true, scores)
    except Exception:
        return [], [], []


def train_and_score(
    train_df: pd.DataFrame,
    inference_df: pd.DataFrame,
    log: Callable[[str], None] | None = None,
    active_anomalies=None,
    anomaly_rate=None,
) -> dict:
    log = log or _default_log

    train_features, label_col = engineer_features(train_df, with_label=True)
    inference_features, _ = engineer_features(inference_df, with_label=False)

    if label_col is None:
        return {"error": "No ground-truth anomaly label found in generated data."}

    train_labels = train_features[label_col].astype(int).reset_index(drop=True)
    train_features = _make_feature_frame(train_features).reset_index(drop=True)
    train_features[label_col] = train_labels
    train_features = train_features.dropna(subset=[label_col])
    inference_features = _make_feature_frame(inference_features).reset_index(drop=True)

    n = len(train_features)
    log(f"   Rows available for ML training: {n:,}")

    if n < 20:
        return {"error": "Not enough data for ML training."}

    split = int(n * 0.70)
    train = train_features.iloc[:split].copy()
    test = train_features.iloc[split:].copy()

    X_train = train[FEATURE_COLS]
    y_train = train[label_col]
    X_test = test[FEATURE_COLS]
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
    pr_precision, pr_recall, _ = precision_recall_curve(y_test, anomaly_prob)
    roc_fpr, roc_tpr, _ = _safe_roc_curve(y_test, anomaly_prob)

    log(f"   Threshold selected: {best_threshold:.2f} (best validation F1={best_f1:.3f})")
    log(f"   Accuracy:  {acc:.3f}  |  Precision: {prec:.3f}  |  Recall: {rec:.3f}  |  F1: {f1:.3f}")
    log(f"   ROC-AUC: {roc_auc:.3f}  |  PR-AUC: {pr_auc:.3f}  |  Balanced Acc: {bal_acc:.3f}  |  MCC: {mcc:.3f}")
    log(f"   TP={int(tp)}  TN={int(tn)}  FP={int(fp)}  FN={int(fn)}")

    importances = model.named_steps["rf"].feature_importances_
    feature_importance = sorted(zip(FEATURE_COLS, importances), key=lambda x: x[1], reverse=True)
    log("   Top features: " + ", ".join(f"{name}={score:.3f}" for name, score in feature_importance[:5]))

    log("   Scoring unlabeled synthetic inference data...")
    inference_prob = model.predict_proba(inference_features[FEATURE_COLS])[:, 1]
    inference_pred = (inference_prob >= best_threshold).astype(int)
    inference_n_anom = int(inference_pred.sum())
    log(f"   Inference anomalies detected: {inference_n_anom} / {len(inference_features)}  ({inference_n_anom/len(inference_features):.1%})")

    scored = inference_df.sort_values("Timestamp").reset_index(drop=True).copy()
    scored["isAnomaly"] = inference_pred
    scored["AnomScore"] = inference_prob

    anom_df = scored[scored["isAnomaly"] == 1]
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
        top50["power_calc"] = (
            top50["Voltage_L1"] * top50["Current.Import_L1"]
            + top50["Voltage_L2"] * top50["Current.Import_L2"]
            + top50["Voltage_L3"] * top50["Current.Import_L3"]
        ) / 1000
        top50["power_gap_abs"] = (top50["Power.Offered"] - top50["Power.Active.Import"]).abs()
        top50["power_calc_gap_abs"] = (top50["power_calc"] - top50["Power.Active.Import"]).abs()

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
        if unique_points >= 2:
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
                "fpr": [float(x) for x in roc_fpr] if len(roc_fpr) else [],
                "tpr": [float(x) for x in roc_tpr] if len(roc_tpr) else [],
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
