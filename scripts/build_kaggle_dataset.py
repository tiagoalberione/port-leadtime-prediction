"""Build local Kaggle-ready datasets for Brazilian port-call lead-time studies."""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd


TARGET = "t_total_port_stay_h"
DATE_COL = "arrival_port_ts"
EXPECTED_ROWS = 129_625
SNAPSHOT_TOLERANCE_ROWS = 1_000

ANALYTICAL_NAME = "brazilian_port_calls_analytical_2023_2025"
MODEL_READY_NAME = "brazilian_port_calls_model_ready_2023_2025"

SPLIT_BOUNDS = {
    "train": ("2023-01-01", "2024-07-01"),
    "validation": ("2024-07-01", "2025-01-01"),
    "calibration": ("2025-01-01", "2025-07-01"),
    "final_test": ("2025-07-01", "2026-01-01"),
}

STATE_TO_REGION = {
    "AC": "NORTE",
    "AP": "NORTE",
    "AM": "NORTE",
    "PA": "NORTE",
    "RO": "NORTE",
    "RR": "NORTE",
    "TO": "NORTE",
    "AL": "NORDESTE",
    "BA": "NORDESTE",
    "CE": "NORDESTE",
    "MA": "NORDESTE",
    "PB": "NORDESTE",
    "PE": "NORDESTE",
    "PI": "NORDESTE",
    "RN": "NORDESTE",
    "SE": "NORDESTE",
    "DF": "CENTRO-OESTE",
    "GO": "CENTRO-OESTE",
    "MT": "CENTRO-OESTE",
    "MS": "CENTRO-OESTE",
    "ES": "SUDESTE",
    "MG": "SUDESTE",
    "RJ": "SUDESTE",
    "SP": "SUDESTE",
    "PR": "SUL",
    "RS": "SUL",
    "SC": "SUL",
}

TECHNICAL_QC_PREFIXES = ("has_", "flag_", "tmp_")
TECHNICAL_QC_COLUMNS = {
    "eligible_for_eda",
    "date",
    "port_display_ref",
    "port_name_ref",
    "latitude_r",
    "longitude_r",
}

PROVENANCE_SENSITIVE_COLUMNS = {
    "city",
    "latitude",
    "longitude",
    "latitude_r",
    "longitude_r",
    "port_display",
    "port_name_ref",
    "port_display_ref",
}

MODEL_READY_BASE_COLUMNS = [
    "port_call_id",
    DATE_COL,
    TARGET,
    "split",
]

TARGET_DERIVED_COLUMNS = {
    "t_wait_for_berthing_h",
    "t_operation_h",
    "t_post_operation_h",
    "t_wait_for_berthing_d",
    "t_operation_d",
    "t_post_operation_d",
    "t_total_port_stay_d",
    "log_t_wait_for_berthing_h",
    "log_t_operation_h",
    "log_t_post_operation_h",
    "log_t_total_port_stay_h",
    "t_wait_for_berthing_h_high",
    "t_wait_for_berthing_h_extreme",
    "t_operation_h_high",
    "t_operation_h_extreme",
    "t_total_port_stay_h_high",
    "t_total_port_stay_h_extreme",
}

POST_ARRIVAL_EVENT_COLUMNS = {
    "berthing_ts",
    "unberthing_ts",
    "departure_port_ts",
}

SAME_DAY_WEATHER_COLUMNS = {
    "temperature_2m_mean",
    "temperature_2m_max",
    "temperature_2m_min",
    "precipitation_sum",
    "rain_sum",
    "precipitation_hours",
    "wind_speed_10m_max",
    "wind_gusts_10m_max",
    "wind_direction_10m_dominant",
}

EDA_CONGESTION_COLUMNS = {
    "avg_wait_prev_20_calls_port",
    "avg_operation_prev_20_calls_port",
    "std_wait_prev_20_calls_port",
    "arrivals_same_day_port",
    "arrivals_prev_day_port",
    "arrivals_prev_7d_avg_port",
}

IDENTIFIER_COLUMNS = {
    "port_call_id",
    "imo",
    "vessel_id",
    "vessel_name",
    "port_name",
    "source_port",
    "source_port_name",
    "destination_port",
    "destination_port_name",
    "port_display",
    "source_port_display",
    "destination_port_display",
}

METADATA_COLUMNS = {
    DATE_COL,
    "split",
    "arrival_date",
    "city",
    "latitude",
    "longitude",
    "has_port_reference",
    "has_weather_data",
    "port_name_ref",
    "port_display_ref",
    "latitude_r",
    "longitude_r",
    "date",
    "arrival_date_for_features",
    "cutoff_date",
    "cutoff_ts",
}

EDA_ONLY_COLUMNS = {
    "operation_type",
    "arrival_year",
    "arrival_month",
    "arrival_day",
    "arrival_dayofweek",
    "arrival_hour",
}

DATA_DICTIONARY_COLUMNS = [
    "column",
    "dtype",
    "description",
    "source",
    "transformation",
    "availability_at_prediction_time",
    "modeling_role",
    "included_in_analytical",
    "included_in_model_ready",
    "notes",
]


