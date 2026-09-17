import csv
from pathlib import Path

import numpy as np

from metscore.core import predict_array
from metscore.parameters import load_parameters


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DATA = PROJECT_ROOT / "examples" / "example_data.csv"
REFERENCE_PREDICTIONS = (
    PROJECT_ROOT
    / "tests"
    / "fixtures"
    / "original_model_predictions.csv"
)
REFERENCE_SAMPLE_COUNT = 100


def test_predictions_match_original_model() -> None:
    parameters = load_parameters()

    with EXAMPLE_DATA.open(newline="", encoding="utf-8") as handle:
        input_rows = list(csv.DictReader(handle))

    with REFERENCE_PREDICTIONS.open(
        newline="",
        encoding="utf-8",
    ) as handle:
        reference_rows = list(csv.DictReader(handle))

    assert len(input_rows) == len(reference_rows)
    assert len(input_rows) == REFERENCE_SAMPLE_COUNT

    input_ids = [row["sample_id"] for row in input_rows]
    reference_ids = [row["sample_id"] for row in reference_rows]

    assert input_ids == reference_ids

    x = np.array(
        [
            [float(row[variable]) for variable in parameters.variables]
            for row in input_rows
        ],
        dtype=float,
    )

    expected_metscore = np.array(
        [float(row["MetSCORE"]) for row in reference_rows]
    )
    expected_t_pred = np.array(
        [float(row["t_pred"]) for row in reference_rows]
    )
    expected_t_orth = np.array(
        [float(row["t_orth_1"]) for row in reference_rows]
    )

    result = predict_array(x)

    np.testing.assert_allclose(
        result.metscore,
        expected_metscore,
        rtol=1e-10,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        result.t_pred,
        expected_t_pred,
        rtol=1e-10,
        atol=1e-12,
    )

    np.testing.assert_allclose(
        result.t_orth[:, 0],
        expected_t_orth,
        rtol=1e-10,
        atol=1e-12,
    )