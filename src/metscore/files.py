from __future__ import annotations

from importlib.util import find_spec
from os import PathLike
from pathlib import Path

import pandas as pd

from metscore.tabular import predict


_SUPPORTED_SUFFIXES = {".csv", ".xlsx"}


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

    if not output_file.parent.exists():
        raise FileNotFoundError(
            f"Output directory does not exist: {output_file.parent}"
        )

    if output_file.exists():
        raise FileExistsError(
            f"Output file already exists: {output_file}"
        )

    data = _read_table(input_file)
    result = predict(data)
    _write_table(result, output_file)

    return output_file


def _validate_suffix(path: Path) -> None:
    if path.suffix.lower() not in _SUPPORTED_SUFFIXES:
        supported = ", ".join(sorted(_SUPPORTED_SUFFIXES))
        raise ValueError(
            f"Unsupported file format '{path.suffix}'. "
            f"Supported formats: {supported}"
        )


def _read_table(path: Path) -> pd.DataFrame:
    suffix = path.suffix.lower()

    if suffix == ".csv":
        return pd.read_csv(path)

    _require_excel_support()
    return pd.read_excel(path, engine="openpyxl")


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