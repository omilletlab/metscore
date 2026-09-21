from metscore.bruker import BrukerParameter, BrukerReport
from metscore.bruker_input import (
    LIPOPROTEIN_VARIABLES,
    METABOLITE_VARIABLES,
    predict_bruker_files,
    prepare_bruker_input,
    prepare_bruker_input_from_files,
)
from metscore.parameters import load_parameters
import pytest
from pathlib import Path


def test_bruker_variables_match_model_variables() -> None:
    parameters = load_parameters()

    bruker_variables = METABOLITE_VARIABLES | LIPOPROTEIN_VARIABLES

    assert bruker_variables == set(parameters.variables)


def test_prepares_bruker_input_in_model_variable_order() -> None:
    metabolite_parameters = {
        name: BrukerParameter(
            name=name,
            value=float(index),
            unit="mmol/L",
            value_source="rawConc",
        )
        for index, name in enumerate(
            sorted(METABOLITE_VARIABLES),
            start=1,
        )
    }

    lipoprotein_parameters = {
        name: BrukerParameter(
            name=name,
            value=float(index),
            unit="mg/dL",
            value_source="value",
        )
        for index, name in enumerate(
            sorted(LIPOPROTEIN_VARIABLES),
            start=101,
        )
    }

    metabolite_report = BrukerReport(
        sample_name="19S20442_expno10.100000.11r",
        sample_date=None,
        sample_type="plasma/serum",
        result_version="Quant-PS 2.0.0",
        quantification_version="Quant-PS 2.0.0",
        report_type="metabolites",
        parameters=metabolite_parameters,
    )

    lipoprotein_report = BrukerReport(
        sample_name="19S20442_expno10.100000.10r",
        sample_date=None,
        sample_type="plasma/serum",
        result_version="Version 1.0.0",
        quantification_version="PL-5009-01/001",
        report_type="lipoproteins",
        parameters=lipoprotein_parameters,
    )

    result = prepare_bruker_input(
        lipoprotein_report,
        metabolite_report,
    )

    model_parameters = load_parameters()

    assert result.shape == (1, len(model_parameters.variables) + 1)
    assert list(result.columns) == [
        "sample_id",
        *model_parameters.variables,
    ]
    assert result.loc[0, "sample_id"] == "19S20442"

    for variable in model_parameters.variables:
        source_report = (
            metabolite_report
            if variable in METABOLITE_VARIABLES
            else lipoprotein_report
        )

        assert (
            result.loc[0, variable]
            == source_report.parameters[variable].value
        )


def test_rejects_two_reports_of_the_same_type() -> None:
    report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="metabolites",
        parameters={},
    )

    with pytest.raises(
        ValueError,
        match="Expected one metabolite report and one lipoprotein report",
    ):
        prepare_bruker_input(report, report)


def test_rejects_reports_from_different_samples() -> None:
    metabolite_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="metabolites",
        parameters={},
    )

    lipoprotein_report = BrukerReport(
        sample_name="sample_002",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="lipoproteins",
        parameters={},
    )

    with pytest.raises(
        ValueError,
        match="Bruker reports do not correspond to the same sample",
    ):
        prepare_bruker_input(
            metabolite_report,
            lipoprotein_report,
        )


def test_rejects_missing_required_variable() -> None:
    metabolite_parameters = {
        name: BrukerParameter(
            name=name,
            value=1.0,
            unit="mmol/L",
            value_source="rawConc",
        )
        for name in METABOLITE_VARIABLES
        if name != "Alanine"
    }

    lipoprotein_parameters = {
        name: BrukerParameter(
            name=name,
            value=1.0,
            unit="mg/dL",
            value_source="value",
        )
        for name in LIPOPROTEIN_VARIABLES
    }

    metabolite_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="metabolites",
        parameters=metabolite_parameters,
    )

    lipoprotein_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="lipoproteins",
        parameters=lipoprotein_parameters,
    )

    with pytest.raises(
        ValueError,
        match="Metabolite report is missing required variable 'Alanine'",
    ):
        prepare_bruker_input(
            metabolite_report,
            lipoprotein_report,
        )


def test_rejects_required_variable_without_numeric_value() -> None:
    metabolite_parameters = {
        name: BrukerParameter(
            name=name,
            value=None if name == "Alanine" else 1.0,
            unit="mmol/L",
            value_source="unavailable" if name == "Alanine" else "rawConc",
        )
        for name in METABOLITE_VARIABLES
    }

    lipoprotein_parameters = {
        name: BrukerParameter(
            name=name,
            value=1.0,
            unit="mg/dL",
            value_source="value",
        )
        for name in LIPOPROTEIN_VARIABLES
    }

    metabolite_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="metabolites",
        parameters=metabolite_parameters,
    )

    lipoprotein_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="lipoproteins",
        parameters=lipoprotein_parameters,
    )

    with pytest.raises(
        ValueError,
        match="Metabolite variable 'Alanine' has no numeric value",
    ):
        prepare_bruker_input(
            metabolite_report,
            lipoprotein_report,
        )