def locate_repo_root() -> Path:
    """Locate the repository root from this script path or the current directory."""
    candidates = [Path(__file__).resolve(), Path.cwd().resolve()]
    for candidate in candidates:
        for parent in [candidate, *candidate.parents]:
            if (parent / ".git").exists() and (parent / "src").exists():
                return parent
    raise RuntimeError("Could not locate the port-leadtime-prediction repository root.")


ROOT = locate_repo_root()
OFFICIAL_PORTS_PSP_REFERENCE = ROOT / "kaggle" / "reference" / "portos_no_porto_sem_papel_setembro_2021.csv"
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from pipelines.build_eda_base import main as build_eda_base_main  # noqa: E402
from scripts.run_cap4_rebuild import build_registry  # noqa: E402
from src.config import EDA_BASE_FILE  # noqa: E402
from src.features.historical_context import add_cyclical_features, run_leakage_tests  # noqa: E402


def run_git(args: list[str]) -> str:
    """Run a read-only Git command for build metadata."""
    return subprocess.check_output(["git", *args], cwd=ROOT, text=True).strip()


def ensure_eda_base() -> None:
    """Create data/processed/eda_base.parquet through the official pipeline if needed."""
    if EDA_BASE_FILE.exists():
        return
    print(f"Source analytical base not found: {EDA_BASE_FILE.relative_to(ROOT)}")
    print("Rebuilding it with pipelines/build_eda_base.py...")
    build_eda_base_main()


def load_source_base() -> pd.DataFrame:
    """Load and minimally normalize the official processed analytical base."""
    ensure_eda_base()
    df = pd.read_parquet(EDA_BASE_FILE)
    for col in [DATE_COL, "berthing_ts", "unberthing_ts", "departure_port_ts", "arrival_date", "date"]:
        if col in df.columns:
            df[col] = pd.to_datetime(df[col], errors="coerce")
    return apply_public_geography(df)


def load_official_port_states() -> pd.DataFrame:
    """Load the official PSP port-code-to-UF reference used for public outputs."""
    if not OFFICIAL_PORTS_PSP_REFERENCE.exists():
        raise FileNotFoundError(
            "Official PSP port reference not found. Expected "
            f"{OFFICIAL_PORTS_PSP_REFERENCE.relative_to(ROOT)}."
        )
    ref = pd.read_csv(
        OFFICIAL_PORTS_PSP_REFERENCE,
        sep=";",
        encoding="latin1",
        skiprows=1,
        dtype="string",
    )
    ref = ref.rename(
        columns={
            "C�digo Bitrigrama": "port",
            "Código Bitrigrama": "port",
            "Nome": "official_port_name",
            "UF": "official_state_label",
            "Tipo": "official_port_type",
            "Ativo": "official_port_active",
        }
    )
    required = {"port", "official_state_label"}
    missing = sorted(required - set(ref.columns))
    if missing:
        raise RuntimeError(f"Official PSP port reference missing columns: {missing}")
    ref["port"] = ref["port"].astype("string").str.strip()
    ref["state"] = ref["official_state_label"].astype("string").str.extract(r"^([A-Z]{2})")[0]
    invalid = sorted(set(ref["state"].dropna()) - set(STATE_TO_REGION))
    if invalid:
        raise RuntimeError(f"Official PSP port reference has invalid UF values: {invalid}")
    return ref[["port", "state"]].dropna(subset=["port"]).drop_duplicates("port")


def apply_public_geography(df: pd.DataFrame) -> pd.DataFrame:
    """Replace manual geography with redistributable public geography semantics."""
    out = df.copy()
    for col in ["state", "region"]:
        if col in out.columns:
            out = out.drop(columns=col)
    state_ref = load_official_port_states()
    out = out.merge(state_ref, on="port", how="left")
    out["region"] = out["state"].map(STATE_TO_REGION).astype("string")
    return out


def assign_split(df: pd.DataFrame) -> pd.Series:
    """Assign the official half-open temporal split labels."""
    split = pd.Series(pd.NA, index=df.index, dtype="string")
    arrival = pd.to_datetime(df[DATE_COL], errors="coerce")
    for name, (start, end) in SPLIT_BOUNDS.items():
        mask = (arrival >= pd.Timestamp(start)) & (arrival < pd.Timestamp(end))
        split.loc[mask] = name
    return split


def analytical_columns(df: pd.DataFrame) -> list[str]:
    """Select the public analytical view while dropping internal QC artifacts."""
    cols: list[str] = []
    for col in df.columns:
        if col in PROVENANCE_SENSITIVE_COLUMNS:
            continue
        if col in TECHNICAL_QC_COLUMNS:
            continue
        if col.startswith(TECHNICAL_QC_PREFIXES):
            continue
        cols.append(col)
    return cols


