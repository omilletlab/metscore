import numpy as np

from metscore.parameters import load_parameters


def test_load_parameters() -> None:
    parameters = load_parameters()

    assert len(parameters.variables) == 22
    assert parameters.x_mean.shape == (22,)
    assert parameters.x_sd.shape == (22,)
    assert parameters.w_orth.shape == (1, 22)
    assert parameters.p_orth.shape == (1, 22)
    assert parameters.w_pred.shape == (22,)


def test_parameter_arrays_are_finite() -> None:
    parameters = load_parameters()

    arrays = (
        parameters.x_mean,
        parameters.x_sd,
        parameters.w_orth,
        parameters.p_orth,
        parameters.w_pred,
    )

    assert all(np.all(np.isfinite(array)) for array in arrays)


def test_parameter_arrays_are_read_only() -> None:
    parameters = load_parameters()

    assert not parameters.x_mean.flags.writeable
    assert not parameters.x_sd.flags.writeable
    assert not parameters.w_orth.flags.writeable
    assert not parameters.p_orth.flags.writeable
    assert not parameters.w_pred.flags.writeable