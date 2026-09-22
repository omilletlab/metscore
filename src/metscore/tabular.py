from __future__ import annotations

import pandas as pd
from pandas.api.types import is_numeric_dtype

from metscore.core import _predict_array
from metscore.parameters import load_parameters


def predict(
    data: pd.DataFrame,
) -> pd.DataFrame:
    """Calculate MetSCORE from a tabular dataset.

    Each row represents one sample. Required MetSCORE variables are selected
    and reordered automatically by column name, so their original order in
    the DataFrame does not matter. Additional columns are preserved.

    Parameters
    ----------
    data
        Input DataFrame containing all variables required by MetSCORE.
        Model variables must be numeric and expressed in the units expected
        by the MetSCORE model; no unit conversion is performed.

    Returns
    -------
    pandas.DataFrame
        Copy of the input DataFrame with ``MetSCORE``, ``t_pred``, and
        one ``t_orth_<n>`` column per orthogonal component appended.

    Raises
    ------
    TypeError
        If ``data`` is not a pandas DataFrame.
    ValueError
        If the DataFrame is empty, contains duplicate column names,
        is missing required variables, contains non-numeric model
        variables, or already contains prediction output columns.
    """
    if not isinstance(data, pd.DataFrame):
        raise TypeError("Input must be a pandas DataFrame.")

    if data.empty:
        raise ValueError("Input DataFrame cannot be empty.")

    if data.columns.duplicated().any():
        duplicated = data.columns[data.columns.duplicated()].unique()
        names = ", ".join(str(name) for name in duplicated)
        raise ValueError(f"Duplicate column names are not allowed: {names}")

    params = load_parameters()

    missing_variables = [
        variable
        for variable in params.variables
        if variable not in data.columns
    ]

    if missing_variables:
        names = ", ".join(missing_variables)
        raise ValueError(f"Missing required model variables: {names}")

    non_numeric_variables = [
        variable
        for variable in params.variables
        if not is_numeric_dtype(data[variable])
    ]

    if non_numeric_variables:
        names = ", ".join(non_numeric_variables)
        raise ValueError(f"Model variables must be numeric: {names}")

    output_columns = [
        "MetSCORE",
        "t_pred",
        *[
            f"t_orth_{index}"
            for index in range(1, params.w_orth.shape[0] + 1)
        ],
    ]

    existing_outputs = [
        column for column in output_columns if column in data.columns
    ]

    if existing_outputs:
        names = ", ".join(existing_outputs)
        raise ValueError(
            f"Prediction output columns already exist: {names}"
        )

    x = data.loc[:, list(params.variables)].to_numpy(dtype=float)

    prediction = _predict_array(x, params)

    result = data.copy()
    result["MetSCORE"] = prediction.metscore
    result["t_pred"] = prediction.t_pred

    for index in range(prediction.t_orth.shape[1]):
        result[f"t_orth_{index + 1}"] = prediction.t_orth[:, index]

    return result