def build_model_ready(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str], dict[str, Any]]:
    """Build the model-ready view from the official safe-history registry."""
    working = df.dropna(subset=[DATE_COL, TARGET]).copy()
    working = working[
        (working[DATE_COL] >= pd.Timestamp("2023-01-01"))
        & (working[DATE_COL] < pd.Timestamp("2026-01-01"))
    ].copy()
    working = add_cyclical_features(working)
    working, registry = build_registry(working)
    working["split"] = assign_split(working)

    feature_cols = [col for col in registry.enriched_features if col in working.columns]
    missing_features = sorted(set(registry.enriched_features) - set(feature_cols))
    if missing_features:
        raise RuntimeError(f"Model-ready features missing after registry build: {missing_features}")

    ordered_cols = list(dict.fromkeys([*MODEL_READY_BASE_COLUMNS, *feature_cols]))
    return working[ordered_cols].copy(), feature_cols, {
        "original_features": registry.original_features,
        "enriched_features": registry.enriched_features,
        "historical_families": registry.historical_families,
        "feature_metadata": registry.feature_metadata,
    }


def classify_column(column: str, model_ready_features: set[str]) -> str:
    """Classify a column by its modeling role in the Kaggle data release."""
    if column == TARGET:
        return "target"
    if column in model_ready_features:
        return "feature"
    if column in PROVENANCE_SENSITIVE_COLUMNS:
        return "metadata"
    if column in {"has_port_reference", "has_weather_data"}:
        return "metadata"
    if (
        column in POST_ARRIVAL_EVENT_COLUMNS
        or column in TARGET_DERIVED_COLUMNS
        or column in SAME_DAY_WEATHER_COLUMNS
        or column in EDA_CONGESTION_COLUMNS
        or column.startswith(TECHNICAL_QC_PREFIXES)
        or column == "eligible_for_eda"
    ):
        return "leakage_do_not_use"
    if column in IDENTIFIER_COLUMNS:
        return "identifier"
    if column in METADATA_COLUMNS:
        return "metadata"
    return "eda_only"


def availability(column: str, role: str) -> str:
    """Describe whether a column is available at the prediction timestamp."""
    if role in {"target", "identifier", "metadata"} and column not in {DATE_COL, "split"}:
        if column in POST_ARRIVAL_EVENT_COLUMNS or column in TARGET_DERIVED_COLUMNS:
            return "no"
        return "not_applicable"
    if role == "leakage_do_not_use":
        return "no"
    if column.endswith(("_prev_1d", "_prev_3d", "_prev_7d")):
        return "historical_only"
    if "_known_" in column or column.startswith(("state_", "flow_balance_", "arrivals_", "departures_", "opmix_")):
        return "historical_only"
    if column == "split":
        return "not_applicable"
    return "yes"


def source_for_column(column: str) -> str:
    """Return a concise source lineage for a column."""
    if column in {"city", "latitude", "longitude", "latitude_r", "longitude_r", "port_name_ref", "port_display_ref", "port_display"}:
        return "Internal historical port reference; not redistributed in Kaggle v1"
    if column in {DATE_COL, "berthing_ts", "unberthing_ts", "departure_port_ts"}:
        return "Porto Sem Papel vessel-stay records"
    if column in IDENTIFIER_COLUMNS or column in {"operation_type", "port"}:
        return "Porto Sem Papel vessel-stay records"
    if column == "state":
        return "Portos no Porto Sem Papel - PSP official public reference"
    if column == "region":
        return "Derived from official Brazilian state (UF)"
    if column in SAME_DAY_WEATHER_COLUMNS or column.endswith(("_prev_1d", "_prev_3d", "_prev_7d")):
        if column.startswith(("rain_", "precipitation_", "wind_", "temperature_")) or column in SAME_DAY_WEATHER_COLUMNS:
            return "Open-Meteo daily weather queried with internal historical port coordinates"
    if column == "split":
        return "Kaggle build script"
    if column.startswith("op_"):
        return "Derived from Porto Sem Papel operation_type"
    return "Derived by project pipeline"


def transformation_for_column(column: str, role: str) -> str:
    """Return the main transformation used to create the column."""
    if column == TARGET:
        return "Computed as departure_port_ts minus arrival_port_ts, expressed in hours after quality filters."
    if column == "port":
        return "Standardized from the Porto - Bitrigrama field in the vessel-stay source."
    if column == "port_name":
        return "Cleaned from the Porto - Nome field in the vessel-stay source."
    if column == "state":
        return "Exact join from official PSP port code to Brazilian state/UF when available."
    if column == "region":
        return "Deterministic Brazilian state-to-macro-region mapping from official state/UF."
    if column in {"city", "latitude", "longitude", "latitude_r", "longitude_r", "port_display", "port_name_ref", "port_display_ref"}:
        return "Historical manual geography/reference enrichment used internally by the academic pipeline; excluded from public Kaggle outputs."
    if column in POST_ARRIVAL_EVENT_COLUMNS:
        return "Parsed timestamp from vessel-stay records; consolidated using first/last event rules."
    if column == DATE_COL:
        return "Parsed arrival timestamp from vessel-stay records and converted to local wall time."
    if column.startswith("log_"):
        return "log1p transformation of the corresponding duration target."
    if column in TARGET_DERIVED_COLUMNS:
        return "Computed from post-arrival event timestamps or empirical target quantiles for EDA."
    if column.startswith("op_"):
        return "Boolean flag parsed from the multi-label operation_type text field."
    if column.startswith("arrival_"):
        return "Derived from arrival_port_ts."
    if column in SAME_DAY_WEATHER_COLUMNS:
        return "Daily realized weather value joined by rounded port coordinates and arrival date."
    if column.endswith(("_prev_1d", "_prev_3d", "_prev_7d")) and column.startswith(("rain_", "precipitation_", "wind_", "temperature_")):
        return "Lagged weather history using shift(1), excluding the arrival day."
    if (
        column.startswith(("arrivals_", "departures_", "flow_balance_", "state_", "opmix_"))
        or "_known_" in column
    ):
        return "Reconstructed historical feature using a D-1 cutoff and only events known before the prediction timestamp."
    if column == "split":
        return "Assigned from half-open official temporal intervals based on arrival_port_ts."
    if column.startswith(TECHNICAL_QC_PREFIXES) or column == "eligible_for_eda":
        return "Internal quality-control flag or temporary duration used before target creation."
    if role == "identifier":
        return "Cleaned and standardized identifier retained from the source records."
    return "Cleaned, standardized, or joined field from the project preparation pipeline."


