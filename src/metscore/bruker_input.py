"""MetSCORE input preparation from Bruker NMR reports."""

from pathlib import Path

import pandas as pd

from metscore.bruker import (
    BrukerReport,
    bruker_reports_match_sample,
    normalize_bruker_sample_name,
    read_bruker_report,
)
from metscore.parameters import load_parameters
from metscore.tabular import predict


METABOLITE_VARIABLES = frozenset(
    {
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
    }
)

LIPOPROTEIN_VARIABLES = frozenset(
    {
        "L5TG",
        "HDFC",
        "H3TG",
        "H4FC",
        "V1PL",
        "L2FC",
        "L6TG",
    }
)


def prepare_bruker_input(
    first: BrukerReport,
    second: BrukerReport,
) -> pd.DataFrame:
    """Prepare one MetSCORE input row from two Bruker reports.

    The two reports may be provided in any order. One must contain metabolite
    quantification results and the other lipoprotein quantification results.

    Parameters
    ----------
    first
        First Bruker report.
    second
        Second Bruker report.

    Returns
    -------
    pandas.DataFrame
        One-row DataFrame containing ``sample_id`` followed by the MetSCORE
        model variables in their required order.

    Raises
    ------
    ValueError
        If the reports are not one metabolite and one lipoprotein report, do
        not correspond to the same sample, or do not contain all required
        MetSCORE variables with numeric values.
    """
    reports = {
        first.report_type: first,
        second.report_type: second,
    }

    if set(reports) != {"metabolites", "lipoproteins"}:
        raise ValueError(
            "Expected one metabolite report and one lipoprotein report."
        )

    if not bruker_reports_match_sample(first, second):
        raise ValueError(
            "Bruker reports do not correspond to the same sample: "
            f"{first.sample_name!r} and {second.sample_name!r}."
        )

    metabolite_report = reports["metabolites"]
    lipoprotein_report = reports["lipoproteins"]

    values: dict[str, float] = {}

    for variable in METABOLITE_VARIABLES:
        parameter = metabolite_report.parameters.get(variable)

        if parameter is None:
            raise ValueError(
                f"Metabolite report is missing required variable {variable!r}."
            )

        if parameter.value is None:
            raise ValueError(
                f"Metabolite variable {variable!r} has no numeric value."
            )

        if parameter.unit != "mmol/L":
            raise ValueError(
                f"Metabolite variable {variable!r} has unit "
                f"{parameter.unit!r}; expected 'mmol/L'."
            )

        values[variable] = parameter.value

    for variable in LIPOPROTEIN_VARIABLES:
        parameter = lipoprotein_report.parameters.get(variable)

        if parameter is None:
            raise ValueError(
                f"Lipoprotein report is missing required variable {variable!r}."
            )

        if parameter.value is None:
            raise ValueError(
                f"Lipoprotein variable {variable!r} has no numeric value."
            )

        if parameter.unit != "mg/dL":
            raise ValueError(
                f"Lipoprotein variable {variable!r} has unit "
                f"{parameter.unit!r}; expected 'mg/dL'."
            )

        values[variable] = parameter.value

    parameters = load_parameters()

    row = {
        "sample_id": normalize_bruker_sample_name(first.sample_name),
        **{
            variable: values[variable]
            for variable in parameters.variables
        },
    }

    return pd.DataFrame([row])


def prepare_bruker_input_from_files(
    first_file: str | Path,
    second_file: str | Path,
) -> pd.DataFrame:
    """Prepare one MetSCORE input row from two Bruker XML files.

    The files may be provided in any order. One must be a metabolite
    quantification report and the other a lipoprotein quantification report.

    Parameters
    ----------
    first_file
        Path to the first Bruker XML report.
    second_file
        Path to the second Bruker XML report.

    Returns
    -------
    pandas.DataFrame
        One-row DataFrame ready for MetSCORE prediction.
    """
    first_report = read_bruker_report(first_file)
    second_report = read_bruker_report(second_file)

    return prepare_bruker_input(
        first_report,
        second_report,
    )


def predict_bruker_files(
    first_file: str | Path,
    second_file: str | Path,
) -> pd.DataFrame:
    """Calculate MetSCORE from two Bruker XML reports.

    The two files may be provided in any order. One must contain metabolite
    quantification results and the other lipoprotein quantification results.
    The reports must correspond to the same sample.

    Metabolite values are expected in mmol/L and lipoprotein values in mg/dL.
    Required units are validated from the XML reports; no unit conversion is
    performed.

    Parameters
    ----------
    first_file
        Path to the first Bruker XML report.
    second_file
        Path to the second Bruker XML report.

    Returns
    -------
    pandas.DataFrame
        One-row DataFrame containing the normalized sample identifier,
        the 22 MetSCORE input variables, ``MetSCORE``, ``t_pred``, and
        one ``t_orth_<n>`` column per orthogonal component.

    Raises
    ------
    FileNotFoundError
        If either input file does not exist.
    ValueError
        If the reports cannot be parsed as compatible Bruker metabolite
        and lipoprotein reports, do not correspond to the same sample,
        are missing required MetSCORE variables, or contain unexpected
        units or invalid values.
    """
    data = prepare_bruker_input_from_files(
        first_file,
        second_file,
    )

    return predict(data)