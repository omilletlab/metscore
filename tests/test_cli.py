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