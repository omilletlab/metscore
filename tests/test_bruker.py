from pathlib import Path

import pytest

from metscore.bruker import read_bruker_report


FIXTURES_DIR = Path(__file__).parent / "fixtures" / "bruker"


def test_reads_metabolite_report_using_raw_concentration() -> None:
    report = read_bruker_report(
        FIXTURES_DIR / "metabolites_rawconc.xml"
    )

    assert report.report_type == "metabolites"
    assert report.sample_name == "sample_001"
    assert report.sample_date == "16-Sep-2026 20:14:15"
    assert report.sample_type == "plasma/serum"

    tmao = report.parameters["Trimethylamine-N-oxide"]
    assert tmao.value == pytest.approx(0.022)
    assert tmao.unit == "mmol/L"
    assert tmao.value_source == "rawConc"

    alanine = report.parameters["Alanine"]
    assert alanine.value == pytest.approx(0.514)
    assert alanine.unit == "mmol/L"
    assert alanine.value_source == "rawConc"

    glycine = report.parameters["Glycine"]
    assert glycine.value == pytest.approx(0.40)
    assert glycine.unit == "mmol/L"
    assert glycine.value_source == "conc"


def test_reads_legacy_metabolite_report_using_value() -> None:
    report = read_bruker_report(
        FIXTURES_DIR / "metabolites_legacy_value.xml"
    )

    assert report.report_type == "metabolites"
    assert report.sample_name == "sample_legacy"

    alanine = report.parameters["Alanine"]
    assert alanine.value == pytest.approx(0.48)
    assert alanine.unit == "mmol/L"
    assert alanine.value_source == "value"

    glucose = report.parameters["Glucose"]
    assert glucose.value == pytest.approx(4.1)
    assert glucose.unit == "mmol/L"
    assert glucose.value_source == "value"


def test_reads_lipoprotein_report_and_collapses_identical_duplicates() -> None:
    report = read_bruker_report(
        FIXTURES_DIR / "lipoproteins_legacy.xml"
    )

    assert report.report_type == "lipoproteins"
    assert report.sample_name == "sample_legacy"

    assert set(report.parameters) == {
        "LDCH",
        "HDFC",
        "L5TG",
    }

    ldch = report.parameters["LDCH"]
    assert ldch.value == pytest.approx(149.95)
    assert ldch.unit == "mg/dL"
    assert ldch.value_source == "value"

    hdfc = report.parameters["HDFC"]
    assert hdfc.value == pytest.approx(11.02)

    l5tg = report.parameters["L5TG"]
    assert l5tg.value == pytest.approx(3.85)


def test_rejects_conflicting_duplicate_parameters(tmp_path: Path) -> None:
    xml_file = tmp_path / "conflicting_duplicates.xml"

    xml_file.write_text(
        """\
<?xml version="1.0" encoding="utf-8"?>
<RESULTS version="B.I.LISA 1.1.0+test">
   <SAMPLE name="sample_001" type="plasma/serum"/>
   <QUANTIFICATION version="PL-5009-01/002">
      <PARAMETER name="HDFC" type="prediction">
         <VALUE unit="mg/dL" value="11.02"/>
      </PARAMETER>
      <PARAMETER name="HDFC" type="prediction">
         <VALUE unit="mg/dL" value="12.34"/>
      </PARAMETER>
   </QUANTIFICATION>
</RESULTS>
""",
        encoding="utf-8",
    )

    with pytest.raises(
        ValueError,
        match="conflicting duplicate parameter 'HDFC'",
    ):
        read_bruker_report(xml_file)