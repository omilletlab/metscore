import pytest

from metscore.parameters import load_parameters

from pathlib import Path

import numpy as np
import pandas as pd

import metscore


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DATA = PROJECT_ROOT / "examples" / "example_data.csv"


def test_predict_matches_reference_order_independently() -> None:
    data = pd.read_csv(EXAMPLE_DATA)

    shuffled = data.sample(
        frac=1,
        axis=1,
        random_state=42,
    )

    result_original = metscore.predict(data)
    result_shuffled = metscore.predict(shuffled)

    np.testing.assert_allclose(
        result_original["MetSCORE"],
        result_shuffled["MetSCORE"],
    )

    np.testing.assert_allclose(
        result_original["t_pred"],
        result_shuffled["t_pred"],
    )

    np.testing.assert_allclose(
        result_original["t_orth_1"],
        result_shuffled["t_orth_1"],
    )


def test_predict_preserves_extra_columns() -> None:
    data = pd.read_csv(EXAMPLE_DATA)

    data["batch"] = "batch_01"
    data["note"] = "example"

    result = metscore.predict(data)

    assert "batch" in result.columns
    assert "note" in result.columns

    assert result["batch"].equals(data["batch"])
    assert result["note"].equals(data["note"])


def test_predict_does_not_modify_input_dataframe() -> None:
    data = pd.read_csv(EXAMPLE_DATA)
    original = data.copy(deep=True)

    metscore.predict(data)

    pd.testing.assert_frame_equal(data, original)


def test_predict_appends_expected_output_columns() -> None:
    data = pd.read_csv(EXAMPLE_DATA)

    result = metscore.predict(data)

    assert list(result.columns[-3:]) == [
        "MetSCORE",
        "t_pred",
        "t_orth_1",
    ]


def test_predict_rejects_missing_model_variable() -> None:
    data = pd.read_csv(EXAMPLE_DATA)
    parameters = load_parameters()
    missing_variable = parameters.variables[0]

    data = data.drop(columns=missing_variable)

    with pytest.raises(
        ValueError,
        match=f"Missing required model variables: {missing_variable}",
    ):
        metscore.predict(data)


def test_predict_rejects_duplicate_column_names() -> None:
    data = pd.read_csv(EXAMPLE_DATA)
    parameters = load_parameters()
    duplicated_variable = parameters.variables[0]

    data = pd.concat(
        [data, data[[duplicated_variable]]],
        axis=1,
    )

    with pytest.raises(
        ValueError,
        match="Duplicate column names are not allowed",
    ):
        metscore.predict(data)


def test_predict_rejects_non_numeric_model_variable() -> None:
    data = pd.read_csv(EXAMPLE_DATA)
    parameters = load_parameters()
    non_numeric_variable = parameters.variables[0]

    data[non_numeric_variable] = data[non_numeric_variable].astype(str)

    with pytest.raises(
        ValueError,
        match=f"Model variables must be numeric: {non_numeric_variable}",
    ):
        metscore.predict(data)


def test_predict_rejects_empty_dataframe() -> None:
    data = pd.read_csv(EXAMPLE_DATA).iloc[0:0]

    with pytest.raises(
        ValueError,
        match="Input DataFrame cannot be empty",
    ):
        metscore.predict(data)


def test_predict_rejects_existing_output_columns() -> None:
    data = pd.read_csv(EXAMPLE_DATA)
    data["MetSCORE"] = 0.0

    with pytest.raises(
        ValueError,
        match="Prediction output columns already exist: MetSCORE",
    ):
        metscore.predict(data)


def test_predict_rejects_non_dataframe_input() -> None:
    with pytest.raises(
        TypeError,
        match="Input must be a pandas DataFrame",
    ):
        metscore.predict([[1.0, 2.0]])