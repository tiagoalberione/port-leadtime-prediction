from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "kaggle" / "notebooks" / "01_brazilian_port_lead_time_eda_baseline.ipynb"
QUANTILE_NOTEBOOK_PATH = (
    ROOT / "kaggle" / "notebooks" / "02_brazilian_port_lead_time_quantile_uncertainty.ipynb"
)
DATAWRANGLER_MIME = "application/vnd.microsoft.datawrangler.viewer.v0+json"


def load_notebook(path=NOTEBOOK_PATH):
    return nbformat.read(path, as_version=4)


def test_public_notebook_is_csv_only_and_has_no_dictionary_runtime_dependency():
    nb = load_notebook()
    code = "\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")

    assert "brazilian_port_calls_model_ready_2023_2025.csv" in code
    assert "pd.read_csv(model_path, parse_dates=[DATE_COL])" in code
    assert "read_parquet" not in code
    assert ".parquet" not in code
    assert "DICTIONARY_FILE" not in code
    assert "data_dictionary" not in code


def test_public_notebook_outputs_are_sanitized():
    nb = load_notebook()
    assert not any("execution" in cell.get("metadata", {}) for cell in nb.cells)
    assert not any(
        DATAWRANGLER_MIME in output.get("data", {})
        for cell in nb.cells
        for output in cell.get("outputs", [])
    )
    assert not any(
        output.get("output_type") == "error"
        for cell in nb.cells
        for output in cell.get("outputs", [])
    )


def test_public_notebook_final_test_modeling_use_is_locked():
    nb = load_notebook()
    locked_index = next(
        idx
        for idx, cell in enumerate(nb.cells)
        if cell.cell_type == "markdown" and cell.source.startswith("## 12. Locked Final Evaluation")
    )
    before_locked_code = "\n".join(
        cell.source for cell in nb.cells[:locked_index] if cell.cell_type == "code"
    )

    assert 'df[df[SPLIT_COL] == "final_test"]' not in before_locked_code
    assert "final_holdout_df" not in before_locked_code
    assert "final_model.fit" not in before_locked_code


def test_quantile_notebook_exists_and_is_csv_only():
    assert QUANTILE_NOTEBOOK_PATH.exists()
    nb = load_notebook(QUANTILE_NOTEBOOK_PATH)
    code = "\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")

    assert "brazilian_port_calls_model_ready_2023_2025.csv" in code
    assert "pd.read_csv(model_path, parse_dates=[DATE_COL])" in code
    assert "read_parquet" not in code
    assert ".parquet" not in code
    assert "data_dictionary" not in code


def test_quantile_notebook_predictor_rule_splits_and_quantiles():
    nb = load_notebook(QUANTILE_NOTEBOOK_PATH)
    code = "\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")

    assert 'BASE_COLUMNS = [ID_COL, DATE_COL, TARGET, SPLIT_COL]' in code
    assert "assert len(predictors) == 120" in code
    assert 'QUANTILES = {"P50": 0.50, "P90": 0.90, "P95": 0.95}' in code
    for expected in [
        '"train": ("2023-01-01", "2024-07-01")',
        '"validation": ("2024-07-01", "2025-01-01")',
        '"calibration": ("2025-01-01", "2025-07-01")',
        '"final_test": ("2025-07-01", "2026-01-01")',
    ]:
        assert expected in code


def test_quantile_notebook_final_test_modeling_use_is_locked():
    nb = load_notebook(QUANTILE_NOTEBOOK_PATH)
    locked_index = next(
        idx
        for idx, cell in enumerate(nb.cells)
        if cell.cell_type == "markdown" and cell.source.startswith("## 10. Locked Final Evaluation")
    )
    before_locked_code = "\n".join(
        cell.source for cell in nb.cells[:locked_index] if cell.cell_type == "code"
    )
    after_locked_code = "\n".join(
        cell.source for cell in nb.cells[locked_index:] if cell.cell_type == "code"
    )

    assert 'df[df[SPLIT_COL] == "final_test"]' not in before_locked_code
    assert "final_holdout_df" not in before_locked_code
    assert "fit_quantile_pipelines(development_for_final)" in after_locked_code


def test_quantile_notebook_outputs_are_sanitized():
    nb = load_notebook(QUANTILE_NOTEBOOK_PATH)
    assert not any("execution" in cell.get("metadata", {}) for cell in nb.cells)
    assert not any(
        DATAWRANGLER_MIME in output.get("data", {})
        for cell in nb.cells
        for output in cell.get("outputs", [])
    )
    assert not any(
        output.get("output_type") == "error"
        for cell in nb.cells
        for output in cell.get("outputs", [])
    )
