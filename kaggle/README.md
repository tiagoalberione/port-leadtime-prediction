# Kaggle Data Release Preparation

This folder prepares a local Kaggle-ready data package for the public repository. It does not publish anything to Kaggle and does not create a remote dataset.

## What Will Be Published

The future Kaggle upload should contain the generated files under `kaggle/dataset/output/`:

- `brazilian_port_calls_analytical_2023_2025.csv`
- `brazilian_port_calls_analytical_2023_2025.parquet`
- `brazilian_port_calls_model_ready_2023_2025.csv`
- `brazilian_port_calls_model_ready_2023_2025.parquet`
- `dataset_build_summary.json`

The repository tracks the build script, metadata, source notes, and data dictionary. The generated output folder is intentionally ignored by Git.

## Dataset Views

The analytical dataset is a cleaned port-call table for EDA, statistical analysis, lead-time exploration, and feature ideation. It has 95 columns. It may include post-arrival timestamps, realized durations, and same-day realized weather variables. Those columns are documented and must not be treated as arrival-time predictors.

The model-ready dataset is for supervised machine learning. It has 124 columns: `port_call_id`, `arrival_port_ts`, the official target `t_total_port_stay_h`, the official temporal `split`, and 120 predictors from the Chapter 4 `ENRICHED_SAFE_HISTORY` feature registry.

The model-ready dataset is not simply a subset of the analytical dataset. It excludes analytical columns that would leak future information and adds reconstructed historical features created specifically for leakage-safe modeling.

## Geographic Data Provenance

Public Kaggle outputs do not redistribute the manually enriched `city`, `latitude`, or `longitude` fields from the historical `data/raw/ports/port.csv` file. Those coordinates were used internally during the academic weather-enrichment process, but they are not published in the Kaggle v1 files.

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

If `data/processed/eda_base.parquet` is missing, the script rebuilds it through `pipelines/build_eda_base.py` before creating the Kaggle files.

## Validate

Run:

```bash
conda run -n port-leadtime python -m pytest -q
```

The build script also validates row counts, schema, temporal ranges, target values, duplicated identifiers, split completeness, CSV-Parquet consistency, and anti-leakage guards.

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

For a future dataset version, update raw source snapshots only after documenting source changes, rebuild `data/processed/eda_base.parquet`, rerun the Kaggle build script and tests, review `dataset_build_summary.json`, and verify source-license compatibility before any Kaggle publication.

## License Review

Code remains MIT. The dataset license is separate. With manual Google Maps-derived geography removed from the public outputs, CC BY 4.0 is the recommended dataset license, provided attribution is maintained for Porto Sem Papel / Ministerio de Portos e Aeroportos and Open-Meteo.
