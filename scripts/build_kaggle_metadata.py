"""Build structured Kaggle metadata for the single-file public dataset."""

from __future__ import annotations

import json
from collections import OrderedDict
from pathlib import Path
from typing import Any

import pandas as pd


ROOT = Path(__file__).resolve().parents[1]
METADATA_PATH = ROOT / "kaggle" / "dataset-metadata.json"
DATA_DICTIONARY_PATH = ROOT / "kaggle" / "dataset" / "data_dictionary.csv"
OUTPUT_DIR = ROOT / "kaggle" / "dataset" / "output"

MODEL_READY_NAME = "brazilian_port_calls_model_ready_2023_2025"
PUBLIC_CSV_NAME = f"{MODEL_READY_NAME}.csv"
PUBLIC_CSV_PATH = OUTPUT_DIR / PUBLIC_CSV_NAME

DATASET_TITLE = "Brazilian Port Calls & Lead Time 2023-2025"
DATASET_ID = "tiagoalberione/brazilian-port-lead-time-2023-2025"
DATASET_SUBTITLE = "Brazilian port-call data for leakage-aware lead-time modeling"
DATASET_DESCRIPTION = (
    "A cleaned academic dataset of Brazilian vessel port calls for arrival-time prediction of total "
    "port stay. It contains 129,625 calls from 2023-2025, an official chronological "
    "train/validation/calibration/final-test split, and leakage-aware historical, operational, "
    "geographic, calendar, and weather features."
)
DATASET_LICENSES = [{"name": "CC-BY-4.0"}]
EXPECTED_UPDATE_FREQUENCY = "never"
RESOURCE_DESCRIPTION = (
    "Leakage-aware machine-learning dataset containing 129,625 Brazilian vessel port calls from "
    "2023 through 2025. The file includes the prediction target, official temporal split, "
    "identifiers, and 120 predictors available at vessel arrival or reconstructed exclusively "
    "from prior historical information."
)

DEFAULT_KEYWORDS = [
    "brazil",
    "regression",
    "artificial intelligence",
    "time series analysis",
    "government",
]


def read_json_without_bom(path: Path) -> dict[str, Any]:
    """Read JSON and reject UTF-8 BOM because Kaggle metadata should be plain UTF-8."""
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError(f"{path.relative_to(ROOT)} contains a UTF-8 BOM.")
    return json.loads(raw.decode("utf-8"))


def load_data_dictionary(path: Path) -> pd.DataFrame:
    """Load and validate the machine-readable data dictionary."""
    if not path.exists():
        raise FileNotFoundError(f"Data dictionary not found: {path.relative_to(ROOT)}")
    dictionary = pd.read_csv(path)
    required = {"column", "dtype", "description"}
    missing = sorted(required - set(dictionary.columns))
    if missing:
        raise RuntimeError(f"Data dictionary missing columns: {missing}")
    empty = dictionary["description"].fillna("").astype(str).str.strip().eq("")
    if empty.any():
        cols = dictionary.loc[empty, "column"].tolist()
        raise RuntimeError(f"Data dictionary has empty descriptions for: {cols}")
    if dictionary["column"].duplicated().any():
        cols = dictionary.loc[dictionary["column"].duplicated(), "column"].tolist()
        raise RuntimeError(f"Data dictionary has duplicated column entries: {cols}")
    return dictionary


def kaggle_type(dtype: str) -> str:
    """Map pandas dtype strings to Kaggle-compatible schema types."""
    normalized = str(dtype).lower()
    if "datetime" in normalized or normalized.startswith("date"):
        return "datetime"
    if "bool" in normalized:
        return "boolean"
    if "int" in normalized or normalized.startswith("uint"):
        return "integer"
    if any(token in normalized for token in ["float", "double", "decimal"]):
        return "numeric"
    return "string"


def read_csv_column_order(path: Path) -> list[str]:
    """Read the exact public CSV column order."""
    if not path.exists():
        raise FileNotFoundError(f"Generated public CSV not found: {path.relative_to(ROOT)}")
    return pd.read_csv(path, nrows=0).columns.tolist()


def build_schema(csv_path: Path, dictionary: pd.DataFrame) -> dict[str, list[dict[str, str]]]:
    """Build the one public CSV schema from actual file order and dictionary descriptions."""
    order = read_csv_column_order(csv_path)
    by_column = dictionary.set_index("column")
    fields = []
    missing = []
    for column in order:
        if column not in by_column.index:
            missing.append(column)
            continue
        row = by_column.loc[column]
        description = str(row["description"]).strip()
        if not description:
            missing.append(column)
            continue
        fields.append(
            {
                "name": column,
                "type": kaggle_type(row["dtype"]),
                "description": description,
            }
        )
    if missing:
        raise RuntimeError(f"{csv_path.name} has fields missing data-dictionary descriptions: {missing}")
    if [field["name"] for field in fields] != order:
        raise RuntimeError(f"Schema field order does not match {csv_path.name}.")
    return {"fields": fields}


