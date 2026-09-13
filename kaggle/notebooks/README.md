# Kaggle Notebooks

This folder contains public notebooks intended for the Kaggle dataset:

https://www.kaggle.com/datasets/tiagoalberione/brazilian-port-calls-lead-time-2023-2025

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

The notebook is designed to run on Kaggle with the published dataset attached. It prefers:

```text
brazilian_port_calls_model_ready_2023_2025.parquet
data_dictionary.csv
```

For local development, it can also resolve files generated under:

```text
kaggle/dataset/output/
```

## Modeling Scope

The notebook is intentionally small and educational. It does not reproduce the full thesis workflow, does not run hyperparameter searches, and does not include quantile regression, uncertainty analysis, or safety-stock simulation.

## Leakage Policy

The model uses only columns present in the model-ready dataset after excluding `port_call_id`, `arrival_port_ts`, `t_total_port_stay_h`, and `split`. It verifies these predictors against `data_dictionary.csv` when available and keeps `final_test` untouched until the final locked evaluation.

## Future Notebooks

Later public notebooks may cover quantile regression, uncertainty intervals, calibration, and supply-chain safety-stock applications using the same dataset and leakage-aware temporal protocol.
