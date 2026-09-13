# Port Lead Time Prediction

This repository contains the reproducible academic workflow for predicting vessel port stay duration in Brazilian ports. The project was developed as part of an MBA thesis in Artificial Intelligence and Big Data at the University of Sao Paulo (USP).

The repository is not a production system, API, or operational forecasting service. It is a transparent research project intended to make the data preparation, exploratory analysis, modeling choices, and final thesis results auditable.

## Overview

The goal is to estimate, at the moment a vessel arrives at a port, how long it will remain in port until departure.

- Main target: `t_total_port_stay_h`.
- Target unit: hours.
- Prediction timestamp: `arrival_port_ts`.
- Central anti-leakage rule: a feature can only be used if it is available at arrival time, or can be reconstructed exclusively from information known before that point.

## Motivation

Port stay time is a relevant component of maritime lead time. Better estimates of its uncertainty can support supply chain planning, service-level discussions, and scenario analysis for safety stock and working capital. In this project, the connection to inventory is treated as a simulation exercise, not as observed financial savings.

## Dataset

The local files under `data/raw/` and `data/downloaded/` come mainly from Brazilian public data related to Porto Sem Papel, plus port reference data and daily weather variables used for descriptive and historical enrichment.

The analytical snapshot used by the thesis covers:

- 129,625 eligible port calls;
- arrivals from 2023-01-01 through 2025-12-31;
- 126 columns in `data/processed/eda_base.parquet` after reconstruction.

Main sources and inputs:

- vessel stay records;
- Documento Unico Virtual (DUV), preserved as raw historical material;
- shipping agency reference files, preserved as raw historical material;
- port reference files;
- daily weather files.

The public source URLs used during the project are listed in `data/downloaded/urls.txt`. See `data/README.md` for the data policy and regeneration notes.

## Methodology

The workflow follows the thesis structure:

1. Read raw public data from `data/raw/`.
2. Clean timestamps and standardize source columns.
3. Consolidate one analytical row per port call.
4. Apply quality filters and remove incomplete, temporally inconsistent, or extreme records.
5. Create duration targets, including `t_total_port_stay_h`.
6. Add calendar, operation-type, port, weather, and historical-context features.
7. Use chronological train, validation, calibration, and final test splits.
8. Compare baselines and regression models.
9. Train quantile models for P50, P90, and P95.
10. Analyze tail behavior and uncertainty width.
11. Run a safety-stock and working-capital proxy simulation.

The official temporal split for Chapter 4 is:

- train: 2023-01-01 to before 2024-07-01;
- validation: 2024-07-01 to before 2025-01-01;
- calibration/development: 2025-01-01 to before 2025-07-01;
- final test: 2025-07-01 to before 2026-01-01.

Intervals are implemented as half-open ranges. The final test period is not used for model or hyperparameter selection.

## Main Results

The final point-model comparison is preserved in `results/cap4_rebuild/point_model_comparison_final.csv` and `results/cap4_notebook_run/final_comparison.csv`.

The main final result preserved by the audited artifacts is:

- HistGradientBoosting with temporally safe historical features: final-test MAE of approximately 38.35 hours.
- HistGradientBoosting with the original feature set: final-test MAE of approximately 41.67 hours.

Quantile regression artifacts are available in:

- `results/cap4_rebuild/quantile_model_comparison.csv`;
- `results/cap4_rebuild/quantile_coverage.csv`;
- `results/cap4_notebook_run/quantile_comparison.csv`;
- `results/cap4_notebook_run/quantile_coverage.csv`.

The safety-stock simulation is preserved in:

- `results/cap4_rebuild/safety_stock_simulation.csv`;
- `results/cap4_notebook_run/safety_stock_simulation.csv`.

These outputs should be read as academic scenario analysis. The dataset does not contain real item demand, unit cost, inventory, or full logistics lead time.

## Repository Structure

```text
data/
  raw/                  Raw inputs expected by the preparation pipeline
  downloaded/           Downloaded source files and source URL references
  interim/              Generated intermediate datasets, ignored by Git
  processed/            Generated analytical dataset, ignored by Git
notebooks/
  01_eda_cap3_final.ipynb
  02_modeling_cap4_final.ipynb
pipelines/
  build_eda_base.py     Rebuilds the analytical dataset
scripts/
  run_cap4_rebuild.py   Canonical heavy rebuild of Chapter 4 artifacts
src/                    Data preparation and feature engineering code
results/                Tracked numerical artifacts used to audit thesis results
outputs/                Generated figures and tables, ignored by Git
tests/                  Smoke and anti-leakage tests
```

## Installation

The audited environment used Python 3.11.

```bash
conda create -n mbausp python=3.11
conda activate mbausp
pip install -r requirements.txt
```

You can also run commands through conda without activating the environment:

```bash
conda run -n mbausp python --version
```

## Running The Project

Rebuild the analytical dataset:

```bash
conda run -n mbausp python pipelines/build_eda_base.py
```

Expected main output:

```text
data/processed/eda_base.parquet
```

Run the lightweight validation suite:

```bash
conda run -n mbausp python -m pytest -q
```

The official notebooks are:

- `notebooks/01_eda_cap3_final.ipynb`: final Chapter 3 exploratory analysis.
- `notebooks/02_modeling_cap4_final.ipynb`: final Chapter 4 modeling, quantile regression, uncertainty analysis, and safety-stock simulation.

The canonical script below preserves the heavier historical rebuild used to generate the tracked `results/cap4_rebuild/` artifacts:

```bash
conda run -n mbausp python scripts/run_cap4_rebuild.py
```

## Reproducibility

All project paths are relative to the repository root. Generated folders are created by the pipeline when needed.

Tracked raw data are included to preserve the academic snapshot. Intermediate files, processed datasets, model binaries, local outputs, notebook checkpoints, and Python caches are ignored because they can be regenerated or are too environment-specific.

The tracked `results/` files are intentionally kept because they document the numerical evidence used in the final thesis review.

## Limitations

- The public data sources may change their download format or availability over time.
- The project models port stay duration, not the complete end-to-end logistics lead time.
- Operation-type flags are treated as known at arrival time as a modeling premise.
- Weather variables from the arrival day are useful for EDA but are not used as substantive final predictors unless reconstructed as lagged historical information.
- The safety-stock and working-capital analysis is a scenario simulation, not an observed company result.
- The workflow is designed for academic reproducibility, not for low-latency production inference.

## Future Work

Potential extensions include updating the public-data download process, adding a cleaner data-release strategy for large files, testing the workflow in a fresh CI environment, and comparing the port-stay proxy with complete logistics lead-time data if such data become available.

## License

Code in this repository is released under the MIT License. Data files remain subject to the terms and availability of their original public sources. See `LICENSE` and `data/README.md`.

## Citation

If you use this project, cite it through `CITATION.cff` or with:

```text
Alberione, T. Port Lead Time Prediction: vessel port stay modeling for Brazilian public port data. MBA thesis project, University of Sao Paulo, 2026.
```
