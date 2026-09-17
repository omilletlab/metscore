from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from metscore.files import predict_file


def build_parser() -> argparse.ArgumentParser:
    """Create the MetSCORE command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="metscore",
        description="Calculate MetSCORE from serum NMR data.",
    )

    parser.add_argument(
        "input",
        type=Path,
        help="Input CSV or XLSX file.",
    )

    parser.add_argument(
        "-o",
        "--output",
        type=Path,
        help=(
            "Output CSV or XLSX file. "
            "By default, the result is written to the current directory."
        ),
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MetSCORE command-line interface."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        output = predict_file(
            args.input,
            output_path=args.output,
        )
    except (
        FileNotFoundError,
        FileExistsError,
        ImportError,
        ValueError,
    ) as exc:
        parser.exit(
            status=2,
            message=f"metscore: error: {exc}\n",
        )

    print(output)
    return 0