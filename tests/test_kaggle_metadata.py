import pytest

from scripts.build_kaggle_metadata import (
    ANALYTICAL_NAME,
    DATA_DICTIONARY_PATH,
    EXPECTED_UPDATE_FREQUENCY,
    METADATA_PATH,
    MODEL_READY_NAME,
    PUBLISHED_RESOURCES,
    STRUCTURED_DATA_FILES,
    build_metadata,
    load_data_dictionary,
    read_column_order,
    read_json_without_bom,
    validate_metadata,
)


def test_kaggle_metadata_json_has_no_bom_and_preserves_core_fields():
    raw = METADATA_PATH.read_bytes()
    assert not raw.startswith(b"\xef\xbb\xbf")

    metadata = read_json_without_bom(METADATA_PATH)
    assert metadata["id"] == "tiagoalberione/brazilian-port-calls-lead-time-2023-2025"
    assert metadata["licenses"] == [{"name": "CC-BY-4.0"}]
    assert metadata["expectedUpdateFrequency"] == EXPECTED_UPDATE_FREQUENCY


def test_kaggle_metadata_resources_and_sources_are_complete_if_outputs_exist():
    if not all(path.exists() for path in STRUCTURED_DATA_FILES.values()):
        pytest.skip("Generated Kaggle output files are not available.")

    metadata = read_json_without_bom(METADATA_PATH)
    validate_metadata(metadata, metadata)

    assert len(metadata["resources"]) == len(PUBLISHED_RESOURCES) == 8
    assert {resource["path"] for resource in metadata["resources"]} == set(PUBLISHED_RESOURCES)
    assert all(str(resource.get("description", "")).strip() for resource in metadata["resources"])

    sources = metadata["userSpecifiedSources"]
    assert "Estadia das Embarcações no Porto Sem Papel" in sources
    assert "Portos no Porto Sem Papel - PSP" in sources
    assert "Open-Meteo historical weather" in sources
    assert "manually researched municipality and coordinate fields" in sources.lower()


def test_kaggle_metadata_schemas_match_public_file_order_if_outputs_exist():
    if not all(path.exists() for path in STRUCTURED_DATA_FILES.values()):
        pytest.skip("Generated Kaggle output files are not available.")

    metadata = read_json_without_bom(METADATA_PATH)
    resources = {resource["path"]: resource for resource in metadata["resources"]}

    expected_counts = {
        f"{ANALYTICAL_NAME}.csv": 95,
        f"{ANALYTICAL_NAME}.parquet": 95,
        f"{MODEL_READY_NAME}.csv": 124,
        f"{MODEL_READY_NAME}.parquet": 124,
    }
    for resource_path, actual_file in STRUCTURED_DATA_FILES.items():
        fields = resources[resource_path]["schema"]["fields"]
        assert [field["name"] for field in fields] == read_column_order(actual_file)
        assert len(fields) == expected_counts[resource_path]
        assert all(str(field.get("description", "")).strip() for field in fields)
        assert all(field["type"] in {"string", "boolean", "integer", "numeric", "datetime"} for field in fields)


def test_metadata_builder_is_deterministic_if_outputs_exist():
    if not all(path.exists() for path in STRUCTURED_DATA_FILES.values()):
        pytest.skip("Generated Kaggle output files are not available.")
    assert DATA_DICTIONARY_PATH.exists()

    current = read_json_without_bom(METADATA_PATH)
    dictionary = load_data_dictionary(DATA_DICTIONARY_PATH)
    rebuilt = build_metadata()

    assert rebuilt["id"] == current["id"]
    assert rebuilt["licenses"] == current["licenses"]
    assert rebuilt["expectedUpdateFrequency"] == current["expectedUpdateFrequency"]
    assert rebuilt["userSpecifiedSources"] == current["userSpecifiedSources"]
    assert rebuilt["resources"] == current["resources"]
    assert len(dictionary) >= max(len(resource["schema"]["fields"]) for resource in rebuilt["resources"] if "schema" in resource)