def description_for_column(column: str, role: str) -> str:
    """Return a human-readable data dictionary description."""
    exact = {
        "port_call_id": "Unique source DUV identifier of the consolidated vessel port call.",
        "port": "Brazilian port code where the vessel call occurred, standardized from the source bitrigrama field.",
        "port_name": "Port name reported in the vessel-stay source record.",
        "imo": "IMO vessel identifier when available in the public source.",
        "vessel_id": "Vessel registration identifier from the public source.",
        "vessel_name": "Vessel name as reported in the public source.",
        "operation_type": "Declared operation motives for the port call, such as loading, unloading, anchorage, bunker, passenger, offshore, or maintenance.",
        "source_port": "Reported previous port code for the vessel call.",
        "source_port_name": "Reported previous port name for the vessel call.",
        "destination_port": "Reported next port code for the vessel call.",
        "destination_port_name": "Reported next port name for the vessel call.",
        DATE_COL: "Timestamp when the vessel arrived at the port; this is the prediction reference time.",
        "berthing_ts": "Timestamp when the vessel berthed after arrival.",
        "unberthing_ts": "Timestamp when the vessel unberthed after port operation.",
        "departure_port_ts": "Timestamp when the vessel departed the port.",
        "port_display": "Historical readable port label from the internal port reference; excluded from public Kaggle v1 due to manual geography provenance.",
        "port_name_ref": "Historical port name from the internal port reference used during the academic pipeline; excluded from public Kaggle v1.",
        "port_display_ref": "Historical display label from the internal port reference used during the academic pipeline; excluded from public Kaggle v1.",
        "source_port_display": "Readable label for the reported previous port.",
        "destination_port_display": "Readable label for the reported next port.",
        TARGET: "Total vessel port stay in hours, from arrival_port_ts to departure_port_ts.",
        "t_wait_for_berthing_h": "Waiting time in hours from port arrival to berthing.",
        "t_operation_h": "Operation time in hours from berthing to unberthing.",
        "t_post_operation_h": "Post-operation time in hours from unberthing to port departure.",
        "t_total_port_stay_d": "Total vessel port stay expressed in days for descriptive analysis.",
        "arrival_date": "Calendar date of arrival at the port.",
        "arrival_year": "Calendar year of arrival.",
        "arrival_month": "Calendar month of arrival.",
        "arrival_quarter": "Calendar quarter of arrival.",
        "arrival_weekofyear": "ISO week number of arrival.",
        "arrival_day": "Day of month of arrival.",
        "arrival_dayofweek": "Day of week of arrival, where Monday is 0.",
        "arrival_hour": "Hour of day of arrival.",
        "arrival_is_weekend": "Indicator equal to 1 when arrival occurred on Saturday or Sunday.",
        "arrival_shift": "Arrival shift label: night, morning, afternoon, or evening.",
        "arrival_season": "Southern Hemisphere season for the arrival month.",
        "arrival_hour_sin": "Sine encoding of arrival hour.",
        "arrival_hour_cos": "Cosine encoding of arrival hour.",
        "arrival_dow_sin": "Sine encoding of arrival day of week.",
        "arrival_dow_cos": "Cosine encoding of arrival day of week.",
        "arrival_month_sin": "Sine encoding of arrival month.",
        "arrival_month_cos": "Cosine encoding of arrival month.",
        "city": "Historical manually enriched municipality associated with the port; excluded from public Kaggle v1.",
        "state": "Brazilian state/UF for the port, reconstructed from the official PSP port reference when an exact port-code match exists.",
        "region": "Brazilian macro-region derived deterministically from the published state/UF.",
        "latitude": "Historical manually enriched latitude used internally for weather collection; excluded from public Kaggle v1.",
        "longitude": "Historical manually enriched longitude used internally for weather collection; excluded from public Kaggle v1.",
        "latitude_r": "Rounded historical latitude used internally as a weather-merge key; excluded from public Kaggle v1.",
        "longitude_r": "Rounded historical longitude used internally as a weather-merge key; excluded from public Kaggle v1.",
        "date": "Weather date joined to the arrival date.",
        "has_port_reference": "Indicator that a port reference row was found for the port code.",
        "has_weather_data": "Indicator that daily weather data were found for the port and arrival date.",
        "eligible_for_eda": "Internal quality-control indicator marking port calls that passed the academic EDA eligibility filters.",
        "split": "Official temporal split label for reproducible modeling.",
        "arrival_date_for_features": "Arrival date used internally to build D-1 historical features.",
        "cutoff_date": "Last calendar date allowed for reconstructed historical features.",
        "cutoff_ts": "Cutoff timestamp, set to 23:59:59 on D-1 for reconstructed historical features.",
    }
    if column in exact:
        return exact[column]
    if column.startswith("op_"):
        label = column.replace("op_", "").replace("_", " ")
        return f"Boolean flag indicating whether the declared operation type includes {label}."
    if column.startswith("log_"):
        base = column.replace("log_", "")
        return f"Log-transformed version of {base}, using log1p."
    if column.endswith("_d") and column.startswith("t_"):
        base = column.replace("_d", "_h")
        return f"Duration {base} expressed in days for descriptive analysis."
    if column.endswith(("_high", "_extreme")):
        base = column.rsplit("_", 1)[0]
        return f"Descriptive severity flag derived from empirical quantiles of {base}."
    if column.startswith(("temperature_", "precipitation_", "rain_", "wind_")):
        if "_prev_" in column:
            return f"Lagged historical weather measure before arrival: {column.replace('_', ' ')}."
        return f"Realized same-day weather measure for the arrival date: {column.replace('_', ' ')}."
    if column.startswith("arrivals_"):
        return f"Historical count or summary of vessel arrivals at the same port: {column.replace('_', ' ')}."
    if column.startswith("departures_"):
        return f"Historical count or summary of vessel departures at the same port: {column.replace('_', ' ')}."
    if column.startswith("flow_balance_"):
        return f"Historical arrival-minus-departure flow balance at the same port: {column.replace('_', ' ')}."
    if column.startswith("state_"):
        return f"Reconstructed operational state at the port before arrival: {column.replace('_', ' ')}."
    if column.startswith("port_") and "_known_" in column:
        return f"Historical known port performance statistic before arrival: {column.replace('_', ' ')}."
    if column.startswith("vessel_port_"):
        return f"Historical known statistic for the vessel at the same port before arrival: {column.replace('_', ' ')}."
    if column.startswith("vessel_") and "_known_" in column:
        return f"Historical known statistic for the same vessel before arrival: {column.replace('_', ' ')}."
    if column.startswith("source_") and "_known_" in column:
        return f"Historical known statistic associated with the reported previous port before arrival: {column.replace('_', ' ')}."
    if column.startswith("destination_") and "_known_" in column:
        return f"Historical known statistic associated with the reported next port before arrival: {column.replace('_', ' ')}."
    if column.startswith("route_") and "_known_" in column:
        return f"Historical known statistic for the reported source-destination route before arrival: {column.replace('_', ' ')}."
    if column.startswith("opmix_"):
        return f"Recent historical operation mix share at the same port before arrival: {column.replace('_', ' ')}."
    if column.startswith("avg_") or column.startswith("std_"):
        return f"Exploratory historical proxy from the EDA pipeline: {column.replace('_', ' ')}."
    if column.startswith("has_"):
        return f"Internal quality-control indicator for presence of {column.replace('has_', '').replace('_', ' ')}."
    if column.startswith("flag_"):
        return f"Internal quality-control flag: {column.replace('_', ' ')}."
    if column.startswith("tmp_"):
        return f"Temporary duration check used by quality control: {column.replace('_', ' ')}."
    return f"Project pipeline column: {column.replace('_', ' ')}."


