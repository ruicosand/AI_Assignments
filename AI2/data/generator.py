"""
Synthetic EV Charger Data Generator
=====================================
Generates realistic EV charger telemetry data that mirrors the structure of
all_chargers_pivoted.xlsx, with optional injection of the same anomaly types
detected by models.py.

Usage examples:
  # Clean data only
  python generate_synthetic_charger_data.py

  # Inject all anomaly types
  python generate_synthetic_charger_data.py --anomalies all

  # Inject specific anomalies
  python generate_synthetic_charger_data.py --anomalies voltage_out_of_range phase_imbalance

  # Full control
  python generate_synthetic_charger_data.py \
      --chargers 3 --sessions-per-charger 50 \
      --anomalies voltage_out_of_range current_zero_phase power_offered_diff \
      --anomaly-rate 0.05 \
      --output synthetic_data.xlsx

Available anomaly types:
  voltage_out_of_range  — Voltage on L1/L2/L3 drifts outside 220–240 V
  phase_voltage_diff    — Voltage difference between phases exceeds 10 V
  current_zero_phase    — One phase reads 0 A while the other two carry current
  current_imbalance     — |I_L1 - I_L2| or similar exceeds 2 A across phases
  power_offered_diff    — |Power.Offered - Power.Active.Import| exceeds 2 kW
  power_consistency     — Measured V×I power deviates from Power.Active.Import by > 1 kW
  all                   — Enable every anomaly type above
"""

import argparse
import uuid
import random
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# ---------------------------------------------------------------------------
# Constants derived from the real dataset
# ---------------------------------------------------------------------------

CHARGER_TEMPLATES = [
    {"ChargePointId": "/circutor",   "has_voltage": False, "connectors": [1, 2]},
    {"ChargePointId": "/starcharge1", "has_voltage": True,  "connectors": [1, 2]},
    {"ChargePointId": "/starcharge2", "has_voltage": True,  "connectors": [1, 2]},
]

STOP_REASONS = ["Remote", "EVDisconnected", "Local", "PowerLoss", "Other"]
STOP_REASON_WEIGHTS = [0.40, 0.35, 0.15, 0.05, 0.05]

# Normal operating ranges (from real data statistics)
NORMAL = {
    "voltage_mean":   233.0,
    "voltage_std":    3.0,
    "voltage_min":    223.0,
    "voltage_max":    243.0,
    "current_mean":   11.5,
    "current_std":    2.5,
    "current_min":    0.0,
    "current_max":    16.5,
    "power_offered_mean": 7.6,   # kW — fixed per session
    "power_offered_std":  3.5,
    "consumption_mean":  22.0,   # kWh — per session
    "consumption_std":   11.7,
    "duration_mean":    203.0,   # minutes
    "duration_std":      82.0,
    "energy_register_max": 19.34,
}

# How many telemetry rows per session (roughly every ~10-60 s)
ROWS_PER_SESSION_MEAN = 25
ROWS_PER_SESSION_STD  = 10

DATE_START = datetime(2026, 1, 2)
DATE_END   = datetime(2026, 4, 30)

# ---------------------------------------------------------------------------
# Anomaly injection helpers
# ---------------------------------------------------------------------------

def inject_voltage_out_of_range(row: dict, rng: np.random.Generator) -> dict:
    """Push one or more voltage phases outside the 220–240 V standard band."""
    phase = rng.choice(["Voltage_L1", "Voltage_L2", "Voltage_L3"])
    direction = rng.choice([-1, 1])
    # Either drop below 220 or push above 240
    if direction == -1:
        row[phase] = float(rng.uniform(190, 219))
    else:
        row[phase] = float(rng.uniform(241, 260))
    return row


def inject_phase_voltage_diff(row: dict, rng: np.random.Generator) -> dict:
    """Create a >10 V gap between two voltage phases."""
    base = float(rng.uniform(228, 235))
    offset = float(rng.uniform(11, 20))
    phase_a, phase_b = rng.choice(
        ["Voltage_L1", "Voltage_L2", "Voltage_L3"], size=2, replace=False
    )
    row[phase_a] = base
    row[phase_b] = base + offset
    return row


def inject_current_zero_phase(row: dict, rng: np.random.Generator) -> dict:
    """Set one phase to 0 A while the other two carry normal current."""
    dead_phase = rng.choice(
        ["Current.Import_L1", "Current.Import_L2", "Current.Import_L3"]
    )
    row[dead_phase] = 0.0
    # Ensure the other two are clearly non-zero
    for phase in ["Current.Import_L1", "Current.Import_L2", "Current.Import_L3"]:
        if phase != dead_phase:
            row[phase] = max(row.get(phase, 0.0), float(rng.uniform(5, 15)))
    return row


def inject_current_imbalance(row: dict, rng: np.random.Generator) -> dict:
    """Force a >2 A gap between two current phases."""
    base_current = float(rng.uniform(8, 14))
    imbalance    = float(rng.uniform(3, 8))
    phase_a, phase_b = rng.choice(
        ["Current.Import_L1", "Current.Import_L2", "Current.Import_L3"],
        size=2, replace=False,
    )
    row[phase_a] = base_current
    row[phase_b] = base_current + imbalance
    return row


