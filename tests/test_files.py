from pathlib import Path

import pandas as pd
import pytest

from metscore.files import predict_file


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DATA = PROJECT_ROOT / "examples" / "example_data.csv"


def test_predict_file_uses_current_directory_by_default(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    output = predict_file(EXAMPLE_DATA)

    expected = tmp_path / "example_data_metscore.csv"

    assert output == expected
    assert output.is_file()

    input_data = pd.read_csv(EXAMPLE_DATA)
    result = pd.read_csv(output)

    assert len(result) == len(input_data)
    assert list(result.columns[-3:]) == [
        "MetSCORE",
        "t_pred",
        "t_orth_1",
    ]


def test_predict_file_uses_explicit_output_path(
    tmp_path: Path,
) -> None:
    output = tmp_path / "predictions.csv"

    returned_path = predict_file(
        EXAMPLE_DATA,
        output_path=output,
    )

    assert returned_path == output
    assert output.is_file()


def test_predict_file_refuses_to_overwrite_existing_file(
    tmp_path: Path,
) -> None:
    output = tmp_path / "predictions.csv"
    output.touch()

    with pytest.raises(
        FileExistsError,
        match="Output file already exists",
    ):
        predict_file(
            EXAMPLE_DATA,
            output_path=output,
        )


def test_predict_file_rejects_unsupported_format(
    tmp_path: Path,
) -> None:
    input_file = tmp_path / "samples.txt"
    input_file.write_text("example", encoding="utf-8")

    with pytest.raises(
        ValueError,
        match="Unsupported file format",
    ):
        predict_file(input_file)


def test_predict_file_rejects_missing_input(
    tmp_path: Path,
) -> None:
    missing_input = tmp_path / "missing.csv"

    with pytest.raises(
        FileNotFoundError,
        match="Input file does not exist",
    ):
        predict_file(missing_input)


def test_predict_file_rejects_missing_output_directory(
    tmp_path: Path,
) -> None:
    output = tmp_path / "missing_directory" / "predictions.csv"

    with pytest.raises(
        FileNotFoundError,
        match="Output directory does not exist",
    ):
        predict_file(
            EXAMPLE_DATA,
            output_path=output,
        )


def test_predict_file_rejects_same_input_and_output() -> None:
    with pytest.raises(
        ValueError,
        match="Input and output paths must be different",
    ):
        predict_file(
            EXAMPLE_DATA,
            output_path=EXAMPLE_DATA,
        )


def test_predict_file_resolves_relative_output_from_current_directory(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.chdir(tmp_path)

    output = Path("predictions.csv")

    returned_path = predict_file(
        EXAMPLE_DATA,
        output_path=output,
    )

    assert returned_path == output
    assert (tmp_path / output).is_file()


def test_predict_file_supports_excel(
    tmp_path: Path,
) -> None:
    pytest.importorskip("openpyxl")

    data = pd.read_csv(EXAMPLE_DATA)

    input_file = tmp_path / "samples.xlsx"
    output_file = tmp_path / "predictions.xlsx"

    data.to_excel(
        input_file,
        index=False,
        engine="openpyxl",
    )

    returned_path = predict_file(
        input_file,
        output_path=output_file,
    )

    assert returned_path == output_file
    assert output_file.is_file()

    result = pd.read_excel(
        output_file,
        engine="openpyxl",
    )

    assert len(result) == len(data)
    assert list(result.columns[-3:]) == [
        "MetSCORE",
        "t_pred",
        "t_orth_1",
    ]


def test_predict_file_explains_missing_excel_dependency(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    input_file = tmp_path / "samples.xlsx"
    input_file.touch()

    monkeypatch.setattr(
        "metscore.files.find_spec",
        lambda name: None,
    )

    with pytest.raises(
        ImportError,
        match="Excel support requires the optional 'excel' dependency",
    ):
        predict_file(input_file)