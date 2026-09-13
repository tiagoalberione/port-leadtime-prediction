# Brazilian Port Calls & Lead Time 2023-2025

## About the Dataset

This dataset contains cleaned Brazilian vessel port-call data for studying port stay duration and building arrival-time machine learning models. Each row represents one consolidated vessel call at a Brazilian port.

The public Kaggle distribution intentionally exposes one easy-to-use CSV file. Detailed source notes, data dictionary files, and local build artifacts are maintained in the GitHub repository for auditability.

## Motivation

Port stay time is an important component of maritime lead time. This dataset supports exploratory analysis, regression, quantile regression, supply chain analytics, and reproducible academic modeling.

## Data Sources

The data come mainly from public Brazilian maritime records related to Porto Sem Papel, enriched with official state information and Open-Meteo daily weather variables. See `SOURCES.md` for source mapping and license status.

## Geographic Data Provenance

Port identifiers and official state information are reconstructed from public maritime sources by exact port-code matching. Brazilian macro-region is derived deterministically from state/UF.

The historical academic workflow used manually researched port coordinates to collect weather data. Those coordinates, and the manually enriched `city` field, are not redistributed in the published Kaggle CSV. Weather variables are redistributed as Open-Meteo-derived values, with Open-Meteo attribution required.

In this snapshot, 534 of 129,625 port calls, approximately 0.41%, do not have published `state` or `region` values because their port codes did not have an exact match in the official PSP port reference. No fuzzy or manual matching was applied.

## Unit of Observation

One row is one consolidated port call, identified by `port_call_id`. Raw vessel-stay records are grouped so that each call keeps the first arrival, first berthing, last unberthing, and last departure timestamps.

## Time Coverage

The snapshot covers arrivals from 2023-01-01 through 2025-12-31. The build validates that no published observation falls outside 2023-2025.

## Main Target

The main target is `t_total_port_stay_h`: total vessel port stay in hours, computed as:

```text
departure_port_ts - arrival_port_ts
```

The prediction timestamp is `arrival_port_ts`.

## Dataset Files

- `brazilian_port_calls_model_ready_2023_2025.csv`

The public Kaggle dataset does not attach `data_dictionary.csv` or separate Markdown documentation files. Use the GitHub repository for full field descriptions, source/provenance review, and local build summaries:

https://github.com/tiagoalberione/port-leadtime-prediction

## Local Analytical Artifact

The repository build can generate a local analytical artifact with 95 columns for EDA, descriptive statistics, lead-time studies, and new feature ideation. It may include useful post-arrival timestamps, realized durations, and descriptive variables. Some columns in that local artifact are not valid predictors at arrival time, and it is not part of the current Kaggle distribution.

## Model-Ready Dataset

The model-ready dataset has 124 columns and is restricted to defensible arrival-time predictors from the official `ENRICHED_SAFE_HISTORY` feature set. It includes identifiers needed for reproducibility, `arrival_port_ts`, `t_total_port_stay_h`, `split`, calendar predictors, declared operation flags, lagged weather variables, and reconstructed historical operational context.

The published model-ready dataset is not simply a subset of the local analytical artifact. It excludes columns that would leak future information and adds historical features reconstructed specifically for leakage-safe modeling.

## Reproducibility Note

The Kaggle version preserves the official target, temporal splits, Open-Meteo weather values, and leakage-safe historical feature logic used for public reuse. Public geographic attributes were sanitized for provenance: coordinates and manual municipality values are excluded, `state` is rebuilt from the official PSP reference when an exact code match exists, and `region` is derived from `state`. Because of that sanitization, the public geographic attributes may differ from the historical thesis feature matrix for a small share of records.

For exact reproduction of the academic environment, use the academic snapshot/tag `v1.0.0-tcc`.

## Official Temporal Splits

- `train`: 2023-01-01 <= arrival < 2024-07-01
- `validation`: 2024-07-01 <= arrival < 2025-01-01
- `calibration`: 2025-01-01 <= arrival < 2025-07-01
- `final_test`: 2025-07-01 <= arrival < 2026-01-01

Use `train`, `validation`, and `calibration` for development work. `final_test` is the official holdout. Do not use `final_test` for feature selection, hyperparameter tuning, model selection, or configuration decisions if the goal is to compare results with the original study.

## Temporal Semantics of Historical Features

Historical features are precomputed in chronological, walk-forward semantics. For an arrival on day D, reconstructed operational features use a conservative cutoff of 23:59:59 on D-1. Earlier port calls contribute to historical statistics only when their relevant outcome is already known: waiting time after `berthing_ts`, operation time after `unberthing_ts`, and total stay after `departure_port_ts`.

These features may therefore include results from earlier calls that had already concluded before the cutoff, simulating an operational database that is updated over time. They do not use the current call's post-arrival events, same-day later events, or future calls.

## Data Dictionary

Use `kaggle/dataset/data_dictionary.csv` in the GitHub repository to identify each column, its source, transformation, prediction-time availability, and modeling role. The dictionary is a full inventory: it also documents columns intentionally excluded from the public outputs due to leakage or provenance constraints.

## Leakage Considerations

A feature may be used in the model-ready dataset only if it is known at `arrival_port_ts` or reconstructed from information known before that instant. Post-arrival timestamps, realized duration components, same-day realized weather, target-derived flags, and exploratory congestion proxies are excluded from the model-ready predictors.

## Known Limitations

The dataset models port stay duration, not complete end-to-end logistics lead time. Public source files may change after this academic snapshot. Operation-type flags are treated as known at arrival time as a modeling premise. Safety stock and working-capital analyses in the original project are academic simulations, not observed financial outcomes.

## Suggested Uses

- Exploratory data analysis of Brazilian port calls
- Port stay duration modeling
- Regression and quantile regression benchmarks
- Temporal validation examples
- Supply chain lead-time uncertainty studies
- Feature engineering experiments with leakage-aware splits

## Citation

Alberione, T. Port Lead Time Prediction: vessel port stay modeling for Brazilian public port data. MBA thesis project, University of Sao Paulo, 2026.

## License and Attribution

Repository code is MIT licensed. The dataset license is separate. With manual coordinates and manual municipality fields removed from the public outputs, the published Kaggle dataset is distributed under CC BY 4.0. Attribution to Porto Sem Papel / Ministerio de Portos e Aeroportos and Open-Meteo should be included when using the dataset.
