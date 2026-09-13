# Data Dictionary

The machine-readable data dictionary is generated at:

```text
kaggle/dataset/data_dictionary.csv
```

It is rebuilt by:

```bash
conda run -n port-leadtime python scripts/build_kaggle_dataset.py
```

## Columns

The CSV is a full inventory of columns exposed by the source analytical base or the model-ready build. Some rows document columns that are intentionally excluded from the public Kaggle outputs because of leakage or provenance constraints.

The CSV contains:

- `column`: column name in the public files
- `dtype`: pandas dtype observed during the build
- `description`: plain-English explanation of the field
- `source`: source or transformation lineage
- `transformation`: how the field is produced
- `availability_at_prediction_time`: `yes`, `no`, `historical_only`, or `not_applicable`
- `modeling_role`: `feature`, `target`, `identifier`, `eda_only`, `leakage_do_not_use`, or `metadata`
- `included_in_analytical`: whether the column appears in the analytical dataset
- `included_in_model_ready`: whether the column appears in the model-ready dataset
- `notes`: usage warnings or modeling notes

## Modeling Rule

The prediction timestamp is `arrival_port_ts`. For the model-ready dataset, a predictor is included only when it is available at arrival time or reconstructed from information known before arrival. Columns marked `leakage_do_not_use` must not be used as predictors for arrival-time modeling.
