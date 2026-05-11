import pandas as pd
import os
import json
import re

# Excel hard cell limit — strings at or near this length are truncated mid-JSON
EXCEL_CELL_LIMIT = 32760


def recover_truncated_json(raw: str) -> list | None:
    """
    Excel truncates cell content at 32,767 characters, leaving the JSON broken
    mid-string. Recovers all fully-closed timestamp entries before the cut.

    Collects ALL positions where a complete entry closes (pattern: }]}),
    then tries from the LAST one backwards to maximise recovered entries.
    """
    all_matches = list(re.finditer(r'\}\s*\]\s*\}', raw))
    for match in reversed(all_matches):
        attempt = raw[:match.end()] + ']'
        try:
            return json.loads(attempt)
        except json.JSONDecodeError:
            continue
    return None


def load_and_parse_meter_values():
    base_dir = os.path.dirname(__file__)
    data_dir = os.path.join(base_dir, 'data')

    if not os.path.exists(data_dir):
        print(f"Data directory not found at: {data_dir}")
        return None

    files = [f for f in os.listdir(data_dir) if f.endswith('.xlsx')]
    if not files:
        print("No Excel files found in the data directory.")
        return None

    pd.set_option('display.max_columns', None)
    pd.set_option('display.width', 1000)
    pd.set_option('display.max_colwidth', 80)

    file_path = os.path.join(data_dir, files[0])
    print(f"Loading: {files[0]}")

    # Identify the first non-empty sheet (name may be non-standard)
    xl = pd.ExcelFile("data/charging transaction.xlsx")
    print(f"Sheets found: {xl.sheet_names}")
    active_sheet = next(
        (s for s in xl.sheet_names if xl.parse(s, nrows=1).shape[0] > 0),
        xl.sheet_names[0]
    )
    print(f"Reading sheet: '{active_sheet}'")
    df = xl.parse(active_sheet)
    print(f"Raw shape: {df.shape}")
    print(f"Columns: {df.columns.tolist()}\n")

    rows = []
    stats = {'ok': 0, 'truncated_recovered': 0, 'truncated_lost': 0, 'empty': 0}

    for _, session in df.iterrows():
        # --- Parse MeterValues JSON ---
        raw = session.get('MeterValues')
        if pd.isna(raw) or raw is None:
            stats['empty'] += 1
            continue

        raw = str(raw) if not isinstance(raw, str) else raw
        truncated = len(raw) >= EXCEL_CELL_LIMIT

        meter_entries = None
        try:
            meter_entries = json.loads(raw)
            stats['ok'] += 1
        except (json.JSONDecodeError, TypeError):
            if truncated:
                # Excel cut this cell — attempt partial recovery
                meter_entries = recover_truncated_json(raw)
                if meter_entries is not None:
                    stats['truncated_recovered'] += 1
                else:
                    stats['truncated_lost'] += 1
            # Non-truncated parse failures are silently dropped (genuinely bad data)

        if not meter_entries:
            continue

        # --- Explode each (timestamp, sampledValues[]) pair ---
        for entry in meter_entries:
            timestamp = entry.get('timestamp')
            sampled_values = entry.get('sampledValues', [])

            for sv in sampled_values:
                rows.append({
                    # Session-level identifiers
                    'Id':                  session.get('Id'),
                    'TenantId':            session.get('TenantId'),
                    'ChargePointId':       session.get('ChargePointId'),
                    'ConnectorId':         session.get('ConnectorId'),
                    'StartDate':           session.get('StartDate'),
                    'EndDate':             session.get('EndDate'),
                    'DurationInMinutes':   session.get('DurationInMinutes'),
                    'Consumption':         session.get('Consumption'),
                    'GreenConsumption':    session.get('GreenConsumption'),
                    'Reason':              session.get('Reason'),
                    # Reading-level fields
                    'Timestamp':           timestamp,
                    'Measurand':           sv.get('measurand'),
                    'Value':               sv.get('value'),
                    'Unit':                sv.get('unit'),
                    'Phase':               sv.get('phase'),
                })

    if not rows:
        print("No MeterValues rows could be parsed.")
        return None

    parsed_df = pd.DataFrame(rows)

    # Cast Value to numeric (it arrives as a string in the JSON)
    parsed_df['Value'] = pd.to_numeric(parsed_df['Value'], errors='coerce')
    parsed_df['Timestamp'] = pd.to_datetime(parsed_df['Timestamp'], errors='coerce')

    total = sum(stats.values())
    print("--- Session parse summary ---")
    print(f"  Total sessions:              {total}")
    print(f"  Parsed cleanly:              {stats['ok']}")
    print(f"  Excel-truncated, recovered:  {stats['truncated_recovered']}  (partial data — last N entries kept)")
    print(f"  Excel-truncated, unrecoverable: {stats['truncated_lost']}  (fully dropped)")
    print(f"  Empty MeterValues:           {stats['empty']}")
    print(f"\nParsed readings shape: {parsed_df.shape}")
    print(f"\nMeasurand types found:\n{parsed_df['Measurand'].value_counts().to_string()}")
    print(f"\nPhase distribution:\n{parsed_df['Phase'].value_counts(dropna=False).to_string()}")
    print(f"\nSample rows:\n{parsed_df.head(10).to_string(index=False)}")

    return parsed_df