def notes_for_column(column: str, role: str) -> str:
    """Return concise usage notes."""
    if role == "leakage_do_not_use":
        return "Do not use as a predictor for arrival-time modeling; retained only when useful for EDA or internal audit."
    if column in SAME_DAY_WEATHER_COLUMNS:
        return "Same-day weather can include hours after arrival."
    if column in EDA_CONGESTION_COLUMNS:
        return "Exploratory proxy superseded by reconstructed safe-history features in the model-ready dataset."
    if column in PROVENANCE_SENSITIVE_COLUMNS:
        return "Excluded from public Kaggle v1 because it depends on historical manual port-reference enrichment."
    if column == "state":
        return "Exact official PSP mapping where available; missing when no exact public port-code match was found."
    if column == "region":
        return "Derived from state; missing when state has no exact official PSP mapping."
    if role == "feature":
        return "Included in the model-ready dataset as an official arrival-time predictor."
    if role == "target":
        return "Main supervised-learning target."
    if column == DATE_COL:
        return "Prediction timestamp. Features in the model-ready dataset are interpreted relative to this instant."
    if column == "port_call_id":
        return "Taken from the public DUV field and used as the stable one-row-per-call key after deterministic grouping."
    if column == "port":
        return "Included as a structural arrival-time feature; high-cardinality modeling should be validated carefully."
    if role == "identifier":
        return "Identifier or label; use carefully in modeling."
    return ""


