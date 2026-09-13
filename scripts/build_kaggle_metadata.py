"""Build structured Kaggle dataset metadata without uploading anything."""

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

ANALYTICAL_NAME = "brazilian_port_calls_analytical_2023_2025"
MODEL_READY_NAME = "brazilian_port_calls_model_ready_2023_2025"

EXPECTED_UPDATE_FREQUENCY = "never"

PUBLISHED_RESOURCES = OrderedDict(
    [
        (
            "README.md",
            "Dataset landing-page documentation describing the port-stay prediction problem, files, target, splits, leakage policy, limitations, citation, and attribution.",
        ),
        (
            "SOURCES.md",
            "Source provenance and licensing review for the public dataset, including Porto Sem Papel, the official PSP port reference, and Open-Meteo.",
        ),
        (
            f"{ANALYTICAL_NAME}.csv",
            "CSV analytical dataset for EDA and descriptive research. It contains 95 columns, including variables that are not necessarily valid arrival-time predictors.",
        ),
        (
            f"{ANALYTICAL_NAME}.parquet",
            "Parquet analytical dataset for EDA and descriptive research. It preserves the same records and columns as the analytical CSV with typed storage.",
        ),
        (
            f"{MODEL_READY_NAME}.csv",
            "CSV arrival-time leakage-safe modeling dataset containing identifiers, the prediction timestamp, target, official temporal split, and 120 predictors.",
        ),
        (
            f"{MODEL_READY_NAME}.parquet",
            "Parquet arrival-time leakage-safe modeling dataset containing the same records and columns as the model-ready CSV with typed storage.",
        ),
        (
            "data_dictionary.csv",
            "Machine-readable documentation of source, transformation, prediction-time availability, modeling role, and publication status for every documented field.",
        ),
        (
            "dataset_build_summary.json",
            "Machine-readable build statistics, file hashes, row and column counts, split counts, and validation check summary.",
        ),
    ]
)

STRUCTURED_DATA_FILES = {
    f"{ANALYTICAL_NAME}.csv": OUTPUT_DIR / f"{ANALYTICAL_NAME}.csv",
    f"{ANALYTICAL_NAME}.parquet": OUTPUT_DIR / f"{ANALYTICAL_NAME}.parquet",
    f"{MODEL_READY_NAME}.csv": OUTPUT_DIR / f"{MODEL_READY_NAME}.csv",
    f"{MODEL_READY_NAME}.parquet": OUTPUT_DIR / f"{MODEL_READY_NAME}.parquet",
}

PRESERVED_KEYS = ["title", "subtitle", "description", "id", "licenses", "keywords"]


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
    if (
        "int" in normalized
        or normalized.startswith("uint")
        or normalized in {"int64", "int32", "int16", "int8"}
    ):
        return "integer"
    if any(token in normalized for token in ["float", "double", "decimal"]):
        return "numeric"
    return "string"


def read_column_order(path: Path) -> list[str]:
    """Read column order from the actual generated public file."""
    if not path.exists():
        raise FileNotFoundError(f"Generated dataset file not found: {path.relative_to(ROOT)}")
    if path.suffix.lower() == ".csv":
        return pd.read_csv(path, nrows=0).columns.tolist()
    if path.suffix.lower() == ".parquet":
        return pd.read_parquet(path).columns.tolist()
    raise ValueError(f"Unsupported structured data file: {path}")


def build_schema(path: Path, dictionary: pd.DataFrame) -> dict[str, list[dict[str, str]]]:
    """Build a Kaggle schema from actual file column order and dictionary descriptions."""
    order = read_column_order(path)
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
                "description": description,
                "type": kaggle_type(row["dtype"]),
            }
        )
    if missing:
        raise RuntimeError(
            f"{path.name} has public columns missing data-dictionary descriptions: {missing}"
        )
    if [field["name"] for field in fields] != order:
        raise RuntimeError(f"Schema field order does not match {path.name}.")
    return {"fields": fields}


def provenance_text() -> str:
    """Return concise markdown provenance for Kaggle structured metadata."""
    return (
        "Sources and transformations:\n"
        "- Estadia das Embarca\u00e7\u00f5es no Porto Sem Papel, Ministerio de Portos e Aeroportos / Porto Sem Papel: "
        "https://dados.transportes.gov.br/dataset/estadia-embarcacao. Port-call data were cleaned and transformed into one consolidated vessel call per row.\n"
        "- Portos no Porto Sem Papel - PSP, Ministerio de Portos e Aeroportos / Porto Sem Papel: "
        "https://dados.transportes.gov.br/dataset/portos-psp. State/UF was reconstructed by exact public port-code matching where available; region was derived from state.\n"
        "- Open-Meteo historical weather: https://open-meteo.com/. Lagged weather values are derived from Open-Meteo historical weather data.\n"
        "Manually researched municipality and coordinate fields from the academic workflow are not redistributed in the public Kaggle files."
    )


