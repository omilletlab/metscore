from pathlib import Path

import pytest

from metscore.examples_cli import export_examples, main
from metscore.resources import (
    EXAMPLE_DATA_CSV,
    EXAMPLE_DATA_XLSX,
    EXAMPLE_LIPOPROTEINS_XML,
    EXAMPLE_METABOLITES_XML,
)


def test_export_examples_creates_expected_files(tmp_path: Path) -> None:
    destination = tmp_path / "examples"

    result = export_examples(destination)

    assert result == destination

    expected_files = {
        destination / "example_data.csv": EXAMPLE_DATA_CSV,
        destination / "example_data.xlsx": EXAMPLE_DATA_XLSX,
        destination / "bruker" / "sample_001_metabolites.xml": EXAMPLE_METABOLITES_XML,
        destination
        / "bruker"
        / "sample_001_lipoproteins.xml": EXAMPLE_LIPOPROTEINS_XML,
    }

    for exported_file, packaged_file in expected_files.items():
        assert exported_file.is_file()
        assert exported_file.read_bytes() == packaged_file.read_bytes()


def test_examples_cli_uses_default_destination(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    capsys: pytest.CaptureFixture[str],
) -> None:
    monkeypatch.chdir(tmp_path)

    exit_code = main([])

    assert exit_code == 0
    assert (tmp_path / "metscore-examples" / "example_data.csv").is_file()
    assert (
        tmp_path / "metscore-examples" / "bruker" / "sample_001_metabolites.xml"
    ).is_file()

    captured = capsys.readouterr()
    assert "Example inputs written to:" in captured.out


def test_examples_cli_refuses_existing_destination(
    tmp_path: Path,
) -> None:
    destination = tmp_path / "existing"
    destination.mkdir()

    with pytest.raises(SystemExit) as exc_info:
        main([str(destination)])

    assert exc_info.value.code == 2
