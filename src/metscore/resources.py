from pathlib import Path

PACKAGE_DIR = Path(__file__).resolve().parent

EXAMPLES_DIR = PACKAGE_DIR / "data" / "examples"

EXAMPLE_DATA_CSV = EXAMPLES_DIR / "example_data.csv"
EXAMPLE_DATA_XLSX = EXAMPLES_DIR / "example_data.xlsx"

EXAMPLE_BRUKER_DIR = EXAMPLES_DIR / "bruker"
EXAMPLE_METABOLITES_XML = EXAMPLE_BRUKER_DIR / "sample_001_metabolites.xml"
EXAMPLE_LIPOPROTEINS_XML = EXAMPLE_BRUKER_DIR / "sample_001_lipoproteins.xml"
