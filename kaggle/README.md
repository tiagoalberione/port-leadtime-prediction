# Kaggle Published Data Release

This folder documents the published Kaggle data release and the local tooling used to rebuild and validate it. The repository does not upload to Kaggle automatically.

## Published Kaggle Dataset

The current public Kaggle dataset is:

- `brazilian_port_calls_model_ready_2023_2025.csv`

https://www.kaggle.com/datasets/tiagoalberione/brazilian-port-lead-time-2023-2025

The Kaggle dataset intentionally contains exactly one public data file: a leakage-aware model-ready CSV with 129,625 rows, 124 columns, and 120 predictors. Detailed documentation stays in GitHub through this directory, including source notes, field documentation, metadata generation, and leakage/provenance review.

The local build may create additional artifacts under `kaggle/dataset/output/`, including analytical, Parquet, and JSON summary files. Those files are used for local validation and historical reproducibility; they are not part of the current Kaggle upload.

## Dataset Views

The published model-ready dataset is for supervised machine learning. It has 124 columns: `port_call_id`, `arrival_port_ts`, the official target `t_total_port_stay_h`, the official temporal `split`, and 120 predictors from the Chapter 4 `ENRICHED_SAFE_HISTORY` feature registry.

The repository can also generate a local analytical artifact for EDA, statistical analysis, lead-time exploration, and feature ideation. That local artifact may include post-arrival timestamps, realized durations, and same-day realized weather variables, and those columns must not be treated as arrival-time predictors. It is not a current Kaggle data file.

The model-ready dataset is not simply a subset of the local analytical artifact. It excludes analytical columns that would leak future information and adds reconstructed historical features created specifically for leakage-safe modeling.

## Geographic Data Provenance

The published Kaggle CSV does not redistribute the manually enriched `city`, `latitude`, or `longitude` fields from the historical `data/raw/ports/port.csv` file. Those coordinates were used internally during the academic weather-enrichment process, but they are not published in the current Kaggle file.

Published `state` is reconstructed by exact port-code joins against the official `Portos no Porto Sem Papel - PSP` public reference where available. Published `region` is derived deterministically from `state` through a Brazilian UF-to-macro-region mapping. `city` is omitted from Kaggle v1 because no compatible exact code-level public mapping was incorporated in this release.

In this snapshot, 534 of 129,625 port calls, approximately 0.41%, do not have published `state` or `region` values because their port codes did not have an exact match in the official PSP port reference. No fuzzy or manual matching was applied.

Weather features remain published as Open-Meteo data-derived variables. The provenance chain is: historical internal port coordinates were used to query weather; Open-Meteo historical weather data were collected; only weather values and lagged weather features are redistributed, not the coordinates.

## Reproducibility Note

The Kaggle version preserves the official target, temporal splits, Open-Meteo weather values, and leakage-safe historical feature logic used for public reuse. Public geographic attributes were sanitized for provenance: coordinates and manual municipality values are excluded, `state` is rebuilt from the official PSP reference when an exact code match exists, and `region` is derived from `state`. Because of that sanitization, the public geographic attributes may differ from the historical thesis feature matrix for a small share of records. For exact reproduction of the academic environment, use the academic snapshot/tag `v1.0.0-tcc`.

## Build Locally

From the repository root:

```bash
conda run -n port-leadtime python scripts/build_kaggle_dataset.py
```

If `data/processed/eda_base.parquet` is missing, the script rebuilds it through `pipelines/build_eda_base.py` before creating the local Kaggle build outputs.

## Validate

Run:

```bash
conda run -n port-leadtime python -m pytest -q
```

The build script also validates row counts, schema, temporal ranges, target values, duplicated identifiers, split completeness, local CSV-Parquet consistency, and anti-leakage guards. The CSV-Parquet check is local validation only; the published Kaggle dataset contains the CSV.

## Official Splits

Splits use half-open intervals based on `arrival_port_ts`:

- `train`: 2023-01-01 <= arrival < 2024-07-01
- `validation`: 2024-07-01 <= arrival < 2025-01-01
- `calibration`: 2025-01-01 <= arrival < 2025-07-01
- `final_test`: 2025-07-01 <= arrival < 2026-01-01

The final test period must not be used for feature selection, model selection, or configuration decisions.

For development that aims to remain comparable with the original study, use `train`, `validation`, and `calibration` for model development and keep `final_test` as the official holdout.

## Leakage Protection

The prediction timestamp is `arrival_port_ts`. A model-ready feature is allowed only when it is available at vessel arrival or can be reconstructed exclusively from information known before that instant. Historical operational features use the existing D-1 cutoff implementation and the permanent `run_leakage_tests` checks from `src.features.historical_context`.

## Temporal Semantics of Historical Features

Historical features in the model-ready dataset are precomputed in chronological, walk-forward semantics. For a vessel arriving on day D, operational history is cut at 23:59:59 on D-1. Earlier calls contribute to historical statistics only after the event that makes the statistic known: waiting time after berthing, operation time after unberthing, and total port stay after departure.

This means the features may incorporate outcomes from previous port calls that had already concluded before the relevant cutoff. That simulates continuous operational updating over time without using the current call's future events or later calls.

## Future Updates

For a future dataset version, update raw source snapshots only after documenting source changes, rebuild `data/processed/eda_base.parquet`, rerun the Kaggle build script and tests, review local build summaries, and verify source-license compatibility before publishing a new Kaggle version.

## License Review

Code remains MIT. The dataset license is separate. With manual Google Maps-derived geography removed from the public outputs, CC BY 4.0 is the recommended dataset license, provided attribution is maintained for Porto Sem Papel / Ministerio de Portos e Aeroportos and Open-Meteo.
