from __future__ import annotations

import argparse
import shutil
from collections.abc import Sequence
from pathlib import Path

from metscore.resources import (
    EXAMPLE_DATA_CSV,
    EXAMPLE_DATA_XLSX,
    EXAMPLE_LIPOPROTEINS_XML,
    EXAMPLE_METABOLITES_XML,
)


def export_examples(destination: Path) -> Path:
    """Export the bundled MetSCORE example inputs."""
    if destination.exists():
        raise FileExistsError(f"Destination already exists: {destination}")

    bruker_dir = destination / "bruker"
    bruker_dir.mkdir(parents=True)

    shutil.copy2(
        EXAMPLE_DATA_CSV,
        destination / EXAMPLE_DATA_CSV.name,
    )
    shutil.copy2(
        EXAMPLE_DATA_XLSX,
        destination / EXAMPLE_DATA_XLSX.name,
    )
    shutil.copy2(
        EXAMPLE_METABOLITES_XML,
        bruker_dir / EXAMPLE_METABOLITES_XML.name,
    )
    shutil.copy2(
        EXAMPLE_LIPOPROTEINS_XML,
        bruker_dir / EXAMPLE_LIPOPROTEINS_XML.name,
    )

    return destination


def build_parser() -> argparse.ArgumentParser:
    """Create the example-export command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="metscore-examples",
        description="Export the bundled MetSCORE example input files.",
    )

    parser.add_argument(
        "destination",
        nargs="?",
        type=Path,
        default=Path("metscore-examples"),
        help=("Destination directory. " "Defaults to ./metscore-examples."),
    )

    return parser


def main(argv: Sequence[str] | None = None) -> int:
    """Run the MetSCORE example exporter."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        destination = export_examples(args.destination)
    except FileExistsError as exc:
        parser.exit(
            status=2,
            message=f"metscore-examples: error: {exc}\n",
        )

    print(f"Example inputs written to: {destination.resolve()}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
