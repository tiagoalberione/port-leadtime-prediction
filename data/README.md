# Data

This project uses an academic snapshot of public Brazilian maritime data, mainly related to Porto Sem Papel, plus port reference files and daily weather data.

## Directory Policy

```text
data/downloaded/   Downloaded source files and URL references preserved for traceability
data/raw/          Canonical raw inputs expected by the preparation pipeline
data/interim/      Generated intermediate parquet files, ignored by Git
data/processed/    Generated analytical dataset, ignored by Git
```

The pipeline reads from `data/raw/` and writes intermediate and processed files. The main generated dataset is:

```text
data/processed/eda_base.parquet
```

## Sources

The source URL list used during the project is preserved in:

```text
data/downloaded/urls.txt
```

The public source files may change after the academic snapshot. For reproducibility of the thesis results, this repository keeps the raw snapshot used by the final workflow.

## Regeneration

From the repository root:

```bash
conda run -n mbausp python pipelines/build_eda_base.py
```

This command rebuilds:

- cleaned port-call data;
- quality-control tables;
- target variables;
- calendar and operation features;
- weather history features;
- the final analytical dataset.

## Redistribution Notes

The code is licensed under MIT. The data files are derived from public sources and remain subject to the original source terms, availability, and public-data policies. Do not treat this repository as the authoritative source for the raw datasets.

No credentials, private API keys, cookies, or private corporate data are required by the project.