def build_data_dictionary(
    all_columns: list[str],
    dtypes: dict[str, str],
    analytical_cols: set[str],
    model_ready_cols: set[str],
    model_ready_features: set[str],
) -> pd.DataFrame:
    """Build the public data dictionary."""
    rows = []
    for column in all_columns:
        role = classify_column(column, model_ready_features)
        rows.append(
            {
                "column": column,
                "dtype": dtypes.get(column, "generated"),
                "description": description_for_column(column, role),
                "source": source_for_column(column),
                "transformation": transformation_for_column(column, role),
                "availability_at_prediction_time": availability(column, role),
                "modeling_role": role,
                "included_in_analytical": column in analytical_cols,
                "included_in_model_ready": column in model_ready_cols,
                "notes": notes_for_column(column, role),
            }
        )
    dictionary = pd.DataFrame(rows, columns=DATA_DICTIONARY_COLUMNS)
    if dictionary["description"].isna().any() or dictionary["description"].astype(str).str.strip().eq("").any():
        raise RuntimeError("Data dictionary contains empty descriptions.")
    return dictionary


def validate_source(df: pd.DataFrame) -> None:
    """Validate source snapshot integrity before exporting."""
    required = {"port_call_id", DATE_COL, TARGET}
    missing = sorted(required - set(df.columns))
    if missing:
        raise RuntimeError(f"Missing required source columns: {missing}")
    if len(df) != df["port_call_id"].nunique():
        raise RuntimeError("Source base must have one row per port_call_id.")
    if df[TARGET].isna().any():
        raise RuntimeError("Source base has missing target values.")
    if (df[TARGET] < 0).any():
        raise RuntimeError("Source base has negative target values.")
    outside = (df[DATE_COL] < pd.Timestamp("2023-01-01")) | (df[DATE_COL] >= pd.Timestamp("2026-01-01"))
    if outside.any():
        raise RuntimeError("Source base has arrivals outside 2023-2025.")
    if abs(len(df) - EXPECTED_ROWS) > SNAPSHOT_TOLERANCE_ROWS:
        raise RuntimeError(
            f"Source row count {len(df):,} differs materially from expected academic snapshot "
            f"({EXPECTED_ROWS:,})."
        )
    if {"state", "region"}.issubset(df.columns):
        invalid_states = sorted(set(df["state"].dropna()) - set(STATE_TO_REGION))
        if invalid_states:
            raise RuntimeError(f"Published state values contain invalid UF codes: {invalid_states}")
        expected_region = df["state"].map(STATE_TO_REGION).astype("string")
        mismatch = df["state"].notna() & df["region"].ne(expected_region)
        if mismatch.any():
            raise RuntimeError("Published region values do not match STATE_TO_REGION[state].")


def validate_model_ready(model_ready: pd.DataFrame, feature_cols: list[str], dictionary: pd.DataFrame) -> None:
    """Validate model-ready schema, splits, target, dates, and leakage exclusions."""
    required = set(MODEL_READY_BASE_COLUMNS)
    missing = sorted(required - set(model_ready.columns))
    if missing:
        raise RuntimeError(f"Missing model-ready required columns: {missing}")
    if model_ready["port_call_id"].duplicated().any():
        raise RuntimeError("Model-ready dataset contains duplicated port_call_id values.")
    if model_ready["split"].isna().any():
        raise RuntimeError("Model-ready dataset contains rows without split.")
    allowed_splits = set(SPLIT_BOUNDS)
    actual_splits = set(model_ready["split"].dropna().astype(str))
    if actual_splits != allowed_splits:
        raise RuntimeError(f"Unexpected split labels: {sorted(actual_splits)}")
    if model_ready[TARGET].isna().any() or (model_ready[TARGET] < 0).any():
        raise RuntimeError("Model-ready target must be present and non-negative.")
    forbidden_public = sorted(PROVENANCE_SENSITIVE_COLUMNS & set(model_ready.columns))
    if forbidden_public:
        raise RuntimeError(f"Provenance-sensitive columns present in model-ready output: {forbidden_public}")

    role_by_column = dictionary.set_index("column")["modeling_role"].to_dict()
    leakage_predictors = [
        col for col in feature_cols if role_by_column.get(col) == "leakage_do_not_use"
    ]
    if leakage_predictors:
        raise RuntimeError(f"Leakage columns present in model-ready predictors: {leakage_predictors}")

    for split_name, (start, end) in SPLIT_BOUNDS.items():
        part = model_ready[model_ready["split"] == split_name]
        if part.empty:
            raise RuntimeError(f"Split {split_name} is empty.")
        if not ((part[DATE_COL] >= pd.Timestamp(start)) & (part[DATE_COL] < pd.Timestamp(end))).all():
            raise RuntimeError(f"Split {split_name} contains rows outside its official interval.")


