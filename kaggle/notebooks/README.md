# Kaggle Notebooks

This folder contains public notebooks intended for the single-file Kaggle dataset:

https://www.kaggle.com/datasets/tiagoalberione/brazilian-port-lead-time-2023-2025

## Available Notebook

```text
01_brazilian_port_lead_time_eda_baseline.ipynb
```

Title:

```text
Brazilian Port Lead Time - EDA and Leakage-Aware Baseline Modeling
```

## Objective

This first notebook is the recommended entry point for users of the public dataset. It introduces the unit of observation, target, official temporal splits, leakage-aware modeling rule, concise exploratory analysis, a global-median baseline, and one simple `HistGradientBoostingRegressor` machine-learning baseline.

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

The notebook is intentionally small and educational. It does not reproduce the full thesis workflow, does not run hyperparameter searches, and does not include quantile regression, uncertainty analysis, or safety-stock simulation.

## Leakage Policy

The model uses only columns present in the model-ready CSV after excluding `port_call_id`, `arrival_port_ts`, `t_total_port_stay_h`, and `split`. It keeps `final_test` untouched until the final locked evaluation.

## Future Notebooks

Later public notebooks may cover quantile regression, uncertainty intervals, calibration, and supply-chain safety-stock applications using the same dataset and leakage-aware temporal protocol.
