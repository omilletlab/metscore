import metscore


def test_public_api() -> None:
    assert callable(metscore.predict_array)
    assert metscore.PredictionResult is not None