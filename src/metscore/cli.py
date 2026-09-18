from __future__ import annotations

import argparse
from collections.abc import Sequence
from pathlib import Path

from metscore.files import predict_bruker_file_pair, predict_file


def build_parser() -> argparse.ArgumentParser:
    """Create the MetSCORE command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="metscore",
        description="Calculate MetSCORE from serum NMR data.",
    )

    parser.add_argument(
        "inputs",
        nargs="+",
        type=Path,
        help=(
            "One CSV/XLSX file, or two Bruker XML reports "
            "(metabolites and lipoproteins, in any order)."
        ),
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
        if len(args.inputs) == 1:
            input_file = args.inputs[0]

            if input_file.suffix.lower() == ".xml":
                raise ValueError(
                    "Bruker XML prediction requires two XML input files: "
                    "one metabolite report and one lipoprotein report."
                )

            output = predict_file(
                input_file,
                output_path=args.output,
            )

        elif len(args.inputs) == 2:
            output = predict_bruker_file_pair(
                args.inputs[0],
                args.inputs[1],
                output_path=args.output,
            )

        else:
            raise ValueError(
                "Expected one CSV/XLSX input file or two Bruker XML input files."
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