def inject_power_offered_diff(row: dict, rng: np.random.Generator) -> dict:
    """|Power.Offered - Power.Active.Import| > 2 kW."""
    gap = float(rng.uniform(2.1, 6.0))
    row["Power.Active.Import"] = max(0.0, row.get("Power.Offered", 7.5) - gap)
    return row


def inject_power_consistency(row: dict, rng: np.random.Generator) -> dict:
    """Make V×I/1000 deviate from Power.Active.Import by more than 1 kW."""
    # Inflate reported active import well above measured power
    reported = row.get("Power.Active.Import", 5.0)
    row["Power.Active.Import"] = reported + float(rng.uniform(1.1, 4.0))
    return row


ANOMALY_INJECTORS = {
    "voltage_out_of_range":  inject_voltage_out_of_range,
    "phase_voltage_diff":    inject_phase_voltage_diff,
    "current_zero_phase":    inject_current_zero_phase,
    "current_imbalance":     inject_current_imbalance,
    "power_offered_diff":    inject_power_offered_diff,
    "power_consistency":     inject_power_consistency,
}

# ---------------------------------------------------------------------------
# Row / session generators
# ---------------------------------------------------------------------------

def normal_voltage(rng: np.random.Generator) -> float:
    return float(np.clip(
        rng.normal(NORMAL["voltage_mean"], NORMAL["voltage_std"]),
        NORMAL["voltage_min"], NORMAL["voltage_max"]
    ))


def normal_current(rng: np.random.Generator, power_offered: float) -> float:
    """Current is loosely derived from power offered (P ≈ V×I×3 / 1000)."""
    expected = (power_offered * 1000) / (3 * NORMAL["voltage_mean"])
    return float(np.clip(
        rng.normal(expected, 0.3),
        NORMAL["current_min"], NORMAL["current_max"]
    ))


def build_telemetry_row(
    charger: dict,
    connector_id: int,
    session_id: str,
    timestamp: datetime,
    power_offered: float,
    energy_so_far: float,
    session_start: datetime,
    session_end: datetime,
    consumption: float,
    duration_min: int,
    rng: np.random.Generator,
) -> dict:
    """Build one telemetry reading row."""
    has_v = charger["has_voltage"]

    current_l1 = normal_current(rng, power_offered)
    current_l2 = float(np.clip(rng.normal(current_l1, 0.2), 0, 16.5))
    current_l3 = float(np.clip(rng.normal(current_l1, 0.2), 0, 16.5))

    v_l1 = normal_voltage(rng) if has_v else np.nan
    v_l2 = normal_voltage(rng) if has_v else np.nan
    v_l3 = normal_voltage(rng) if has_v else np.nan

    if has_v:
        measured_power = (v_l1 * current_l1 + v_l2 * current_l2 + v_l3 * current_l3) / 1000
    else:
        measured_power = power_offered * rng.uniform(0.95, 1.02)

    return {
        "Id":                          session_id,
        "ChargePointId":               charger["ChargePointId"],
        "ConnectorId":                 connector_id,
        "StartDate":                   session_start,
        "EndDate":                     session_end,
        "DurationInMinutes":           duration_min,
        "Consumption":                 round(consumption, 3),
        "GreenConsumption":            round(consumption * rng.uniform(0.0, 0.3), 3),
        "Reason":                      random.choices(STOP_REASONS, STOP_REASON_WEIGHTS)[0],
        "Timestamp":                   timestamp,
        "Current.Import_L1":           round(current_l1, 2),
        "Current.Import_L2":           round(current_l2, 2),
        "Current.Import_L3":           round(current_l3, 2),
        "Energy.Active.Import.Register": round(energy_so_far, 3),
        "Power.Active.Import":         round(measured_power, 3),
        "Power.Offered":               round(power_offered, 3),
        "SoC":                         0.0,
        "Voltage_L1":                  round(v_l1, 1) if has_v else np.nan,
        "Voltage_L2":                  round(v_l2, 1) if has_v else np.nan,
        "Voltage_L3":                  round(v_l3, 1) if has_v else np.nan,
    }


def generate_session(
    charger: dict,
    session_start: datetime,
    active_anomalies: list,
    anomaly_rate: float,
    rng: np.random.Generator,
) -> list[dict]:
    """Generate all telemetry rows for a single charging session."""
    connector_id  = random.choice(charger["connectors"])
    session_id    = str(uuid.uuid4())
    duration_min  = max(1, int(rng.normal(NORMAL["duration_mean"], NORMAL["duration_std"])))
    consumption   = max(0.01, rng.normal(NORMAL["consumption_mean"], NORMAL["consumption_std"]))
    power_offered = max(1.0, rng.normal(
        NORMAL["power_offered_mean"], NORMAL["power_offered_std"]
    ))
    session_end   = session_start + timedelta(minutes=duration_min)

    n_rows = max(2, int(rng.normal(ROWS_PER_SESSION_MEAN, ROWS_PER_SESSION_STD)))
    interval_seconds = (duration_min * 60) / n_rows

    rows = []
    energy_so_far = 0.0
    energy_step   = consumption / n_rows

    for i in range(n_rows):
        ts = session_start + timedelta(seconds=i * interval_seconds)
        energy_so_far += energy_step

        row = build_telemetry_row(
            charger, connector_id, session_id, ts,
            power_offered, energy_so_far,
            session_start, session_end,
            consumption, duration_min, rng,
        )

        # Optionally inject an anomaly into this row
        if active_anomalies and rng.random() < anomaly_rate:
            injector = ANOMALY_INJECTORS[rng.choice(active_anomalies)]
            row = injector(row, rng)

        rows.append(row)

    return rows