def validate_public_geography(analytical: pd.DataFrame, model_ready: pd.DataFrame) -> None:
    """Ensure manual geography is not redistributed and region follows state."""
    forbidden = {"city", "latitude", "longitude", "latitude_r", "longitude_r", "port_display"}
    for name, frame in {"analytical": analytical, "model_ready": model_ready}.items():
        leaked = sorted(forbidden & set(frame.columns))
        if leaked:
            raise RuntimeError(f"Provenance-sensitive geography leaked into {name}: {leaked}")
        if {"state", "region"}.issubset(frame.columns):
            invalid_states = sorted(set(frame["state"].dropna()) - set(STATE_TO_REGION))
            if invalid_states:
                raise RuntimeError(f"{name} contains invalid state values: {invalid_states}")
            expected = frame["state"].map(STATE_TO_REGION).astype("string")
            mapped = frame["state"].notna()
            if not frame.loc[mapped, "region"].astype("string").equals(expected.loc[mapped]):
                raise RuntimeError(f"{name} region values do not match STATE_TO_REGION[state].")
            if not frame.loc[frame["state"].isna(), "region"].isna().all():
                raise RuntimeError(f"{name} has region values where state is missing.")


def normalize_for_csv(df: pd.DataFrame) -> pd.DataFrame:
    """Prepare a deterministic UTF-8 CSV representation with ISO timestamps."""
    out = df.copy()
    for col in out.columns:
        if pd.api.types.is_datetime64_any_dtype(out[col]):
            out[col] = out[col].dt.strftime("%Y-%m-%dT%H:%M:%S")
    return out


def write_dataset(df: pd.DataFrame, output_dir: Path, name: str) -> dict[str, Any]:
    """Write CSV and Parquet versions and return file metadata."""
    csv_path = output_dir / f"{name}.csv"
    parquet_path = output_dir / f"{name}.parquet"
    normalize_for_csv(df).to_csv(csv_path, index=False, encoding="utf-8")
    df.to_parquet(parquet_path, index=False)
    validate_csv_parquet(csv_path, parquet_path)
    return {
        "csv": file_summary(csv_path),
        "parquet": file_summary(parquet_path),
    }


def validate_csv_parquet(csv_path: Path, parquet_path: Path) -> None:
    """Confirm that CSV and Parquet contain the same columns and primary records."""
    csv_df = pd.read_csv(csv_path)
    parquet_df = pd.read_parquet(parquet_path)
    if list(csv_df.columns) != list(parquet_df.columns):
        raise RuntimeError(f"CSV/Parquet column mismatch for {csv_path.name}.")
    if len(csv_df) != len(parquet_df):
        raise RuntimeError(f"CSV/Parquet row mismatch for {csv_path.name}.")
    if "port_call_id" in csv_df.columns:
        csv_ids = csv_df["port_call_id"].astype(str).tolist()
        parquet_ids = parquet_df["port_call_id"].astype(str).tolist()
        if csv_ids != parquet_ids:
            raise RuntimeError(f"CSV/Parquet primary identifier mismatch for {csv_path.name}.")


