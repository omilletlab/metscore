import metscore


def test_public_api() -> None:
    assert metscore.PredictionResult is not None
    assert callable(metscore.predict)
    assert callable(metscore.predict_array)
    assert callable(metscore.predict_bruker_files)
