# Kaggle Notebooks

This folder contains public notebooks intended for the single-file Kaggle dataset:

https://www.kaggle.com/datasets/tiagoalberione/brazilian-port-lead-time-2023-2025

## Available Notebooks

```text
01_brazilian_port_lead_time_eda_baseline.ipynb
02_brazilian_port_lead_time_quantile_uncertainty.ipynb
03_brazilian_port_lead_time_safety_stock.ipynb
```

Titles:

```text
Brazilian Port Lead Time CSV Baseline
Brazilian Port Lead Time Quantile Uncertainty
Brazilian Port Lead Time Safety Stock Application
```

Public Kaggle URLs:

- https://www.kaggle.com/code/tiagoalberione/brazilian-port-lead-time-csv-baseline
- https://www.kaggle.com/code/tiagoalberione/brazilian-port-lead-time-quantile-uncertainty
- https://www.kaggle.com/code/tiagoalberione/brazilian-port-lead-time-safety-stock-application

## Objective

Notebook 01 is the recommended entry point for users of the public dataset. It introduces the unit of observation, target, official temporal splits, leakage-aware modeling rule, concise exploratory analysis, a global-median baseline, and one simple `HistGradientBoostingRegressor` machine-learning baseline.

Notebook 02 extends the public baseline from point prediction to quantile regression. It explains P50, P90, and P95 lead-time estimates, checks empirical coverage, diagnoses quantile crossing, and analyzes prediction-uncertainty width without introducing safety-stock or working-capital simulation.

Notebook 03 translates the quantile estimates into an illustrative safety-stock and working-capital proxy scenario. It is a planning example, not a measurement of realized financial savings or actual company inventory performance.

## Dataset Dependency

The notebook is designed to run on Kaggle with the published dataset attached. The public Kaggle dataset exposes one CSV file:

```text
brazilian_port_calls_model_ready_2023_2025.csv
```

For local development, the notebook can also resolve the generated CSV under:

```text
kaggle/dataset/output/
```

Repository documentation files such as `kaggle/SOURCES.md`, `kaggle/DATA_DICTIONARY.md`, and `kaggle/dataset/data_dictionary.csv` remain in GitHub for auditability, but they are not runtime dependencies of the public notebook.

## Modeling Scope

The notebooks are intentionally small and educational. They do not reproduce the full thesis workflow and do not run hyperparameter searches. The safety-stock notebook uses simulated demand/value assumptions and does not claim observed inventory, service-level, or working-capital outcomes.

## Leakage Policy

The models use only columns present in the model-ready CSV after excluding `port_call_id`, `arrival_port_ts`, `t_total_port_stay_h`, and `split`. They keep `final_test` untouched until the final locked evaluation.

## Further Work

Later public work may add deeper scenario variants, but the initial public notebook series is complete with EDA, quantile uncertainty, and one illustrative supply-chain application.