def sha256(path: Path) -> str:
    """Compute a SHA256 hash for a generated file."""
    h = hashlib.sha256()
    with path.open("rb") as fh:
        for chunk in iter(lambda: fh.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def file_summary(path: Path) -> dict[str, Any]:
    """Return size and hash metadata for a generated file."""
    return {
        "path": str(path.relative_to(ROOT)),
        "bytes": path.stat().st_size,
        "sha256": sha256(path),
    }


def build_summary(
    analytical: pd.DataFrame,
    model_ready: pd.DataFrame,
    feature_cols: list[str],
    dictionary: pd.DataFrame,
    files: dict[str, Any],
    leakage_results: pd.DataFrame,
) -> dict[str, Any]:
    """Create the JSON build summary."""
    split_counts = model_ready["split"].value_counts().reindex(list(SPLIT_BOUNDS), fill_value=0).astype(int)
    leakage_excluded = dictionary[
        dictionary["modeling_role"].eq("leakage_do_not_use")
        & ~dictionary["included_in_model_ready"]
    ]["column"].tolist()
    provenance_excluded = sorted(
        col for col in PROVENANCE_SENSITIVE_COLUMNS if col in set(dictionary["column"])
    )
    analytical_state_missing = int(analytical["state"].isna().sum()) if "state" in analytical.columns else None
    analytical_region_missing = int(analytical["region"].isna().sum()) if "region" in analytical.columns else None
    model_state_missing = int(model_ready["state"].isna().sum()) if "state" in model_ready.columns else None
    model_region_missing = int(model_ready["region"].isna().sum()) if "region" in model_ready.columns else None
    return {
        "build_timestamp_utc": datetime.now(timezone.utc).isoformat(),
        "git": {
            "branch": run_git(["branch", "--show-current"]),
            "head": run_git(["rev-parse", "HEAD"]),
            "status": run_git(["status", "--short", "--branch"]),
        },
        "target": TARGET,
        "prediction_timestamp": DATE_COL,
        "analytical": {
            "rows": int(len(analytical)),
            "columns": int(analytical.shape[1]),
            "date_min": str(analytical[DATE_COL].min()),
            "date_max": str(analytical[DATE_COL].max()),
            "missing_target": int(analytical[TARGET].isna().sum()),
            "state_missing_rows": analytical_state_missing,
            "region_missing_rows": analytical_region_missing,
        },
        "model_ready": {
            "rows": int(len(model_ready)),
            "columns": int(model_ready.shape[1]),
            "features": int(len(feature_cols)),
            "date_min": str(model_ready[DATE_COL].min()),
            "date_max": str(model_ready[DATE_COL].max()),
            "state_missing_rows": model_state_missing,
            "region_missing_rows": model_region_missing,
            "split_counts": split_counts.to_dict(),
        },
        "checks": {
            "source_schema": "passed",
            "snapshot_row_count": "passed",
            "unique_port_calls": "passed",
            "target_non_negative": "passed",
            "temporal_range_2023_2025": "passed",
            "split_complete": "passed",
            "csv_parquet_consistency": "passed",
            "historical_context_leakage_tests": "passed" if leakage_results["passed"].all() else "failed",
            "model_ready_leakage_exclusion": "passed",
        },
        "leakage_columns_excluded": leakage_excluded,
        "excluded_from_publication_due_to_provenance": provenance_excluded,
        "data_dictionary_rows": int(len(dictionary)),
        "files": files,
    }


def print_report(
    analytical: pd.DataFrame,
    model_ready: pd.DataFrame,
    feature_cols: list[str],
    dictionary: pd.DataFrame,
    files: dict[str, Any],
) -> None:
    """Print the final build report expected by local reviewers."""
    split_counts = model_ready["split"].value_counts().reindex(list(SPLIT_BOUNDS), fill_value=0).astype(int)
    leakage_excluded = dictionary[
        dictionary["modeling_role"].eq("leakage_do_not_use")
        & ~dictionary["included_in_model_ready"]
    ]["column"].tolist()
    print()
    print("Kaggle dataset build complete.")
    print(f"Total rows: {len(analytical):,}")
    print(f"Total columns: analytical={analytical.shape[1]:,}; model_ready={model_ready.shape[1]:,}")
    print(f"Unique port calls: {analytical['port_call_id'].nunique():,}")
    print(f"Date range: {analytical[DATE_COL].min()} to {analytical[DATE_COL].max()}")
    print(f"Missing target: {analytical[TARGET].isna().sum():,}")
    print(f"Duplicated primary identifiers: {analytical['port_call_id'].duplicated().sum():,}")
    print(f"Train rows: {split_counts['train']:,}")
    print(f"Validation rows: {split_counts['validation']:,}")
    print(f"Calibration rows: {split_counts['calibration']:,}")
    print(f"Final-test rows: {split_counts['final_test']:,}")
    print(f"Features included: {len(feature_cols):,}")
    print(f"EDA-only columns: {(dictionary['modeling_role'] == 'eda_only').sum():,}")
    print(f"Leakage columns excluded: {len(leakage_excluded):,}")
    print()
    print("Generated files:")
    for view in files.values():
        for meta in view.values():
            print(f"- {meta['path']} ({meta['bytes']:,} bytes, sha256={meta['sha256'][:12]}...)")


def main() -> int:
    """Build all local Kaggle files without publishing anything remotely."""
    output_dir = ROOT / "kaggle" / "dataset" / "output"
    output_dir.mkdir(parents=True, exist_ok=True)

    source = load_source_base()
    validate_source(source)

    analytical = source[analytical_columns(source)].copy()
    model_ready, feature_cols, registry_info = build_model_ready(source)

    all_columns = list(dict.fromkeys([*source.columns, *model_ready.columns]))
    dtypes = {column: str(dtype) for column, dtype in source.dtypes.items()}
    dtypes.update({column: str(dtype) for column, dtype in model_ready.dtypes.items()})
    dictionary = build_data_dictionary(
        all_columns=all_columns,
        dtypes=dtypes,
        analytical_cols=set(analytical.columns),
        model_ready_cols=set(model_ready.columns),
        model_ready_features=set(feature_cols),
    )
    validate_model_ready(model_ready, feature_cols, dictionary)
    validate_public_geography(analytical, model_ready)

    leakage_results = run_leakage_tests()
    if not leakage_results["passed"].all():
        failures = leakage_results.loc[~leakage_results["passed"]].to_dict("records")
        raise RuntimeError(f"Historical-context leakage tests failed: {failures}")

    dictionary_path = ROOT / "kaggle" / "dataset" / "data_dictionary.csv"
    dictionary.to_csv(dictionary_path, index=False, encoding="utf-8")

    files = {
        "analytical": write_dataset(analytical, output_dir, ANALYTICAL_NAME),
        "model_ready": write_dataset(model_ready, output_dir, MODEL_READY_NAME),
        "data_dictionary": {"csv": file_summary(dictionary_path)},
    }

    summary = build_summary(analytical, model_ready, feature_cols, dictionary, files, leakage_results)
    summary["registry"] = {
        "original_feature_count": len(registry_info["original_features"]),
        "enriched_feature_count": len(registry_info["enriched_features"]),
        "historical_families": registry_info["historical_families"],
    }
    summary_path = output_dir / "dataset_build_summary.json"
    summary_path.write_text(json.dumps(summary, indent=2, default=str), encoding="utf-8")
    files["summary"] = {"json": file_summary(summary_path)}
    print_report(analytical, model_ready, feature_cols, dictionary, files)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