def provenance_text() -> str:
    """Return concise markdown provenance for Kaggle structured metadata."""
    return (
        "Sources and transformations:\n"
        "- Porto Sem Papel / Minist\u00e9rio de Portos e Aeroportos: "
        "https://dados.transportes.gov.br/dataset/estadia-embarcacao. Vessel port-call records "
        "originate from public Porto Sem Papel data and were cleaned and consolidated into one row "
        "per port call.\n"
        "- Official Porto Sem Papel port reference: https://dados.transportes.gov.br/dataset/portos-psp. "
        "State is reconstructed by exact official port-code matching where available, and region is "
        "derived deterministically from state.\n"
        "- Open-Meteo: https://open-meteo.com/. Historical weather features are derived from Open-Meteo "
        "data.\n"
        "Manually researched municipality and geographic coordinates are not redistributed. Historical "
        "aggregate predictors use leakage-safe walk-forward reconstruction."
    )


def build_metadata() -> dict[str, Any]:
    """Build deterministic metadata for the new single-file Kaggle dataset."""
    current = read_json_without_bom(METADATA_PATH)
    dictionary = load_data_dictionary(DATA_DICTIONARY_PATH)
    keywords = current.get("keywords") or DEFAULT_KEYWORDS

    metadata: OrderedDict[str, Any] = OrderedDict()
    metadata["title"] = DATASET_TITLE
    metadata["subtitle"] = DATASET_SUBTITLE
    metadata["description"] = DATASET_DESCRIPTION
    metadata["id"] = DATASET_ID
    metadata["licenses"] = DATASET_LICENSES
    metadata["keywords"] = keywords
    metadata["expectedUpdateFrequency"] = EXPECTED_UPDATE_FREQUENCY
    metadata["userSpecifiedSources"] = provenance_text()
    metadata["resources"] = [
        {
            "path": PUBLIC_CSV_NAME,
            "description": RESOURCE_DESCRIPTION,
            "schema": build_schema(PUBLIC_CSV_PATH, dictionary),
        }
    ]
    return dict(metadata)


def validate_metadata(metadata: dict[str, Any]) -> None:
    """Validate the structured metadata generated for the single-file Kaggle dataset."""
    if metadata.get("id") != DATASET_ID:
        raise RuntimeError("Metadata id does not match the new Kaggle dataset id.")
    if metadata.get("licenses") != DATASET_LICENSES:
        raise RuntimeError("Metadata license must be CC-BY-4.0.")
    if metadata.get("expectedUpdateFrequency") != EXPECTED_UPDATE_FREQUENCY:
        raise RuntimeError("expectedUpdateFrequency must be never.")
    if not str(metadata.get("userSpecifiedSources", "")).strip():
        raise RuntimeError("userSpecifiedSources must be populated.")

    resources = metadata.get("resources", [])
    if len(resources) != 1:
        raise RuntimeError(f"Expected exactly 1 resource, found {len(resources)}.")
    resource = resources[0]
    if resource.get("path") != PUBLIC_CSV_NAME:
        raise RuntimeError(f"Unexpected resource path: {resource.get('path')}")
    if not str(resource.get("description", "")).strip():
        raise RuntimeError("The public CSV resource is missing its description.")

    fields = resource.get("schema", {}).get("fields", [])
    actual_order = read_csv_column_order(PUBLIC_CSV_PATH)
    if [field.get("name") for field in fields] != actual_order:
        raise RuntimeError("Schema field order does not match the public CSV column order.")
    if any(not str(field.get("description", "")).strip() for field in fields):
        raise RuntimeError("At least one schema field has an empty description.")
    if any(field.get("type") not in {"string", "boolean", "integer", "numeric", "datetime"} for field in fields):
        raise RuntimeError("At least one schema field has an unsupported Kaggle type.")


def write_metadata(metadata: dict[str, Any], path: Path) -> None:
    """Write deterministic UTF-8 JSON without BOM."""
    path.write_text(json.dumps(metadata, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    if path.read_bytes().startswith(b"\xef\xbb\xbf"):
        raise RuntimeError(f"{path.relative_to(ROOT)} was written with a UTF-8 BOM.")


def main() -> int:
    """Generate and validate local Kaggle metadata without uploading anything."""
    metadata = build_metadata()
    validate_metadata(metadata)
    write_metadata(metadata, METADATA_PATH)
    written = read_json_without_bom(METADATA_PATH)
    validate_metadata(written)

    fields = written["resources"][0]["schema"]["fields"]
    print("Kaggle dataset metadata updated.")
    print(f"id: {written['id']}")
    print(f"expectedUpdateFrequency: {written['expectedUpdateFrequency']}")
    print(f"resources: {len(written['resources'])}")
    print(f"schema fields: {len(fields)}")
    print(f"metadata path: {METADATA_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
