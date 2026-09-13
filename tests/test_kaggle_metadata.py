import pytest

from scripts.build_kaggle_metadata import (
    DATASET_ID,
    DATASET_LICENSES,
    DATA_DICTIONARY_PATH,
    EXPECTED_UPDATE_FREQUENCY,
    METADATA_PATH,
    PUBLIC_CSV_NAME,
    PUBLIC_CSV_PATH,
    build_metadata,
    load_data_dictionary,
    read_csv_column_order,
    read_json_without_bom,
    validate_metadata,
)


def test_kaggle_metadata_json_has_no_bom_and_new_dataset_identity():
    raw = METADATA_PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")

    metadata = read_json_without_bom(METADATA_PATH)
    assert metadata["id"] == DATASET_ID
    assert metadata["licenses"] == DATASET_LICENSES
    assert metadata["expectedUpdateFrequency"] == EXPECTED_UPDATE_FREQUENCY


def test_kaggle_metadata_has_one_described_csv_resource_if_output_exists():
    if not PUBLIC_CSV_PATH.exists():
        pytest.skip("Generated model-ready CSV is not available.")

    metadata = read_json_without_bom(METADATA_PATH)
    validate_metadata(metadata)

    resources = metadata["resources"]
    assert len(resources) == 1
    assert resources[0]["path"] == PUBLIC_CSV_NAME
    assert resources[0]["description"].startswith("Leakage-aware machine-learning dataset")


def test_kaggle_metadata_schema_matches_public_csv_order_if_output_exists():
    if not PUBLIC_CSV_PATH.exists():
        pytest.skip("Generated model-ready CSV is not available.")

    metadata = read_json_without_bom(METADATA_PATH)
    fields = metadata["resources"][0]["schema"]["fields"]

    assert [field["name"] for field in fields] == read_csv_column_order(PUBLIC_CSV_PATH)
    assert len(fields) == 124
    assert all(str(field.get("description", "")).strip() for field in fields)
    assert all(str(field.get("title", "")).strip() for field in fields)
    assert all(field["title"] == field["description"] for field in fields)
    assert all(field["type"] in {"string", "boolean", "integer", "numeric", "datetime"} for field in fields)


def test_kaggle_metadata_sources_are_populated():
    metadata = read_json_without_bom(METADATA_PATH)
    sources = metadata["userSpecifiedSources"]
    assert "Porto Sem Papel" in sources
    assert "https://dados.transportes.gov.br/dataset/estadia-embarcacao" in sources
    assert "https://dados.transportes.gov.br/dataset/portos-psp" in sources
    assert "https://open-meteo.com/" in sources
    assert "not redistributed" in sources
    assert "walk-forward" in sources


def test_metadata_builder_is_deterministic_for_single_csv_if_output_exists():
    if not PUBLIC_CSV_PATH.exists():
        pytest.skip("Generated model-ready CSV is not available.")
    assert DATA_DICTIONARY_PATH.exists()

    current = read_json_without_bom(METADATA_PATH)
    dictionary = load_data_dictionary(DATA_DICTIONARY_PATH)
    rebuilt = build_metadata()

    assert rebuilt == current
    assert len(dictionary) >= len(rebuilt["resources"][0]["schema"]["fields"])
