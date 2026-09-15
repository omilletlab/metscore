from __future__ import annotations

import json
from dataclasses import dataclass
from importlib.resources import files

import numpy as np


_REQUIRED_FIELDS = {
    "variables",
    "x_mean",
    "x_sd",
    "w_orth",
    "p_orth",
    "w_pred",
    "threshold",
    "glm_intercept",
    "glm_coef_tpred",
}


@dataclass(frozen=True, slots=True)
class ModelParameters:
    """Parameters required to calculate MetSCORE.

    Attributes
    ----------
    variables
        Ordered names of the model input variables.
    x_mean
        Mean values used for autoscaling.
    x_sd
        Standard deviations used for autoscaling.
    w_orth
        Orthogonal weight vectors.
    p_orth
        Orthogonal loading vectors.
    w_pred
        Predictive weight vector.
    threshold
        Classification threshold associated with the model.
    glm_intercept
        Intercept of the logistic regression model.
    glm_coef_tpred
        Logistic regression coefficient for the predictive score.
    """

    variables: tuple[str, ...]
    x_mean: np.ndarray
    x_sd: np.ndarray
    w_orth: np.ndarray
    p_orth: np.ndarray
    w_pred: np.ndarray
    threshold: float
    glm_intercept: float
    glm_coef_tpred: float


def load_parameters() -> ModelParameters:
    """Load and validate the packaged MetSCORE model parameters.

    Returns
    -------
    ModelParameters
        Validated model parameters.

    Raises
    ------
    ValueError
        If the parameter file is incomplete, malformed, or internally
        inconsistent.
    """
    resource = files("metscore").joinpath("data", "metscore_params.json")

    with resource.open("r", encoding="utf-8") as handle:
        raw = json.load(handle)

    if not isinstance(raw, dict):
        raise ValueError("The model parameter file must contain a JSON object.")

    missing_fields = _REQUIRED_FIELDS.difference(raw)
    if missing_fields:
        missing = ", ".join(sorted(missing_fields))
        raise ValueError(f"Missing model parameter fields: {missing}")

    variables_raw = raw["variables"]
    if (
        not isinstance(variables_raw, list)
        or not variables_raw
        or not all(isinstance(value, str) and value for value in variables_raw)
    ):
        raise ValueError("Model variables must be a non-empty list of strings.")

    parameters = ModelParameters(
        variables=tuple(variables_raw),
        x_mean=_to_float_array(raw["x_mean"], "x_mean"),
        x_sd=_to_float_array(raw["x_sd"], "x_sd"),
        w_orth=_to_float_array(raw["w_orth"], "w_orth"),
        p_orth=_to_float_array(raw["p_orth"], "p_orth"),
        w_pred=_to_float_array(raw["w_pred"], "w_pred"),
        threshold=_to_finite_float(raw["threshold"], "threshold"),
        glm_intercept=_to_finite_float(
            raw["glm_intercept"], "glm_intercept"
        ),
        glm_coef_tpred=_to_finite_float(
            raw["glm_coef_tpred"], "glm_coef_tpred"
        ),
    )

    _validate_parameters(parameters)
    return parameters


def _to_float_array(value: object, field_name: str) -> np.ndarray:
    try:
        array = np.asarray(value, dtype=float)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Model parameter '{field_name}' must contain numeric values."
        ) from exc

    if not np.all(np.isfinite(array)):
        raise ValueError(
            f"Model parameter '{field_name}' contains non-finite values."
        )

    array.setflags(write=False)
    return array


def _to_finite_float(value: object, field_name: str) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError) as exc:
        raise ValueError(
            f"Model parameter '{field_name}' must be numeric."
        ) from exc

    if not np.isfinite(number):
        raise ValueError(
            f"Model parameter '{field_name}' must be finite."
        )

    return number


def _validate_parameters(parameters: ModelParameters) -> None:
    n_variables = len(parameters.variables)

    if len(set(parameters.variables)) != n_variables:
        raise ValueError("Model variable names must be unique.")

    expected_vector_shape = (n_variables,)

    for field_name in ("x_mean", "x_sd", "w_pred"):
        array = getattr(parameters, field_name)
        if array.shape != expected_vector_shape:
            raise ValueError(
                f"Model parameter '{field_name}' must have shape "
                f"{expected_vector_shape}, got {array.shape}."
            )

    if parameters.w_orth.ndim != 2:
        raise ValueError("Model parameter 'w_orth' must be two-dimensional.")

    if parameters.p_orth.ndim != 2:
        raise ValueError("Model parameter 'p_orth' must be two-dimensional.")

    if parameters.w_orth.shape != parameters.p_orth.shape:
        raise ValueError(
            "Model parameters 'w_orth' and 'p_orth' must have the same shape."
        )

    if parameters.w_orth.shape[1] != n_variables:
        raise ValueError(
            "Orthogonal model parameters must match the number of variables."
        )

    if np.any(parameters.x_sd == 0):
        raise ValueError("Model parameter 'x_sd' cannot contain zero values.")