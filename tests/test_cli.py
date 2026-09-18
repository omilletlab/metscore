from pathlib import Path

import pytest

from metscore.cli import main


PROJECT_ROOT = Path(__file__).resolve().parents[1]
EXAMPLE_DATA = PROJECT_ROOT / "examples" / "example_data.csv"


def test_cli_creates_default_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main([str(EXAMPLE_DATA)])

    expected_output = tmp_path / "example_data_metscore.csv"

    assert exit_code == 0
    assert expected_output.is_file()

    captured = capsys.readouterr()
    assert "example_data_metscore.csv" in captured.out


def test_cli_accepts_explicit_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "predictions.csv"

    exit_code = main(
        [
            str(EXAMPLE_DATA),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0
    assert output.is_file()

    captured = capsys.readouterr()
    assert str(output) in captured.out


def test_cli_reports_missing_input(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    missing_input = tmp_path / "missing.csv"

    with pytest.raises(SystemExit) as exc_info:
        main([str(missing_input)])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "Input file does not exist" in captured.err


def test_cli_reports_existing_output(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    output = tmp_path / "predictions.csv"
    output.touch()

    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                str(EXAMPLE_DATA),
                "--output",
                str(output),
            ]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert "Output file already exists" in captured.err


def test_cli_help(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(["--help"])

    assert exc_info.value.code == 0

    captured = capsys.readouterr()
    assert "Calculate MetSCORE from serum NMR data." in captured.out
    assert "--output" in captured.out


@pytest.mark.parametrize(
    "input_order",
    [
        ("metabolites.xml", "lipoproteins.xml"),
        ("lipoproteins.xml", "metabolites.xml"),
    ],
)
def test_cli_accepts_two_bruker_xml_inputs_in_any_order(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
    input_order: tuple[str, str],
) -> None:
    first = tmp_path / input_order[0]
    second = tmp_path / input_order[1]

    first.touch()
    second.touch()

    expected_output = tmp_path / "sample_001_metscore.csv"

    def fake_predict_bruker_file_pair(
        first_path: Path,
        second_path: Path,
        output_path: Path | None = None,
    ) -> Path:
        assert first_path == first
        assert second_path == second
        assert output_path is None
        return expected_output

    monkeypatch.setattr(
        "metscore.cli.predict_bruker_file_pair",
        fake_predict_bruker_file_pair,
    )

    exit_code = main(
        [
            str(first),
            str(second),
        ]
    )

    assert exit_code == 0

    captured = capsys.readouterr()
    assert str(expected_output) in captured.out


def test_cli_accepts_explicit_output_for_bruker_xml(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    first = tmp_path / "metabolites.xml"
    second = tmp_path / "lipoproteins.xml"
    output = tmp_path / "predictions.csv"

    first.touch()
    second.touch()

    def fake_predict_bruker_file_pair(
        first_path: Path,
        second_path: Path,
        output_path: Path | None = None,
    ) -> Path:
        assert first_path == first
        assert second_path == second
        assert output_path == output
        return output

    monkeypatch.setattr(
        "metscore.cli.predict_bruker_file_pair",
        fake_predict_bruker_file_pair,
    )

    exit_code = main(
        [
            str(first),
            str(second),
            "--output",
            str(output),
        ]
    )

    assert exit_code == 0

    captured = capsys.readouterr()
    assert str(output) in captured.out


def test_cli_rejects_single_bruker_xml(
    tmp_path: Path,
    capsys: pytest.CaptureFixture[str],
) -> None:
    xml_file = tmp_path / "metabolites.xml"
    xml_file.touch()

    with pytest.raises(SystemExit) as exc_info:
        main([str(xml_file)])

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert (
        "Bruker XML prediction requires two XML input files"
        in captured.err
    )


def test_cli_rejects_more_than_two_inputs(
    capsys: pytest.CaptureFixture[str],
) -> None:
    with pytest.raises(SystemExit) as exc_info:
        main(
            [
                "first.xml",
                "second.xml",
                "third.xml",
            ]
        )

    assert exc_info.value.code == 2

    captured = capsys.readouterr()
    assert (
        "Expected one CSV/XLSX input file or two Bruker XML input files"
        in captured.err
    )