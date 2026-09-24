from __future__ import annotations

from importlib.util import find_spec
from os import PathLike
from pathlib import Path

import pandas as pd

from metscore.bruker_input import predict_bruker_files as _predict_bruker_files
from metscore.tabular import predict


_SUPPORTED_SUFFIXES = {".csv", ".xlsx"}
_XML_SUFFIX = ".xml"


def predict_file(
    input_path: str | PathLike[str],
    output_path: str | PathLike[str] | None = None,
) -> Path:
    """Calculate MetSCORE from a CSV or Excel file.

    The input file is read as a tabular dataset, predictions are appended
    to the original columns, and the resulting table is written to a new
    file.

    Parameters
    ----------
    input_path
        Path to a CSV or XLSX input file.
    output_path
        Path for the prediction output. If omitted, ``_metscore`` is
        appended to the input filename.

    Returns
    -------
    pathlib.Path
        Path to the generated output file.

    Raises
    ------
    FileNotFoundError
        If the input file or output directory does not exist.
    FileExistsError
        If the output file already exists.
    ValueError
        If an unsupported file format is used or input and output paths
        refer to the same file.
    ImportError
        If Excel support is requested but the optional dependency is not
        installed.
    """
    input_file = Path(input_path)

    if not input_file.is_file():
        raise FileNotFoundError(f"Input file does not exist: {input_file}")

    _validate_suffix(input_file)

    if output_path is None:
        output_file = Path.cwd() / (
            f"{input_file.stem}_metscore{input_file.suffix}"
        )
    else:
        output_file = Path(output_path)

    _validate_suffix(output_file)

    if input_file.resolve() == output_file.resolve():
        raise ValueError("Input and output paths must be different.")

    _validate_output_file(output_file)

    data = _read_table(input_file)
    result = predict(data)
    _write_table(result, output_file)

    return output_file


def predict_bruker_file_pair(
    first_path: str | PathLike[str],
    second_path: str | PathLike[str],
    output_path: str | PathLike[str] | None = None,
) -> Path:
    """Calculate MetSCORE from two Bruker XML reports.

    The XML files may be provided in any order. One must contain metabolite
    quantification results and the other lipoprotein quantification results.

    Parameters
    ----------
    first_path
        Path to the first Bruker XML report.
    second_path
        Path to the second Bruker XML report.
    output_path
        Path for the prediction output. If omitted, a CSV file named from
        the normalized sample identifier is created in the current working
        directory.

    Returns
    -------
    pathlib.Path
        Path to the generated output file.

    Raises
    ------
    FileNotFoundError
        If an input file or output directory does not exist.
    FileExistsError
        If the output file already exists.
    ValueError
        If the two input paths are identical, an input is not an XML file,
        the Bruker reports are incompatible, or the output format is not
        supported.
    ImportError
        If Excel output is requested but the optional dependency is not
        installed.
    """
    first_file = Path(first_path)
    second_file = Path(second_path)

    for input_file in (first_file, second_file):
        if not input_file.is_file():
            raise FileNotFoundError(
                f"Input file does not exist: {input_file}"
            )

        if input_file.suffix.lower() != _XML_SUFFIX:
            raise ValueError(
                f"Expected a Bruker XML file, got: {input_file}"
            )

    if first_file.resolve() == second_file.resolve():
        raise ValueError("Bruker XML input paths must be different.")

    result = _predict_bruker_files(
        first_file,
        second_file,
    )

    if output_path is None:
        sample_id = str(result.iloc[0]["sample_id"])
        output_file = _default_bruker_output_path(sample_id)
    else:
        output_file = Path(output_path)

    _validate_suffix(output_file)
    _validate_output_file(output_file)

    _write_table(result, output_file)

    return output_file


def _default_bruker_output_path(sample_id: str) -> Path:
    if (
        not sample_id
        or sample_id in {".", ".."}
        or "/" in sample_id
        or "\\" in sample_id
    ):
        raise ValueError(
            "Bruker sample identifier cannot be used safely as an output "
            f"filename: {sample_id!r}"
        )

    return Path.cwd() / f"{sample_id}_metscore.csv"


def _validate_output_file(path: Path) -> None:
    if not path.parent.exists():
        raise FileNotFoundError(
            f"Output directory does not exist: {path.parent}"
        )

    if path.exists():
        raise FileExistsError(
            f"Output file already exists: {path}"
        )


def _validate_suffix(path: Path) -> None:
    if path.suffix.lower() not in _SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(_SUPPORTED_SUFFIXES))
        raise ValueError(
            f"Unsupported file format '{path.suffix}'. "
            f"Supported formats: {supported}"
        )


def read_table(source, *, filename: str | None = None) -> pd.DataFrame:
    source_name = filename

    if source_name is None:
        if isinstance(source, (str, PathLike)):
            source_name = str(source)
        else:
            source_name = getattr(source, "name", None)

    if not source_name:
        raise ValueError(
            "A filename is required to determine the input file type."
        )

    source_path = Path(source_name)
    _validate_suffix(source_path)
    suffix = source_path.suffix.lower()

    if suffix == ".xlsx":
        _require_excel_support()

    _validate_raw_header(source, suffix)
    _rewind(source)

    if suffix == ".csv":
        return pd.read_csv(source)

    return pd.read_excel(source, engine="openpyxl")


def _read_table(path: Path) -> pd.DataFrame:
    return read_table(path)


def _validate_raw_header(source, suffix: str) -> None:
    _rewind(source)

    if suffix == ".csv":
        header = pd.read_csv(
            source,
            header=None,
            nrows=1,
            keep_default_na=False,
        )
    else:
        header = pd.read_excel(
            source,
            header=None,
            nrows=1,
            keep_default_na=False,
            engine="openpyxl",
        )

    if header.empty:
        return

    seen = set()
    duplicates = []

    for value in header.iloc[0].tolist():
        if pd.isna(value):
            continue

        name = str(value)

        if not name:
            continue

        if name in seen and name not in duplicates:
            duplicates.append(name)

        seen.add(name)

    if duplicates:
        names = ", ".join(duplicates)
        raise ValueError(
            f"Input contains duplicate column names: {names}"
        )


def _rewind(source) -> None:
    seek = getattr(source, "seek", None)

    if seek is not None:
        seek(0)


def _write_table(data: pd.DataFrame, path: Path) -> None:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        data.to_csv(path, index=False)
        return

    _require_excel_support()
    data.to_excel(path, index=False, engine="openpyxl")


def _require_excel_support() -> None:
    if find_spec("openpyxl") is None:
        raise ImportError(
            "Excel support requires the optional 'excel' dependency. "
            'Install it with: pip install "metscore[excel]"'
        )