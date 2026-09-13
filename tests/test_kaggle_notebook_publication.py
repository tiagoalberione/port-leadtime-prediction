from pathlib import Path

import nbformat


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOK_PATH = ROOT / "kaggle" / "notebooks" / "01_brazilian_port_lead_time_eda_baseline.ipynb"
QUANTILE_NOTEBOOK_PATH = (
    ROOT / "kaggle" / "notebooks" / "02_brazilian_port_lead_time_quantile_uncertainty.ipynb"
)
SAFETY_STOCK_NOTEBOOK_PATH = (
    ROOT / "kaggle" / "notebooks" / "03_brazilian_port_lead_time_safety_stock.ipynb"
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


def test_safety_stock_notebook_exists_and_is_csv_only():
    assert SAFETY_STOCK_NOTEBOOK_PATH.exists()
    nb = load_notebook(SAFETY_STOCK_NOTEBOOK_PATH)
    code = "\n".join(cell.source for cell in nb.cells if cell.cell_type == "code")

    assert "brazilian_port_calls_model_ready_2023_2025.csv" in code
    assert "pd.read_csv(model_path, parse_dates=[DATE_COL])" in code
    assert "read_parquet" not in code
    assert ".parquet" not in code
    assert "data_dictionary" not in code
    assert "safety_stock_simulation.csv" not in code


def test_safety_stock_notebook_predictor_rule_splits_and_quantiles():
    nb = load_notebook(SAFETY_STOCK_NOTEBOOK_PATH)
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


def test_safety_stock_notebook_final_test_use_is_locked_to_application_stage():
    nb = load_notebook(SAFETY_STOCK_NOTEBOOK_PATH)
    locked_index = next(
        idx
        for idx, cell in enumerate(nb.cells)
        if cell.cell_type == "markdown" and cell.source.startswith("## 5. Generate Locked Quantile Predictions")
    )
    before_locked_code = "\n".join(
        cell.source for cell in nb.cells[:locked_index] if cell.cell_type == "code"
    )
    after_locked_code = "\n".join(
        cell.source for cell in nb.cells[locked_index:] if cell.cell_type == "code"
    )

    assert 'df[df[SPLIT_COL] == "final_test"]' not in before_locked_code
    assert "final_holdout_df" not in before_locked_code
    assert "fit_quantile_pipelines(development_df)" in after_locked_code
    assert "hierarchical_historical_quantile(development_policy, final_policy" in after_locked_code


def test_safety_stock_notebook_has_explicit_assumptions_formula_and_limitations():
    nb = load_notebook(SAFETY_STOCK_NOTEBOOK_PATH)
    text = "\n".join(cell.source for cell in nb.cells)

    for expected in [
        '"scenario": "base"',
        '"mean_daily_demand_units": 100.0',
        '"daily_demand_std_units": 25.0',
        '"service_factor_z": 1.65',
        '"unit_value_brl": 50.0',
        "variance_demand_during_lead = sigma**2 * lead + mu**2 * lead_variance",
        "safety_stock = z * np.sqrt",
        "Protection rate is:",
        "policy_lead_time >= actual_lead_time",
        "working-capital proxy",
        "educational scenario analysis",
        "The results do not demonstrate realized financial savings.",
    ]:
        assert expected in text


def test_safety_stock_notebook_outputs_are_sanitized():
    nb = load_notebook(SAFETY_STOCK_NOTEBOOK_PATH)
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
