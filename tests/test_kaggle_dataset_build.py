import json
from pathlib import Path

import pandas as pd
import pytest

from scripts.build_kaggle_dataset import (
    DATE_COL,
    MODEL_READY_NAME,
    PROVENANCE_SENSITIVE_COLUMNS,
    STATE_TO_REGION,
    SPLIT_BOUNDS,
    TARGET,
    assign_split,
    classify_column,
)


ROOT = Path(__file__).resolve().parents[1]
OUTPUT_DIR = ROOT / "kaggle" / "dataset" / "output"
DICTIONARY_PATH = ROOT / "kaggle" / "dataset" / "data_dictionary.csv"
SUMMARY_PATH = OUTPUT_DIR / "dataset_build_summary.json"


def test_assign_split_boundaries():
    df = pd.DataFrame(
        {
            DATE_COL: pd.to_datetime(
                [
                    "2023-01-01 00:00:00",
                    "2024-06-30 23:59:59",
                    "2024-07-01 00:00:00",
                    "2025-01-01 00:00:00",
                    "2025-07-01 00:00:00",
                    "2025-12-31 23:59:59",
                    "2026-01-01 00:00:00",
                ]
            )
        }
    )
    assert assign_split(df).astype("object").tolist() == [
        "train",
        "train",
        "validation",
        "calibration",
        "final_test",
        "final_test",
        pd.NA,
    ]


def test_known_leakage_columns_are_not_features():
    model_ready_features = {"port", "arrival_hour_sin"}
    leakage_cols = [
        "berthing_ts",
        "unberthing_ts",
        "departure_port_ts",
        "t_wait_for_berthing_h",
        "log_t_total_port_stay_h",
        "temperature_2m_mean",
        "arrivals_same_day_port",
        "avg_wait_prev_20_calls_port",
    ]
    assert all(
        classify_column(col, model_ready_features) == "leakage_do_not_use"
        for col in leakage_cols
    )


def test_generated_data_dictionary_schema_if_built():
    if not DICTIONARY_PATH.exists():
        pytest.skip("Kaggle data dictionary has not been built yet.")
    dictionary = pd.read_csv(DICTIONARY_PATH)
    required = {
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
    }
    assert required.issubset(dictionary.columns)
    assert not dictionary["description"].fillna("").str.strip().eq("").any()
    assert TARGET in set(dictionary["column"])
    assert dictionary.loc[dictionary["column"].eq(TARGET), "modeling_role"].iloc[0] == "target"


def test_model_ready_output_schema_target_dates_and_splits_if_built():
    path = OUTPUT_DIR / f"{MODEL_READY_NAME}.parquet"
    if not path.exists():
        pytest.skip("Model-ready Kaggle dataset has not been built yet.")
    df = pd.read_parquet(path)
    assert {"port_call_id", DATE_COL, TARGET, "split"}.issubset(df.columns)
    assert df["port_call_id"].is_unique
    assert df[TARGET].notna().all()
    assert (df[TARGET] >= 0).all()
    assert ((df[DATE_COL] >= "2023-01-01") & (df[DATE_COL] < "2026-01-01")).all()
    assert set(df["split"]) == set(SPLIT_BOUNDS)
    for split, (start, end) in SPLIT_BOUNDS.items():
        part = df[df["split"] == split]
        assert not part.empty
        assert ((part[DATE_COL] >= start) & (part[DATE_COL] < end)).all()


def test_model_ready_excludes_dictionary_leakage_if_built():
    path = OUTPUT_DIR / f"{MODEL_READY_NAME}.parquet"
    if not path.exists() or not DICTIONARY_PATH.exists():
        pytest.skip("Kaggle outputs have not been built yet.")
    df = pd.read_parquet(path)
    dictionary = pd.read_csv(DICTIONARY_PATH)
    leakage_cols = set(
        dictionary.loc[
            dictionary["modeling_role"].eq("leakage_do_not_use"),
            "column",
        ]
    )
    predictors = set(df.columns) - {"port_call_id", DATE_COL, TARGET, "split"}
    assert predictors.isdisjoint(leakage_cols)


def test_model_ready_csv_parquet_consistency_if_built():
    csv_path = OUTPUT_DIR / f"{MODEL_READY_NAME}.csv"
    parquet_path = OUTPUT_DIR / f"{MODEL_READY_NAME}.parquet"
    if not csv_path.exists() or not parquet_path.exists():
        pytest.skip("Kaggle outputs have not been built yet.")
    csv_df = pd.read_csv(csv_path)
    parquet_df = pd.read_parquet(parquet_path)
    assert list(csv_df.columns) == list(parquet_df.columns)
    assert len(csv_df) == len(parquet_df)
    assert csv_df["port_call_id"].astype(str).tolist() == parquet_df["port_call_id"].astype(str).tolist()


def test_public_outputs_exclude_manual_geography_if_built():
    analytical_path = OUTPUT_DIR / "brazilian_port_calls_analytical_2023_2025.parquet"
    model_ready_path = OUTPUT_DIR / f"{MODEL_READY_NAME}.parquet"
    if not analytical_path.exists() or not model_ready_path.exists():
        pytest.skip("Kaggle outputs have not been built yet.")
    analytical = pd.read_parquet(analytical_path)
    model_ready = pd.read_parquet(model_ready_path)
    forbidden = {"city", "latitude", "longitude", "latitude_r", "longitude_r", "port_display"}
    assert forbidden.isdisjoint(analytical.columns)
    assert forbidden.isdisjoint(model_ready.columns)
    predictors = set(model_ready.columns) - {"port_call_id", DATE_COL, TARGET, "split"}
    assert {"latitude", "longitude"}.isdisjoint(predictors)
    assert forbidden.issubset(PROVENANCE_SENSITIVE_COLUMNS)


def test_published_state_and_region_are_officially_mapped_if_built():
    analytical_path = OUTPUT_DIR / "brazilian_port_calls_analytical_2023_2025.parquet"
    model_ready_path = OUTPUT_DIR / f"{MODEL_READY_NAME}.parquet"
    if not analytical_path.exists() or not model_ready_path.exists():
        pytest.skip("Kaggle outputs have not been built yet.")
    for path in [analytical_path, model_ready_path]:
        df = pd.read_parquet(path)
        assert {"state", "region"}.issubset(df.columns)
        assert set(df["state"].dropna()).issubset(STATE_TO_REGION)
        expected = df["state"].map(STATE_TO_REGION).astype("string")
        mapped = df["state"].notna()
        assert df.loc[mapped, "region"].astype("string").equals(expected.loc[mapped])
        assert df.loc[df["state"].isna(), "region"].isna().all()


def test_build_summary_reports_missing_public_geography_if_built():
    if not SUMMARY_PATH.exists():
        pytest.skip("Kaggle build summary has not been built yet.")
    summary = json.loads(SUMMARY_PATH.read_text(encoding="utf-8"))
    for view in ["analytical", "model_ready"]:
        assert "state_missing_rows" in summary[view]
        assert "region_missing_rows" in summary[view]
        assert summary[view]["state_missing_rows"] == summary[view]["region_missing_rows"]
