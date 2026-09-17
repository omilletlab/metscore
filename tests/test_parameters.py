import numpy as np

from metscore.parameters import load_parameters

N_MODEL_VARIABLES = 22
N_ORTHOGONAL_COMPONENTS = 1

def test_load_parameters() -> None:
    parameters = load_parameters()

    assert len(parameters.variables) == N_MODEL_VARIABLES
    assert parameters.x_mean.shape == (N_MODEL_VARIABLES,)
    assert parameters.x_sd.shape == (N_MODEL_VARIABLES,)
    assert parameters.w_orth.shape == (N_ORTHOGONAL_COMPONENTS, N_MODEL_VARIABLES)
    assert parameters.p_orth.shape == (N_ORTHOGONAL_COMPONENTS, N_MODEL_VARIABLES)
    assert parameters.w_pred.shape == (N_MODEL_VARIABLES,)


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