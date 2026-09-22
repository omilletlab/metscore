from __future__ import annotations

from dataclasses import dataclass

import numpy as np
from numpy.typing import ArrayLike, NDArray

from metscore.parameters import ModelParameters, load_parameters


@dataclass(frozen=True, slots=True)
class PredictionResult:
    """Results produced by the MetSCORE model.

    Attributes
    ----------
    metscore
        MetSCORE values between 0 and 1, one per sample.
    t_pred
        Predictive OPLS scores, one per sample.
    t_orth
        Orthogonal OPLS scores with shape
        ``(n_samples, n_orthogonal_components)``.
    """

    metscore: NDArray[np.float64]
    t_pred: NDArray[np.float64]
    t_orth: NDArray[np.float64]


def predict_array(
    x: ArrayLike,
) -> PredictionResult:
    """Calculate MetSCORE from a numeric array.

    This low-level interface expects the MetSCORE input variables in the
    exact order required by the packaged model. Variable names and units
    cannot be validated because the input array contains no column metadata.

    For named tabular data, use `metscore.predict`, which selects and
    reorders the required variables automatically.

    Parameters
    ----------
    x
        Input values with shape ``(n_variables,)`` for one sample or
        ``(n_samples, n_variables)`` for multiple samples. Values must use
        the units expected by the MetSCORE model; no unit conversion is
        performed.

    Returns
    -------
    PredictionResult
        MetSCORE values, predictive OPLS scores, and orthogonal OPLS scores
        for all samples.

    Raises
    ------
    ValueError
        If the input has an invalid shape, contains non-finite values,
        or contains values incompatible with the ``log10(x + 1)``
        transformation.
    """
    return _predict_array(
        x,
        load_parameters(),
    )


def _predict_array(
    x: ArrayLike,
    parameters: ModelParameters,
) -> PredictionResult:
    params = parameters

    x_array = np.asarray(x, dtype=float)

    if x_array.ndim == 1:
        x_array = x_array[np.newaxis, :]

    _validate_input(x_array, len(params.variables))

    x_log = np.log10(x_array + 1.0)
    x_scaled = (x_log - params.x_mean) / params.x_sd

    residual, t_orth = _orthogonal_deflation(
        x_scaled,
        params.w_orth,
        params.p_orth,
    )

    t_pred = residual @ params.w_pred
    logit = params.glm_intercept + params.glm_coef_tpred * t_pred
    metscore = _sigmoid(logit)

    return PredictionResult(
        metscore=metscore,
        t_pred=t_pred,
        t_orth=t_orth,
    )


def _validate_input(
    x: NDArray[np.float64],
    n_variables: int,
) -> None:
    if x.ndim != 2:
        raise ValueError(
            "Input must be a one- or two-dimensional numeric array."
        )

    if x.shape[1] != n_variables:
        raise ValueError(
            f"Expected {n_variables} variables, got {x.shape[1]}."
        )

    if not np.all(np.isfinite(x)):
        raise ValueError("Input contains non-finite values.")

    if np.any(x <= -1):
        raise ValueError(
            "Input values must be greater than -1 for the log10(x + 1) "
            "transformation."
        )


def _orthogonal_deflation(
    x_scaled: NDArray[np.float64],
    w_orth: NDArray[np.float64],
    p_orth: NDArray[np.float64],
) -> tuple[NDArray[np.float64], NDArray[np.float64]]:
    residual = x_scaled.copy()
    orthogonal_scores: list[NDArray[np.float64]] = []

    for w_o, p_o in zip(w_orth, p_orth, strict=True):
        norm_squared = float(w_o @ w_o)

        if norm_squared == 0:
            raise ValueError(
                "Orthogonal weight vector cannot have zero norm."
            )

        t_o = (residual @ w_o) / norm_squared
        orthogonal_scores.append(t_o)

        residual = residual - np.outer(t_o, p_o)

    if orthogonal_scores:
        t_orth = np.column_stack(orthogonal_scores)
    else:
        t_orth = np.empty((x_scaled.shape[0], 0), dtype=float)

    return residual, t_orth


def _sigmoid(
    x: NDArray[np.float64],
) -> NDArray[np.float64]:
    result = np.empty_like(x, dtype=float)

    positive = x >= 0
    result[positive] = 1.0 / (1.0 + np.exp(-x[positive]))

    exp_x = np.exp(x[~positive])
    result[~positive] = exp_x / (1.0 + exp_x)

    return result