# ---------------------------------------------------------------------------
# Main generator
# ---------------------------------------------------------------------------

def generate_dataset(
    n_chargers: int,
    sessions_per_charger: int,
    active_anomalies: list,
    anomaly_rate: float,
    seed: int,
) -> pd.DataFrame:
    rng = np.random.default_rng(seed)
    random.seed(seed)

    # Use real charger templates; cycle if n_chargers > 3
    chargers = [CHARGER_TEMPLATES[i % len(CHARGER_TEMPLATES)] for i in range(n_chargers)]

    total_span_days = (DATE_END - DATE_START).days
    all_rows = []

    for charger in chargers:
        for _ in range(sessions_per_charger):
            # Random session start within the date range
            offset_days    = rng.integers(0, total_span_days)
            offset_hours   = rng.integers(6, 22)   # 06:00–22:00 operating hours
            offset_minutes = rng.integers(0, 60)
            session_start  = DATE_START + timedelta(
                days=int(offset_days),
                hours=int(offset_hours),
                minutes=int(offset_minutes),
            )

            rows = generate_session(
                charger, session_start,
                active_anomalies, anomaly_rate, rng,
            )
            all_rows.extend(rows)

    df = pd.DataFrame(all_rows)
    df = df.sort_values("Timestamp").reset_index(drop=True)
    return df

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

VALID_ANOMALIES = list(ANOMALY_INJECTORS.keys())


def parse_args():
    parser = argparse.ArgumentParser(
        description="Generate synthetic EV charger telemetry data.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--chargers", type=int, default=3, metavar="N",
        help="Number of chargers to simulate (default: 3).",
    )
    parser.add_argument(
        "--sessions-per-charger", type=int, default=60, metavar="N",
        help="Charging sessions per charger (default: 60).",
    )
    parser.add_argument(
        "--anomalies", nargs="+", default=[],
        choices=VALID_ANOMALIES + ["all"],
        metavar="TYPE",
        help=(
            "Anomaly type(s) to inject. Use 'all' for every type. "
            f"Choices: {', '.join(VALID_ANOMALIES + ['all'])}"
        ),
    )
    parser.add_argument(
        "--anomaly-rate", type=float, default=0.05, metavar="RATE",
        help=(
            "Fraction of telemetry rows that will contain an injected anomaly "
            "(0.0–1.0, default: 0.05)."
        ),
    )
    parser.add_argument(
        "--output", type=str, default="synthetic_charger_data.xlsx",
        help="Output filename (default: synthetic_charger_data.xlsx).",
    )
    parser.add_argument(
        "--seed", type=int, default=42,
        help="Random seed for reproducibility (default: 42).",
    )
    return parser.parse_args()


def main():
    args = parse_args()

    # Resolve anomaly list
    if "all" in args.anomalies:
        active_anomalies = VALID_ANOMALIES
    else:
        active_anomalies = args.anomalies

    print("=" * 60)
    print("Synthetic EV Charger Data Generator")
    print("=" * 60)
    print(f"  Chargers            : {args.chargers}")
    print(f"  Sessions / charger  : {args.sessions_per_charger}")
    print(f"  Active anomalies    : {active_anomalies or 'none (clean data)'}")
    print(f"  Anomaly rate        : {args.anomaly_rate:.1%}")
    print(f"  Random seed         : {args.seed}")
    print(f"  Output file         : {args.output}")
    print("=" * 60)

    df = generate_dataset(
        n_chargers=args.chargers,
        sessions_per_charger=args.sessions_per_charger,
        active_anomalies=active_anomalies,
        anomaly_rate=args.anomaly_rate,
        seed=args.seed,
    )

    df.to_excel(args.output, index=False)

    print(f"\nDone! Generated {len(df):,} telemetry rows across "
          f"{args.chargers} charger(s) / "
          f"{args.chargers * args.sessions_per_charger} session(s).")
    print(f"Saved to: {args.output}")

    # Quick summary
    print("\nColumn dtypes:")
    print(df.dtypes.to_string())
    print("\nElectric feature statistics:")
    electric_cols = [
        "Current.Import_L1", "Current.Import_L2", "Current.Import_L3",
        "Power.Active.Import", "Power.Offered",
        "Voltage_L1", "Voltage_L2", "Voltage_L3",
    ]
    print(df[electric_cols].describe().round(3).to_string())


if __name__ == "__main__":
    main()