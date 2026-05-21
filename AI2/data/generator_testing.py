"""Benchmark-oriented synthetic generator for model evaluation.

This module builds on generator.py, but creates a more realistic split for
machine-learning evaluation:
- hold out charger IDs between training and inference
- hold out anomaly types between training and inference
- add subtle faults for the held-out set
- add sensor noise and missingness
- allow the inference set to be unlabeled
"""

from __future__ import annotations

import copy
from dataclasses import dataclass
from typing import Iterable

import numpy as np
import pandas as pd

import generator as base


ANOMALY_INJECTORS = base.ANOMALY_INJECTORS
VALID_ANOMALIES = list(ANOMALY_INJECTORS.keys())


ELECTRIC_COLS = [
    "Current.Import_L1",
    "Current.Import_L2",
    "Current.Import_L3",
    "Power.Active.Import",
    "Power.Offered",
    "Voltage_L1",
    "Voltage_L2",
    "Voltage_L3",
]

LABEL_COLS = ["is_anomaly", "anomaly_type"]


@dataclass(frozen=True)
class SplitConfig:
    charger_ids: tuple[str, ...]
    anomaly_types: tuple[str, ...]
    anomaly_rate: float
    seed: int
    include_labels: bool
    missing_rate: float
    voltage_noise_std: float
    current_noise_std: float
    power_noise_std: float


TRAIN_CONFIG = SplitConfig(
    charger_ids=("/circutor", "/starcharge1"),
    anomaly_types=("voltage_out_of_range", "current_zero_phase", "power_offered_diff"),
    anomaly_rate=0.06,
    seed=42,
    include_labels=True,
    missing_rate=0.015,
    voltage_noise_std=0.8,
    current_noise_std=0.25,
    power_noise_std=0.12,
)

INFERENCE_CONFIG = SplitConfig(
    charger_ids=("/starcharge2",),
    anomaly_types=("phase_voltage_diff", "current_imbalance", "power_consistency"),
    anomaly_rate=0.04,
    seed=43,
    include_labels=False,
    missing_rate=0.03,
    voltage_noise_std=1.4,
    current_noise_std=0.45,
    power_noise_std=0.2,
)


def _normalize_anomalies(anomalies: Iterable[str] | None) -> list[str]:
    if not anomalies:
        return []
    anomalies = list(anomalies)
    if "all" in anomalies:
        return list(base.ANOMALY_INJECTORS.keys())
    return [a for a in anomalies if a in base.ANOMALY_INJECTORS]


def _pick_allowed_ids(df: pd.DataFrame, allowed: tuple[str, ...]) -> pd.DataFrame:
    if not allowed:
        return df.copy()
    return df[df["ChargePointId"].isin(allowed)].copy()


def _soften_faults(df: pd.DataFrame, rng: np.random.Generator) -> pd.DataFrame:
    out = df.copy()
    if "anomaly_type" not in out.columns:
        return out

    for idx, row in out[out["is_anomaly"] == 1].iterrows():
        kind = row.get("anomaly_type", "")

        if kind == "voltage_out_of_range":
            phase = rng.choice(["Voltage_L1", "Voltage_L2", "Voltage_L3"])
            if pd.notna(out.at[idx, phase]):
                out.at[idx, phase] = float(
                    219.0 + rng.uniform(-0.4, 0.9)
                    if rng.random() < 0.5
                    else 240.0 + rng.uniform(0.2, 1.8)
                )

        elif kind == "phase_voltage_diff":
            phases = ["Voltage_L1", "Voltage_L2", "Voltage_L3"]
            a, b = rng.choice(phases, size=2, replace=False)
            base_value = float(rng.uniform(228.0, 236.0))
            out.at[idx, a] = base_value
            out.at[idx, b] = base_value + float(rng.uniform(6.5, 9.8))

        elif kind == "current_zero_phase":
            dead = rng.choice(["Current.Import_L1", "Current.Import_L2", "Current.Import_L3"])
            out.at[idx, dead] = 0.0
            for phase in ["Current.Import_L1", "Current.Import_L2", "Current.Import_L3"]:
                if phase != dead and pd.notna(out.at[idx, phase]):
                    out.at[idx, phase] = max(float(out.at[idx, phase]), float(rng.uniform(4.0, 10.0)))

        elif kind == "current_imbalance":
            a, b = rng.choice(["Current.Import_L1", "Current.Import_L2", "Current.Import_L3"], size=2, replace=False)
            base_current = float(rng.uniform(7.5, 13.0))
            out.at[idx, a] = base_current
            out.at[idx, b] = base_current + float(rng.uniform(2.1, 4.2))

        elif kind == "power_offered_diff":
            gap = float(rng.uniform(2.05, 3.8))
            offered = float(out.at[idx, "Power.Offered"])
            out.at[idx, "Power.Active.Import"] = max(0.0, offered - gap)

        elif kind == "power_consistency":
            current_power = float(out.at[idx, "Power.Active.Import"])
            out.at[idx, "Power.Active.Import"] = current_power + float(rng.uniform(0.6, 1.8))

    return out