# ---------------------------------------------------------------------------
# Step 2 — Pivot measurands into wide-format columns
# ---------------------------------------------------------------------------
 
def pivot_measurands(parsed_df: pd.DataFrame) -> pd.DataFrame:
    """
    Transform the long-format parsed DataFrame (one row per measurand reading)
    into a wide-format DataFrame (one row per timestamp per session), where
    each (Measurand, Phase) combination becomes its own column.
 
    Column naming convention:
      - Phase is null/None  → column named after measurand only, e.g. 'SoC'
      - Phase is L1/L2/L3  → column named 'Measurand_Phase', e.g. 'Voltage_L1'
 
    Within each session the resulting NaN gaps (not every measurand is reported
    at every timestamp) are forward-filled, then backward-filled, to propagate
    the last known reading. This is appropriate for slowly-changing signals like
    voltage and SoC; abrupt transients are preserved because fill only crosses
    NaN gaps, not real zeros.
    """
    print("\n--- Step 2: Pivoting measurands ---")
 
    df = parsed_df.copy()
 
    # Build the column label for each reading
    df['MeasurandCol'] = df.apply(
        lambda r: r['Measurand'] if pd.isna(r['Phase']) else f"{r['Measurand']}_{r['Phase']}",
        axis=1
    )
 
    # Pivot: index = session identity + timestamp, columns = measurand labels
    # aggfunc='first' handles the rare case of duplicate readings at the same
    # timestamp (e.g. two entries for the same measurand in one sampledValues list)
    session_keys = ['Id', 'ChargePointId', 'ConnectorId', 'StartDate', 'EndDate',
                    'DurationInMinutes', 'Consumption', 'GreenConsumption', 'Reason']
 
    pivoted = df.pivot_table(
        index=session_keys + ['Timestamp'],
        columns='MeasurandCol',
        values='Value',
        aggfunc='first'
    ).reset_index()
 
    # Flatten the column index left by pivot_table
    pivoted.columns.name = None
 
    # Forward-fill then backward-fill within each session to bridge NaN gaps
    measurand_cols = [c for c in pivoted.columns if c not in session_keys + ['Timestamp']]
    pivoted = pivoted.sort_values(['Id', 'Timestamp'])
    pivoted[measurand_cols] = (
        pivoted.groupby('Id')[measurand_cols]
        .transform(lambda s: s.ffill().bfill())
    )
 
    print(f"  Shape before pivot: {parsed_df.shape}")
    print(f"  Shape after pivot:  {pivoted.shape}")
    print(f"\n  Measurand columns created:")
    for col in sorted(measurand_cols):
        non_null = pivoted[col].notna().sum()
        print(f"    {col:<40} {non_null:>8,} non-null values")
 
    return pivoted
 
 
