# Sources

This file separates the data redistributed in the published Kaggle CSV from historical inputs preserved for academic reproducibility. The Kaggle build reads the official project snapshot locally. Raw vessel-stay and weather source files are not redistributed in the Kaggle upload; cleaned and derived values from those sources are redistributed in `brazilian_port_calls_model_ready_2023_2025.csv`. The official PSP port reference snapshot `kaggle/reference/portos_no_porto_sem_papel_setembro_2021.csv` is versioned in GitHub for auditability because it is the public reference used to reconstruct `state`.

## Redistributed Data Sources

| Source | Provider | Official URL | License / terms | Data used in Kaggle outputs | Redistribution mode | Status |
|---|---|---|---|---|---|---|
| Estadia das Embarcacoes no PSP (Porto Sem Papel) | Ministerio de Portos e Aeroportos / Porto Sem Papel | https://dados.transportes.gov.br/dataset/estadia-embarcacao | Creative Commons Attribution | Port-call identifier, port code/name, vessel identifiers/names, operation type, source/destination ports, arrival/berthing/unberthing/departure timestamps, and duration targets derived from those timestamps | Raw file is not redistributed; cleaned and derived port-call values are redistributed | attribution_required |
| Portos no Porto Sem Papel - PSP - DESCONTINUADO | Ministerio de Portos e Aeroportos / Porto Sem Papel | https://dados.transportes.gov.br/dataset/portos-psp | Other (Public Domain) | State/UF by exact port-code match where available | Raw reference is included under `kaggle/reference/` for auditability; derived `state` is redistributed | public_domain |
| Open-Meteo historical weather data | Open-Meteo | https://open-meteo.com/ and https://github.com/open-meteo/open-meteo | CC BY 4.0, attribution required | Daily weather values and lagged weather features joined to port calls | Raw local weather extract is not redistributed; weather values and lagged weather features are redistributed | attribution_required |

## Derived Attributes

| Field | Source | Transformation | Status |
|---|---|---|---|
| `t_total_port_stay_h` | Porto Sem Papel vessel-stay timestamps | `departure_port_ts - arrival_port_ts`, expressed in hours after quality filters | compatible |
| `state` | Portos no Porto Sem Papel - PSP | Exact join from public port code to UF when available; no fuzzy matching | public_domain |
| `region` | Published `state` | Deterministic Brazilian state-to-macro-region mapping in `scripts/build_kaggle_dataset.py` | compatible |
| Calendar features | `arrival_port_ts` | Direct timestamp decomposition and cyclical encodings | compatible |
| Operation flags | `operation_type` | Deterministic parsing of declared operation motives | compatible |
| Historical operational features | Cleaned port-call history | Chronological D-1 walk-forward reconstruction using only events known before cutoff | compatible |
| Weather history features | Open-Meteo daily values | Lagged and rolling historical weather summaries excluding arrival-day weather | attribution_required |

## Internal Historical References

The original academic workflow used `data/raw/ports/port.csv` with manually enriched geography:

- `city`
- `state`
- `region`
- `latitude`
- `longitude`

Those geography fields were manually researched during the thesis process and are preserved only as historical/internal inputs. They are not treated as Porto Sem Papel fields. The published Kaggle CSV does not redistribute `city`, `latitude`, `longitude`, `latitude_r`, `longitude_r`, `port_display`, `port_name_ref`, or `port_display_ref` from that internal reference. Published `state` is rebuilt from the official PSP reference, and published `region` is derived from `state`.

The historical coordinates were used internally to query Open-Meteo weather data. The coordinates are not redistributed; Open-Meteo-derived weather values remain in the public outputs with attribution.

## Preserved but Unused Inputs

| Local file | Official public dataset represented | Official URL | License / terms | Kaggle build use |
|---|---|---|---|---|
| `data/raw/agencia/dadosagencias.csv` | Agencia de Navegacao - DUV (Porto Sem Papel) | https://dados.transportes.gov.br/dataset/agencia-navegacao-psp | Creative Commons Attribution | Preserved, not used |
| `data/raw/agencia/lista-agencias.csv` | Agencia de Navegacao - DUV (Porto Sem Papel) | https://dados.transportes.gov.br/dataset/agencia-navegacao-psp | Creative Commons Attribution | Preserved, not used |
| `data/raw/duv/DUV - Consolidated Raw Data.xlsx` | Documento Unico Virtual | https://dados.transportes.gov.br/dataset/documento-unico-virtual-psp | Other (Public Domain) | Preserved, not used |
| `data/raw/estadia/estadia_embarcacao.xlsx` | Estadia das Embarcacoes no PSP (Porto Sem Papel) | https://dados.transportes.gov.br/dataset/estadia-embarcacao | Creative Commons Attribution | Preserved, not used by the CSV-based pipeline |
| `data/raw/ports/port.xlsx` | Historical internal port reference | Local academic snapshot | Mixed/manual provenance | Preserved, not used by the CSV-based pipeline |
| `data/raw/weather/weather.xlsx` | Open-Meteo historical weather extract | https://open-meteo.com/ | CC BY 4.0 | Preserved, not used by the CSV-based pipeline |

## License Compatibility Review

| Source | Status | Notes |
|---|---|---|
| Estadia das Embarcacoes no PSP (Porto Sem Papel) | attribution_required | Official page declares Creative Commons Attribution. |
| Portos no Porto Sem Papel - PSP | public_domain | Official page declares Other (Public Domain); only exact code-to-UF values are used. |
| Open-Meteo daily weather | attribution_required | API data are CC BY 4.0. Attribution to Open-Meteo and indication of changes are required. |
| Internal manual port geography | compatible | Potential redistribution issue avoided by excluding coordinates and municipality from public Kaggle outputs. |
| Agencia de Navegacao - DUV (Porto Sem Papel) | attribution_required | Preserved locally but not used by the Kaggle build. |
| Documento Unico Virtual | public_domain | Preserved locally but not used by the Kaggle build. |

## License Decision

The repository code remains under the MIT License. The dataset license is separate from the code license, and the original sources remain subject to their own terms.

With manual Google Maps-derived geography removed from the published Kaggle CSV, the generated Kaggle dataset is technically suitable for publication under CC BY 4.0, provided attribution is maintained for Porto Sem Papel / Ministerio de Portos e Aeroportos and Open-Meteo.
