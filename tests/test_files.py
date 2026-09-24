from pathlib import Path

import pandas as pd
import pytest

from metscore.files import predict_bruker_file_pair, predict_file, read_table


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


def test_predict_bruker_file_pair_uses_sample_id_for_default_output(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    metabolite_xml = tmp_path / "metabolites.xml"
    lipoprotein_xml = tmp_path / "lipoproteins.xml"

    metabolite_names = [
        "Alanine",
        "Citric acid",
        "Creatine",
        "Creatinine",
        "Formic acid",
        "Glucose",
        "Glutamic acid",
        "Glycine",
        "Isoleucine",
        "Lactic acid",
        "Methionine",
        "Phenylalanine",
        "Proline",
        "Sarcosine",
        "Trimethylamine-N-oxide",
    ]

    lipoprotein_names = [
        "L5TG",
        "HDFC",
        "H3TG",
        "H4FC",
        "V1PL",
        "L2FC",
        "L6TG",
    ]

    metabolite_parameters = "\n".join(
        f"""
      <PARAMETER name="{name}" type="quantification">
         <VALUE conc="1.0" concUnit="mmol/L"/>
         <RELDATA rawConc="1.0" rawConcUnit="mmol/L"/>
      </PARAMETER>"""
        for name in metabolite_names
    )

    lipoprotein_parameters = "\n".join(
        f"""
      <PARAMETER name="{name}" type="prediction">
         <VALUE value="1.0" unit="mg/dL"/>
      </PARAMETER>"""
        for name in lipoprotein_names
    )

    metabolite_xml.write_text(
        f"""\
<?xml version="1.0" encoding="utf-8"?>
<RESULTS version="B.I.Quant-PS 2.1.0+test">
   <SAMPLE name="sample_001" type="plasma/serum"/>
   <QUANTIFICATION version="2.1.0+test">
{metabolite_parameters}
   </QUANTIFICATION>
</RESULTS>
""",
        encoding="utf-8",
    )

    lipoprotein_xml.write_text(
        f"""\
<?xml version="1.0" encoding="utf-8"?>
<RESULTS version="B.I.LISA 1.1.0+test">
   <SAMPLE name="sample_001" type="plasma/serum"/>
   <QUANTIFICATION version="PL-5009-01/002">
{lipoprotein_parameters}
   </QUANTIFICATION>
</RESULTS>
""",
        encoding="utf-8",
    )

    monkeypatch.chdir(tmp_path)

    output = predict_bruker_file_pair(
        metabolite_xml,
        lipoprotein_xml,
    )

    expected = tmp_path / "sample_001_metscore.csv"

    assert output == expected
    assert output.is_file()

    result = pd.read_csv(output)

    assert len(result) == 1
    assert result.loc[0, "sample_id"] == "sample_001"
    assert list(result.columns[-3:]) == [
        "MetSCORE",
        "t_pred",
        "t_orth_1",
    ]


def test_predict_bruker_file_pair_uses_explicit_output_path(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_xml = tmp_path / "metabolites.xml"
    second_xml = tmp_path / "lipoproteins.xml"

    first_xml.touch()
    second_xml.touch()

    prediction = pd.DataFrame(
        {
            "sample_id": ["sample_001"],
            "MetSCORE": [0.5],
            "t_pred": [1.0],
            "t_orth_1": [0.0],
        }
    )

    monkeypatch.setattr(
        "metscore.files._predict_bruker_files",
        lambda first, second: prediction,
    )

    output = tmp_path / "predictions.csv"

    returned_path = predict_bruker_file_pair(
        first_xml,
        second_xml,
        output_path=output,
    )

    assert returned_path == output
    assert output.is_file()

    result = pd.read_csv(output)

    assert result.loc[0, "sample_id"] == "sample_001"
    assert result.loc[0, "MetSCORE"] == pytest.approx(0.5)


def test_predict_bruker_file_pair_refuses_to_overwrite_existing_file(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_xml = tmp_path / "metabolites.xml"
    second_xml = tmp_path / "lipoproteins.xml"

    first_xml.touch()
    second_xml.touch()

    prediction = pd.DataFrame(
        {
            "sample_id": ["sample_001"],
            "MetSCORE": [0.5],
            "t_pred": [1.0],
            "t_orth_1": [0.0],
        }
    )

    monkeypatch.setattr(
        "metscore.files._predict_bruker_files",
        lambda first, second: prediction,
    )

    output = tmp_path / "predictions.csv"
    output.touch()

    with pytest.raises(
        FileExistsError,
        match="Output file already exists",
    ):
        predict_bruker_file_pair(
            first_xml,
            second_xml,
            output_path=output,
        )


def test_predict_bruker_file_pair_rejects_non_xml_input(
    tmp_path: Path,
) -> None:
    first_file = tmp_path / "metabolites.csv"
    second_file = tmp_path / "lipoproteins.xml"

    first_file.touch()
    second_file.touch()

    with pytest.raises(
        ValueError,
        match="Expected a Bruker XML file",
    ):
        predict_bruker_file_pair(
            first_file,
            second_file,
        )


def test_predict_bruker_file_pair_rejects_same_input_file(
    tmp_path: Path,
) -> None:
    xml_file = tmp_path / "sample.xml"
    xml_file.touch()

    with pytest.raises(
        ValueError,
        match="Bruker XML input paths must be different",
    ):
        predict_bruker_file_pair(
            xml_file,
            xml_file,
        )


def test_predict_bruker_file_pair_rejects_missing_input(
    tmp_path: Path,
) -> None:
    first_xml = tmp_path / "missing.xml"
    second_xml = tmp_path / "lipoproteins.xml"

    second_xml.touch()

    with pytest.raises(
        FileNotFoundError,
        match="Input file does not exist",
    ):
        predict_bruker_file_pair(
            first_xml,
            second_xml,
        )


def test_predict_bruker_file_pair_rejects_unsafe_sample_id(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    first_xml = tmp_path / "metabolites.xml"
    second_xml = tmp_path / "lipoproteins.xml"

    first_xml.touch()
    second_xml.touch()

    prediction = pd.DataFrame(
        {
            "sample_id": ["../sample_001"],
            "MetSCORE": [0.5],
            "t_pred": [1.0],
            "t_orth_1": [0.0],
        }
    )

    monkeypatch.setattr(
        "metscore.files._predict_bruker_files",
        lambda first, second: prediction,
    )

    with pytest.raises(
        ValueError,
        match="cannot be used safely as an output filename",
    ):
        predict_bruker_file_pair(
            first_xml,
            second_xml,
        )

def test_read_table_rejects_duplicate_csv_headers(tmp_path):
    path = tmp_path / "duplicate.csv"
    path.write_text(
        "Alanine,Glucose,Alanine\n1,2,3\n",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match=r"duplicate column names.*Alanine",
    ):
        read_table(path)


def test_read_table_rejects_duplicate_excel_headers(tmp_path):
    path = tmp_path / "duplicate.xlsx"

    pd.DataFrame(
        [[1, 2, 3]],
        columns=["Alanine", "Glucose", "Alanine"],
    ).to_excel(
        path,
        index=False,
        engine="openpyxl",
    )

    with pytest.raises(
        ValueError,
        match=r"duplicate column names.*Alanine",
    ):
        read_table(path)