def build_resources(dictionary: pd.DataFrame) -> list[dict[str, Any]]:
    """Build one resource entry for each file expected in the Kaggle upload."""
    resources: list[dict[str, Any]] = []
    for path, description in PUBLISHED_RESOURCES.items():
        resource: dict[str, Any] = {"path": path, "description": description}
        if path in STRUCTURED_DATA_FILES:
            resource["schema"] = build_schema(STRUCTURED_DATA_FILES[path], dictionary)
        resources.append(resource)
    return resources


def build_metadata() -> dict[str, Any]:
    """Build complete structured metadata while preserving existing stable fields."""
    current = read_json_without_bom(METADATA_PATH)
    dictionary = load_data_dictionary(DATA_DICTIONARY_PATH)
    resources = build_resources(dictionary)

    metadata: OrderedDict[str, Any] = OrderedDict()
    for key in PRESERVED_KEYS:
        if key in current:
            metadata[key] = current[key]
    metadata["expectedUpdateFrequency"] = EXPECTED_UPDATE_FREQUENCY
    metadata["userSpecifiedSources"] = provenance_text()
    metadata["resources"] = resources

    for key, value in current.items():
        if key not in metadata:
            metadata[key] = value
    return dict(metadata)


def validate_metadata(metadata: dict[str, Any], original: dict[str, Any]) -> None:
    """Validate the structured metadata generated for Kaggle."""
    if metadata.get("expectedUpdateFrequency") != EXPECTED_UPDATE_FREQUENCY:
        raise RuntimeError("expectedUpdateFrequency must be never.")
    if metadata.get("id") != original.get("id"):
        raise RuntimeError("Dataset id was not preserved.")
    if metadata.get("licenses") != original.get("licenses"):
        raise RuntimeError("Dataset license was not preserved.")

    resources = metadata.get("resources", [])
    if len(resources) != len(PUBLISHED_RESOURCES):
        raise RuntimeError(f"Expected {len(PUBLISHED_RESOURCES)} resources, found {len(resources)}.")
    resource_by_path = {resource.get("path"): resource for resource in resources}
    expected_paths = set(PUBLISHED_RESOURCES)
    if set(resource_by_path) != expected_paths:
        raise RuntimeError(f"Unexpected resource paths: {sorted(set(resource_by_path) ^ expected_paths)}")
    missing_description = [
        path
        for path, resource in resource_by_path.items()
        if not str(resource.get("description", "")).strip()
    ]
    if missing_description:
        raise RuntimeError(f"Resources missing descriptions: {missing_description}")

    for path, actual_path in STRUCTURED_DATA_FILES.items():
        resource = resource_by_path[path]
        fields = resource.get("schema", {}).get("fields", [])
        actual_order = read_column_order(actual_path)
        if [field.get("name") for field in fields] != actual_order:
            raise RuntimeError(f"Schema order does not match actual file order for {path}.")
        if any(not str(field.get("description", "")).strip() for field in fields):
            raise RuntimeError(f"Schema field missing description in {path}.")
        if any(field.get("type") not in {"string", "boolean", "integer", "numeric", "datetime"} for field in fields):
            raise RuntimeError(f"Schema field has unsupported type in {path}.")


def write_metadata(metadata: dict[str, Any], path: Path) -> None:
    """Write deterministic UTF-8 JSON without BOM."""
    path.write_text(
        json.dumps(metadata, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"):
        raise RuntimeError(f"{path.relative_to(ROOT)} was written with a UTF-8 BOM.")


def main() -> int:
    """Generate and validate Kaggle metadata locally."""
    original = read_json_without_bom(METADATA_PATH)
    metadata = build_metadata()
    validate_metadata(metadata, original)
    write_metadata(metadata, METADATA_PATH)
    written = read_json_without_bom(METADATA_PATH)
    validate_metadata(written, original)

    resources = written["resources"]
    analytical_fields = len(
        next(r for r in resources if r["path"] == f"{ANALYTICAL_NAME}.csv")["schema"]["fields"]
    )
    model_ready_fields = len(
        next(r for r in resources if r["path"] == f"{MODEL_READY_NAME}.csv")["schema"]["fields"]
    )
    print("Kaggle dataset metadata updated.")
    print(f"expectedUpdateFrequency: {written['expectedUpdateFrequency']}")
    print(f"resources: {len(resources)}")
    print(f"analytical schema fields: {analytical_fields}")
    print(f"model-ready schema fields: {model_ready_fields}")
    print(f"metadata path: {METADATA_PATH.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
