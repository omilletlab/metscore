"""Utilities for reading Bruker NMR quantification reports."""

from dataclasses import dataclass
import math
from pathlib import Path
import xml.etree.ElementTree as ET


@dataclass(frozen=True, slots=True)
class BrukerParameter:
    """Normalized value extracted from a Bruker quantification parameter.

    Attributes
    ----------
    name
        Parameter name as reported in the XML file.
    value
        Numeric value selected from the available XML fields, or ``None`` if
        no numeric value is available.
    unit
        Unit associated with the selected value, if available.
    value_source
        XML attribute used as the source of the numeric value, such as
        ``rawConc``, ``value``, or ``conc``.
    """

    name: str
    value: float | None
    unit: str | None
    value_source: str


@dataclass(frozen=True, slots=True)
class BrukerReport:
    """Normalized representation of a Bruker quantification report.

    Attributes
    ----------
    sample_name
        Sample name reported in the XML file.
    sample_date
        Sample date exactly as reported in the XML file, if available.
    sample_type
        Sample type reported in the XML file, if available.
    result_version
        Version reported by the root ``RESULTS`` element.
    quantification_version
        Version reported by the ``QUANTIFICATION`` element.
    report_type
        Normalized report type: ``metabolites`` or ``lipoproteins``.
    parameters
        Parameters indexed by their reported names.
    """

    sample_name: str
    sample_date: str | None
    sample_type: str | None
    result_version: str | None
    quantification_version: str | None
    report_type: str
    parameters: dict[str, BrukerParameter]


def read_bruker_report(file_path: str | Path) -> BrukerReport:
    """Read and normalize a supported Bruker quantification XML report.

    The reader supports the metabolite and lipoprotein report structures
    observed across the available Bruker report versions. XML fields are
    normalized so downstream code does not need to depend on a specific
    report version.

    Parameters
    ----------
    file_path
        Path to the Bruker XML report.

    Returns
    -------
    BrukerReport
        Normalized report metadata and parameter values.

    Raises
    ------
    FileNotFoundError
        If the XML file does not exist.
    ValueError
        If the XML is malformed, its report type is unsupported, or required
        report structure is missing or inconsistent.
    """
    path = Path(file_path)

    if not path.is_file():
        raise FileNotFoundError(f"Bruker XML file does not exist: {path}")

    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"Invalid Bruker XML file: {path}") from exc

    if root.tag != "RESULTS":
        raise ValueError(
            f"Expected RESULTS as the XML root element in {path}, "
            f"found {root.tag!r}."
        )

    sample_element = root.find("SAMPLE")
    if sample_element is None:
        raise ValueError(f"Bruker XML report does not contain SAMPLE: {path}")

    quantification_element = root.find("QUANTIFICATION")
    if quantification_element is None:
        raise ValueError(
            f"Bruker XML report does not contain QUANTIFICATION: {path}"
        )

    sample_name = _clean_text(sample_element.get("name"))
    if sample_name is None:
        raise ValueError(f"Bruker XML report has no sample name: {path}")

    result_version = _clean_text(root.get("version"))
    quantification_version = _clean_text(
        quantification_element.get("version")
    )

    report_type = _detect_report_type(
        result_version=result_version,
        quantification_version=quantification_version,
    )

    parameter_elements = quantification_element.findall("PARAMETER")
    if not parameter_elements:
        raise ValueError(
            f"Bruker XML report contains no quantification parameters: {path}"
        )

    parameters: dict[str, BrukerParameter] = {}

    for parameter_element in parameter_elements:
        parameter = _read_parameter(parameter_element)

        existing = parameters.get(parameter.name)
        if existing is not None:
            if existing != parameter:
                raise ValueError(
                    "Bruker XML report contains conflicting duplicate "
                    f"parameter {parameter.name!r}: {path}"
                )
            continue

        parameters[parameter.name] = parameter

    return BrukerReport(
        sample_name=sample_name,
        sample_date=_clean_text(sample_element.get("date")),
        sample_type=_clean_text(sample_element.get("type")),
        result_version=result_version,
        quantification_version=quantification_version,
        report_type=report_type,
        parameters=parameters,
    )


def _detect_report_type(
    *,
    result_version: str | None,
    quantification_version: str | None,
) -> str:
    version_text = " ".join(
        value
        for value in (result_version, quantification_version)
        if value is not None
    ).lower()

    if "b.i.lisa" in version_text or "pl-5009" in version_text:
        return "lipoproteins"

    if "b.i.quant" in version_text or "quant-ps" in version_text:
        return "metabolites"

    raise ValueError(
        "Unsupported Bruker report type. Expected a B.I.Quant/Quant-PS "
        "metabolite report or a B.I.LISA/PL-5009 lipoprotein report."
    )


def _read_parameter(element: ET.Element) -> BrukerParameter:
    name = _clean_text(element.get("name"))
    if name is None:
        raise ValueError("Bruker PARAMETER element has no name.")

    value_element = element.find("VALUE")
    if value_element is None:
        raise ValueError(
            f"Bruker parameter {name!r} does not contain a VALUE element."
        )

    reldata_element = element.find("RELDATA")

    if reldata_element is not None:
        raw_conc = _parse_numeric_value(
            reldata_element.get("rawConc"),
            parameter_name=name,
            source="rawConc",
        )

        if raw_conc is not None:
            unit = (
                _clean_text(reldata_element.get("rawConcUnit"))
                or _clean_text(value_element.get("concUnit"))
                or _clean_text(value_element.get("unit"))
            )
            return BrukerParameter(
                name=name,
                value=raw_conc,
                unit=unit,
                value_source="rawConc",
            )

    value = _parse_numeric_value(
        value_element.get("value"),
        parameter_name=name,
        source="value",
    )

    if value is not None:
        return BrukerParameter(
            name=name,
            value=value,
            unit=_clean_text(value_element.get("unit")),
            value_source="value",
        )

    concentration = _parse_numeric_value(
        value_element.get("conc"),
        parameter_name=name,
        source="conc",
    )

    if concentration is not None:
        return BrukerParameter(
            name=name,
            value=concentration,
            unit=_clean_text(value_element.get("concUnit")),
            value_source="conc",
        )

    unit = (
        _clean_text(value_element.get("unit"))
        or _clean_text(value_element.get("concUnit"))
    )

    return BrukerParameter(
        name=name,
        value=None,
        unit=unit,
        value_source="unavailable",
    )


def _parse_numeric_value(
    value: str | None,
    *,
    parameter_name: str,
    source: str,
) -> float | None:
    cleaned = _clean_text(value)

    if cleaned is None:
        return None

    try:
        result = float(cleaned)
    except ValueError as exc:
        raise ValueError(
            f"Parameter {parameter_name!r} contains a non-numeric "
            f"{source} value: {cleaned!r}."
        ) from exc

    if not math.isfinite(result):
        raise ValueError(
            f"Parameter {parameter_name!r} contains a non-finite "
            f"{source} value: {cleaned!r}."
        )

    return result


def _clean_text(value: str | None) -> str | None:
    if value is None:
        return None

    cleaned = value.strip()

    if cleaned in {"", "-", "-/-"}:
        return None

    return cleaned