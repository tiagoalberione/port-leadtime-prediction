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

Port stay time is a relevant component of maritime lead time. Better estimates of its uncertainty can support supply chain planning, service-level discussions, and scenario analysis for safety stock and working capital.

In this project, the connection to inventory is treated as a simulation exercise, not as observed financial savings.

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

### Public Kaggle Dataset

A cleaned and documented public release of the processed dataset is available on Kaggle:

https://www.kaggle.com/datasets/tiagoalberione/brazilian-port-calls-lead-time-2023-2025

The Kaggle release provides two complementary views:

- **Analytical dataset:** intended for exploratory data analysis, descriptive statistics, and broader research use.
- **Model-ready dataset:** contains arrival-time-safe predictors, the target variable, and the official temporal split used by the modeling workflow.

Both datasets are available in CSV and Parquet formats.

The release also includes:

- a machine-readable data dictionary;
- source and provenance documentation;
- build metadata;
- the official train, validation, calibration, and final-test split;
- explicit documentation of leakage-sensitive variables.

The public Kaggle release is intentionally different from the full historical academic snapshot. Geography fields derived manually during the original research were not redistributed. State information was reconstructed from an official public port reference, region was derived deterministically from state, and municipality and manually researched coordinates were excluded from the public dataset.

See:

- `kaggle/README.md`
- `kaggle/SOURCES.md`
- `kaggle/DATA_DICTIONARY.md`
- `kaggle/dataset/data_dictionary.csv`

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

kaggle/
  README.md              Kaggle release overview and build instructions
  SOURCES.md             Source provenance and licensing review
  DATA_DICTIONARY.md     Documentation for the machine-readable dictionary
  dataset/
    README.md            Dataset-specific documentation
    data_dictionary.csv  Machine-readable field documentation
    output/              Generated Kaggle datasets, ignored by Git
  reference/             Public reference data used for redistribution
  notebooks/             Notes and support files for future Kaggle notebooks

notebooks/
  01_eda_cap3_final.ipynb
  02_modeling_cap4_final.ipynb

pipelines/
  build_eda_base.py      Rebuilds the analytical dataset

scripts/
  run_cap4_rebuild.py    Canonical heavy rebuild of Chapter 4 artifacts
  build_kaggle_dataset.py
                         Builds and validates the public Kaggle dataset package

src/                     Data preparation and feature engineering code
results/                 Tracked numerical artifacts used to audit thesis results
outputs/                 Generated figures and tables, ignored by Git
tests/                   Smoke, reproducibility, and anti-leakage tests
```

## Installation

The audited environment uses Python 3.11.

Create a dedicated environment:

```bash
conda create -n port-leadtime python=3.11
conda activate port-leadtime
pip install -r requirements.txt
```

You can also run commands through Conda without activating the environment:

```bash
conda run -n port-leadtime python --version
```

## Running the Project

### Rebuild the analytical dataset

```bash
conda run -n port-leadtime python pipelines/build_eda_base.py
```

Expected main output:

```text
data/processed/eda_base.parquet
```

### Run the validation suite

```bash
conda run -n port-leadtime python -m pytest -q
```

### Run the thesis notebooks

The official notebooks are:

- `notebooks/01_eda_cap3_final.ipynb`: final Chapter 3 exploratory analysis.
- `notebooks/02_modeling_cap4_final.ipynb`: final Chapter 4 modeling, quantile regression, uncertainty analysis, and safety-stock simulation.

### Rebuild the Chapter 4 artifacts

The canonical script below preserves the heavier historical rebuild used to generate the tracked `results/cap4_rebuild/` artifacts:

```bash
conda run -n port-leadtime python scripts/run_cap4_rebuild.py
```

### Build the public Kaggle dataset

The public analytical and model-ready datasets can be regenerated with:

```bash
conda run -n port-leadtime python scripts/build_kaggle_dataset.py
```

Generated files are written under:

```text
kaggle/dataset/output/
```

The generated output directory is intentionally ignored by Git because the published dataset is hosted on Kaggle.

For release-specific documentation, provenance, feature definitions, and licensing notes, see the `kaggle/` directory.

## Reproducibility

All project paths are relative to the repository root. Generated folders are created by the pipeline when needed.

Tracked raw data are included to preserve the academic snapshot. Intermediate files, processed datasets, model binaries, local outputs, notebook checkpoints, and Python caches are ignored because they can be regenerated or are too environment-specific.

The tracked `results/` files are intentionally kept because they document the numerical evidence used in the final thesis review.

The public Kaggle release preserves the core analytical population, target definition, official temporal split, weather enrichment, and temporally safe historical-feature logic, while applying additional redistribution and provenance safeguards to selected geographic attributes.

For this reason, the Kaggle release should be treated as the recommended public dataset for reuse, while the repository preserves the broader academic workflow and historical reproducibility context.

## Limitations

- The public data sources may change their download format or availability over time.
- The project models port stay duration, not the complete end-to-end logistics lead time.
- Operation-type flags are treated as known at arrival time as a modeling premise.
- Weather variables from the arrival day are useful for EDA but are not used as substantive final predictors unless reconstructed as lagged historical information.
- Historical aggregate features must respect temporal availability and are generated using walk-forward logic.
- The safety-stock and working-capital analysis is a scenario simulation, not an observed company result.
- The workflow is designed for academic reproducibility, not for low-latency production inference.
- A small number of port calls in the public Kaggle dataset do not receive `state` and `region` values because their port codes do not have an exact match in the official public reference. No fuzzy or manual matching is applied in the public release.

## Future Work

Potential extensions include:

- publishing reproducible Kaggle notebooks for EDA and baseline modeling;
- evaluating additional regression and probabilistic modeling approaches;
- updating the public-data snapshot as new years become available;
- improving automated source ingestion and validation;
- evaluating calibration and uncertainty estimation techniques beyond the current quantile-regression workflow;
- comparing the port-stay proxy with complete logistics lead-time data if such data become available.

## License

Project code is released under the MIT License.

The public Kaggle dataset is distributed under CC BY 4.0:

https://www.kaggle.com/datasets/tiagoalberione/brazilian-port-calls-lead-time-2023-2025

Original public data sources remain subject to their respective terms, attribution requirements, and availability.

See `kaggle/SOURCES.md` for the detailed provenance and source-specific licensing review used for the public dataset release.

## Citation

If you use this project, cite it through `CITATION.cff` or with:

```text
Alberione, T. Port Lead Time Prediction: vessel port stay modeling for Brazilian public port data. MBA thesis project, University of Sao Paulo, 2026.
```

When using the public dataset, please also cite the Kaggle dataset page and preserve the source attribution described in `kaggle/SOURCES.md`.