def test_rejects_metabolite_with_unexpected_unit() -> None:
    metabolite_parameters = {
        name: BrukerParameter(
            name=name,
            value=1.0,
            unit="mg/dL" if name == "Alanine" else "mmol/L",
            value_source="rawConc",
        )
        for name in METABOLITE_VARIABLES
    }

    lipoprotein_parameters = {
        name: BrukerParameter(
            name=name,
            value=1.0,
            unit="mg/dL",
            value_source="value",
        )
        for name in LIPOPROTEIN_VARIABLES
    }

    metabolite_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="metabolites",
        parameters=metabolite_parameters,
    )

    lipoprotein_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="lipoproteins",
        parameters=lipoprotein_parameters,
    )

    with pytest.raises(
        ValueError,
        match="Metabolite variable 'Alanine' has unit 'mg/dL'; expected 'mmol/L'",
    ):
        prepare_bruker_input(
            metabolite_report,
            lipoprotein_report,
        )


def test_rejects_lipoprotein_with_unexpected_unit() -> None:
    metabolite_parameters = {
        name: BrukerParameter(
            name=name,
            value=1.0,
            unit="mmol/L",
            value_source="rawConc",
        )
        for name in METABOLITE_VARIABLES
    }

    lipoprotein_parameters = {
        name: BrukerParameter(
            name=name,
            value=1.0,
            unit="mmol/L" if name == "HDFC" else "mg/dL",
            value_source="value",
        )
        for name in LIPOPROTEIN_VARIABLES
    }

    metabolite_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="metabolites",
        parameters=metabolite_parameters,
    )

    lipoprotein_report = BrukerReport(
        sample_name="sample_001",
        sample_date=None,
        sample_type="plasma/serum",
        result_version=None,
        quantification_version=None,
        report_type="lipoproteins",
        parameters=lipoprotein_parameters,
    )

    with pytest.raises(
        ValueError,
        match="Lipoprotein variable 'HDFC' has unit 'mmol/L'; expected 'mg/dL'",
    ):
        prepare_bruker_input(
            metabolite_report,
            lipoprotein_report,
        )


def test_prepares_bruker_input_from_xml_files(tmp_path: Path) -> None:
    metabolite_xml = tmp_path / "metabolites.xml"
    lipoprotein_xml = tmp_path / "lipoproteins.xml"

    metabolite_parameters = "\n".join(
        f"""
      <PARAMETER name="{name}" type="quantification">
         <VALUE conc="1.0" concUnit="mmol/L"/>
         <RELDATA rawConc="1.0" rawConcUnit="mmol/L"/>
      </PARAMETER>"""
        for name in sorted(METABOLITE_VARIABLES)
    )

    lipoprotein_parameters = "\n".join(
        f"""
      <PARAMETER name="{name}" type="prediction">
         <VALUE value="1.0" unit="mg/dL"/>
      </PARAMETER>"""
        for name in sorted(LIPOPROTEIN_VARIABLES)
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

    result = prepare_bruker_input_from_files(
        lipoprotein_xml,
        metabolite_xml,
    )

    parameters = load_parameters()

    assert result.shape == (1, len(parameters.variables) + 1)
    assert list(result.columns) == [
        "sample_id",
        *parameters.variables,
    ]
    assert result.loc[0, "sample_id"] == "sample_001"

    for variable in parameters.variables:
        assert result.loc[0, variable] == 1.0


def test_predicts_metscore_from_bruker_xml_files(tmp_path: Path) -> None:
    metabolite_xml = tmp_path / "metabolites.xml"
    lipoprotein_xml = tmp_path / "lipoproteins.xml"

    metabolite_parameters = "\n".join(
        f"""
      <PARAMETER name="{name}" type="quantification">
         <VALUE conc="1.0" concUnit="mmol/L"/>
         <RELDATA rawConc="1.0" rawConcUnit="mmol/L"/>
      </PARAMETER>"""
        for name in sorted(METABOLITE_VARIABLES)
    )

    lipoprotein_parameters = "\n".join(
        f"""
      <PARAMETER name="{name}" type="prediction">
         <VALUE value="1.0" unit="mg/dL"/>
      </PARAMETER>"""
        for name in sorted(LIPOPROTEIN_VARIABLES)
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

    result = predict_bruker_files(
        metabolite_xml,
        lipoprotein_xml,
    )

    parameters = load_parameters()

    assert result.shape == (
        1,
        len(parameters.variables) + 4,
    )
    assert result.loc[0, "sample_id"] == "sample_001"

    assert "MetSCORE" in result.columns
    assert "t_pred" in result.columns
    assert "t_orth_1" in result.columns

    assert 0.0 <= result.loc[0, "MetSCORE"] <= 1.0


def test_bruker_xml_regression_matches_original_r_model() -> None:
    fixture_dir = Path(__file__).parent / "fixtures" / "bruker"

    result = predict_bruker_files(
        fixture_dir / "metabolites_regression.xml",
        fixture_dir / "lipoproteins_regression.xml",
    )

    assert result.loc[0, "sample_id"] == "sample_regression_001"

    assert result.loc[0, "t_pred"] == pytest.approx(
        1.09254067903752,
        rel=1e-12,
        abs=1e-12,
    )
    assert result.loc[0, "t_orth_1"] == pytest.approx(
        2.32953294534929,
        rel=1e-12,
        abs=1e-12,
    )
    assert result.loc[0, "MetSCORE"] == pytest.approx(
        0.388609410044161,
        rel=1e-12,
        abs=1e-12,
    )