def _add_noise_and_missingness(df: pd.DataFrame, cfg: SplitConfig, rng: np.random.Generator) -> pd.DataFrame:
    out = df.copy()

    # Sensor noise: subtle, but realistic.
    for col in ["Voltage_L1", "Voltage_L2", "Voltage_L3"]:
        mask = out[col].notna()
        out.loc[mask, col] = out.loc[mask, col] + rng.normal(0, cfg.voltage_noise_std, mask.sum())

    for col in ["Current.Import_L1", "Current.Import_L2", "Current.Import_L3"]:
        mask = out[col].notna()
        out.loc[mask, col] = np.clip(out.loc[mask, col] + rng.normal(0, cfg.current_noise_std, mask.sum()), 0, None)

    for col in ["Power.Active.Import", "Power.Offered"]:
        mask = out[col].notna()
        out.loc[mask, col] = np.clip(out.loc[mask, col] + rng.normal(0, cfg.power_noise_std, mask.sum()), 0, None)

    # Missingness: create partial sensor dropout.
    for col in ELECTRIC_COLS:
        if col not in out.columns:
            continue
        m = rng.random(len(out)) < cfg.missing_rate
        if col.startswith("Voltage_"):
            # keep no-voltage chargers intact: only drop on chargers that already have voltage
            m = m & out[col].notna().to_numpy()
        out.loc[m, col] = np.nan

    return out


def generate_dataset(
    n_chargers: int,
    sessions_per_charger: int,
    active_anomalies: list | None = None,
    anomaly_rate: float | None = None,
    seed: int | None = None,
    include_labels: bool = False,
    purpose: str = "inference",
) -> pd.DataFrame:
    """Generate a more realistic benchmark dataset.

    Parameters mirror generator.generate_dataset, but purpose controls the
    benchmark split and the anomaly profile.
    """

    purpose = purpose.lower().strip()
    if purpose not in {"train", "inference"}:
        raise ValueError("purpose must be 'train' or 'inference'")

    cfg = TRAIN_CONFIG if purpose == "train" else INFERENCE_CONFIG
    rng = np.random.default_rng(cfg.seed if seed is None else seed)

    anomalies = _normalize_anomalies(active_anomalies)
    if not anomalies:
        anomalies = list(cfg.anomaly_types)

    if anomaly_rate is None:
        anomaly_rate = cfg.anomaly_rate

    # Generate a labeled base dataset, then split/filter it.
    base_df = base.generate_dataset(
        n_chargers=n_chargers,
        sessions_per_charger=sessions_per_charger,
        active_anomalies=anomalies,
        anomaly_rate=anomaly_rate,
        seed=int(cfg.seed if seed is None else seed),
        include_labels=True,
    )

    # Charger-ID holdout: training and inference use disjoint charger IDs.
    available_ids = list(dict.fromkeys(base_df["ChargePointId"].tolist()))
    if len(available_ids) >= 2:
        if purpose == "train":
            keep_ids = available_ids[: max(1, len(available_ids) - 1)]
        else:
            keep_ids = available_ids[max(1, len(available_ids) - 1):]
            if not keep_ids:
                keep_ids = [available_ids[-1]]
    else:
        keep_ids = available_ids

    df = _pick_allowed_ids(base_df, tuple(keep_ids))

    # For the benchmark, the training split uses easy types, the inference split
    # uses held-out types. If the caller explicitly provides anomaly types, we
    # still respect them by filtering to the requested purpose-specific subset.
    if purpose == "train":
        desired = set(TRAIN_CONFIG.anomaly_types)
    else:
        desired = set(INFERENCE_CONFIG.anomaly_types)

    if "anomaly_type" in df.columns:
        normal_rows = df["anomaly_type"].eq("normal")
        anom_rows = df["anomaly_type"].isin(desired)
        df = df[normal_rows | anom_rows].copy()

    # Make the inference split harder: subtle faults + noise + missingness.
    if purpose == "inference":
        df = _soften_faults(df, rng)

    df = _add_noise_and_missingness(df, cfg, rng)
    df = df.sort_values("Timestamp").reset_index(drop=True)

    if not include_labels:
        df = df.drop(columns=[c for c in LABEL_COLS if c in df.columns])

    return df


def generate_benchmark_pair(
    n_chargers: int,
    sessions_per_charger: int,
    seed: int = 42,
) -> tuple[pd.DataFrame, pd.DataFrame, dict]:
    """Return labeled training and unlabeled inference datasets."""

    train_df = generate_dataset(
        n_chargers=n_chargers,
        sessions_per_charger=sessions_per_charger,
        seed=seed,
        include_labels=True,
        purpose="train",
    )
    inference_df = generate_dataset(
        n_chargers=n_chargers,
        sessions_per_charger=sessions_per_charger,
        seed=seed + 1,
        include_labels=False,
        purpose="inference",
    )

    meta = {
        "train_chargers": list(TRAIN_CONFIG.charger_ids),
        "inference_chargers": list(INFERENCE_CONFIG.charger_ids),
        "train_anomalies": list(TRAIN_CONFIG.anomaly_types),
        "inference_anomalies": list(INFERENCE_CONFIG.anomaly_types),
        "train_noise": {
            "missing_rate": TRAIN_CONFIG.missing_rate,
            "voltage_noise_std": TRAIN_CONFIG.voltage_noise_std,
            "current_noise_std": TRAIN_CONFIG.current_noise_std,
            "power_noise_std": TRAIN_CONFIG.power_noise_std,
        },
        "inference_noise": {
            "missing_rate": INFERENCE_CONFIG.missing_rate,
            "voltage_noise_std": INFERENCE_CONFIG.voltage_noise_std,
            "current_noise_std": INFERENCE_CONFIG.current_noise_std,
            "power_noise_std": INFERENCE_CONFIG.power_noise_std,
        },
    }

    return train_df, inference_df, meta