# ---------------------------------------------------------------------------
# Step 3 — Group by (ChargePointId, ConnectorId)
# ---------------------------------------------------------------------------
 
def group_by_charger(pivoted_df: pd.DataFrame) -> dict:
    """
    Split the wide-format DataFrame into a dictionary keyed by
    (ChargePointId, ConnectorId), where each value is a DataFrame of all
    timestamped readings for that charger/connector pair, sorted by time.
 
    This is the unit of analysis for anomaly detection: each pair gets its
    own independent time series, which can be fed to Isolation Forest
    (session-level features) or an Autoencoder (sequence windows).
    """
    print("\n--- Step 3: Grouping by (ChargePointId, ConnectorId) ---")
 
    groups = {}
    measurand_cols = [c for c in pivoted_df.columns
                      if c not in ['Id', 'TenantId', 'ChargePointId', 'ConnectorId',
                                   'StartDate', 'EndDate', 'DurationInMinutes',
                                   'Consumption', 'GreenConsumption', 'Reason', 'Timestamp']]
 
    for (cp_id, conn_id), group_df in pivoted_df.groupby(['ChargePointId', 'ConnectorId']):
        key = (cp_id, conn_id)
        groups[key] = group_df.sort_values('Timestamp').reset_index(drop=True)
 
    print(f"  Total (ChargePointId, ConnectorId) pairs: {len(groups)}")
    print(f"\n  {'ChargePointId':<30} {'ConnectorId':>12} {'Sessions':>10} {'Readings':>10}")
    print(f"  {'-'*65}")
 
    for (cp_id, conn_id), gdf in sorted(groups.items()):
        sessions = gdf['Id'].nunique()
        readings = len(gdf)
        print(f"  {str(cp_id):<30} {str(conn_id):>12} {sessions:>10,} {readings:>10,}")
 
    print(f"\n  Measurand columns available for modelling:")
    for col in sorted(measurand_cols):
        print(f"    {col}")
 
    return groups


def export_to_excel(df: pd.DataFrame, filename: str = 'parsed_meter_readings.xlsx'):
    """
    Write the flat parsed DataFrame to Excel for human inspection.
    Useful for spot-checking values, filtering by charger, and eyeballing
    anomalies before committing to a model architecture.
    """
    base_dir = os.path.dirname(__file__)
    output_path = os.path.join(base_dir, 'data', filename)
 
    # Timestamps must be timezone-naive for Excel compatibility
    df = df.copy()
    if pd.api.types.is_datetime64tz_dtype(df['Timestamp']):
        df['Timestamp'] = df['Timestamp'].dt.tz_localize(None)
 
    with pd.ExcelWriter(output_path, engine='openpyxl') as writer:
        df.to_excel(writer, index=False, sheet_name='ParsedReadings')
 
        # Auto-fit column widths for readability
        ws = writer.sheets['ParsedReadings']
        for col in ws.columns:
            max_len = max(len(str(cell.value or '')) for cell in col)
            ws.column_dimensions[col[0].column_letter].width = min(max_len + 2, 40)
 
    print(f"\nExported to: {output_path}")
    print(f"  Rows: {len(df):,}  |  Columns: {len(df.columns)}")
 
 
def export_groups_to_single_sheet(groups_dict: dict, filename: str = 'all_chargers_pivoted.xlsx'):
    # Concatenate all DataFrames in the dictionary into one
    combined_df = pd.concat(groups_dict.values(), ignore_index=True)
    
    # Reuse your existing export function
    export_to_excel(combined_df, filename=filename)



if __name__ == "__main__":
    parsed_df = load_and_parse_meter_values()
    if parsed_df is not None:
        export_to_excel(parsed_df)
    else:
        raise SystemExit("Step 1 failed — no data to process.")

    # Step 2 — Pivot
    pivoted_df = pivot_measurands(parsed_df)
 
    # Step 3 — Group
    charger_groups = group_by_charger(pivoted_df)

    export_groups_to_single_sheet(charger_groups)