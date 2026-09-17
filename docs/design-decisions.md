# MetSCORE Design Decisions

This document records the main architectural and implementation decisions behind the Python implementation of MetSCORE.

It is intended to explain choices that may not be obvious from the source code alone. It is a living document and should be updated when an important design decision changes.

## Project scope

MetSCORE provides a Python implementation of the MetSCORE metabolic syndrome model.

The package is designed to support:

* use as a Python library;
* prediction from tabular data;
* prediction from files through a command-line interface;
* additional input adapters in the future, without coupling them to the mathematical implementation of the model.

The Python implementation does not require R or serialized R objects at runtime.

## Python and project management

MetSCORE requires Python 3.11 or newer.

Development currently uses Python 3.12.

The project uses:

* `pyproject.toml` for project metadata and dependency declaration;
* `uv` for development environment and dependency management;
* Hatchling as the build backend;
* a `src/` package layout.

`uv` is a development tool and is not required by users installing MetSCORE through standard Python package installers.

## Separation of responsibilities

The package separates model calculation from input/output handling.

The main layers are:

```text
input adapters
    ↓
tabular representation
    ↓
model-variable validation and ordering
    ↓
mathematical core
    ↓
prediction results
```

The mathematical core should not contain logic specific to CSV, Excel, XML, or other external formats.

This allows new input formats to be added without duplicating or modifying the model calculation.

## Model parameters

The trained model parameters are distributed as package data in:

```text
src/metscore/data/metscore_params.json
```

They include:

* ordered model variables;
* autoscaling means and standard deviations;
* orthogonal weights and loadings;
* predictive weights;
* logistic regression parameters;
* the model threshold.

The parameter loader validates dimensions, numeric values, uniqueness of variable names, and other internal consistency requirements before the model is used.

Parameter arrays are exposed internally as read-only NumPy arrays to reduce the risk of accidental modification.

## Parameter precision

Full numerical precision must be preserved when exporting trained model parameters.

The original parameters were exported using `jsonlite`. The default JSON precision was found to be insufficient for exact reproduction of the original model predictions.

Parameters must therefore be exported using full precision, for example:

```r
write_json(
  metscore_params,
  "MetSCORE.params.json",
  pretty = TRUE,
  auto_unbox = TRUE,
  digits = NA
)
```

Reducing parameter precision can produce small but systematic differences in MetSCORE predictions.

## Mathematical core

The core implementation operates on numeric arrays whose columns already follow the order defined in the model parameters.

The calculation reproduces:

```text
raw input
→ log10(x + 1)
→ autoscaling
→ orthogonal deflation
→ predictive score
→ logistic transformation
→ MetSCORE
```

The core returns:

* `MetSCORE`;
* `t_pred`;
* all orthogonal component scores (`t_orth`).

Although the current model contains one orthogonal component, the implementation is designed to support an arbitrary number of orthogonal components.

The array-level API is intentionally strict because NumPy arrays do not contain variable names.

## Tabular API

For pandas DataFrames, one row represents one sample.

Required model variables are identified by column name rather than by their original position in the DataFrame.

The package therefore:

1. verifies that all required variables are present;
2. reorders them internally according to the model definition;
3. performs the prediction;
4. returns a copy of the original DataFrame with prediction columns appended.

Additional user columns are preserved.

The original DataFrame is not modified in place.

Prediction columns are appended as:

```text
MetSCORE
t_pred
t_orth_1
t_orth_2
...
```

depending on the number of orthogonal components in the model.

## Sample identifiers

MetSCORE does not require a specific sample identifier column.

Identifiers such as:

```text
sample_id
cic_id
patient
code
```

are treated like any other additional column and are preserved in tabular outputs.

The package does not impose or generate a sample identifier for tabular data because an identifier is not required for the model calculation.

Input adapters that genuinely require sample identity, such as future paired-XML processing, may implement their own identifier validation.

## File-based predictions

File-based prediction currently supports:

* CSV;
* XLSX.

File handling is a layer above the tabular prediction API and does not contain model-specific mathematics.

If no output path is provided, the generated file is written to the current working directory rather than to the directory containing the input file.

For example:

```text
input:
/data/shared/samples.csv

working directory:
/home/user/analysis

default output:
/home/user/analysis/samples_metscore.csv
```

This avoids assuming that the input directory is writable and avoids modifying directories containing original datasets.

Existing output files are not overwritten silently.

## Excel support

Excel support is optional.

The base package supports DataFrames and CSV without requiring an Excel engine.

Excel support is installed using:

```bash
pip install "metscore[excel]"
```

This currently installs `openpyxl`.

If Excel functionality is requested without the optional dependency installed, MetSCORE raises an explanatory error containing the installation command.

## Command-line interface

The CLI intentionally has no `predict` subcommand.

Prediction is the primary operation of MetSCORE, so the interface is kept direct:

```bash
metscore input.csv
```

or:

```bash
metscore input.csv --output results.csv
```

The short form is also supported:

```bash
metscore input.csv -o results.csv
```

The CLI is implemented using Python's standard `argparse` module rather than an additional CLI framework.

The CLI is a thin layer over the same file and prediction functions used by the Python API.

No model calculation is duplicated in the CLI.

## Reference validation

The Python implementation is validated against predictions generated by the original model implementation.

The repository contains:

```text
examples/example_data.csv
```

with 100 example samples and anonymized identifiers, and:

```text
tests/fixtures/original_model_predictions.csv
```

with the corresponding reference values for:

* `MetSCORE`;
* `t_pred`;
* `t_orth_1`.

The same example input is used for documentation/examples and model-reference testing rather than maintaining duplicate input datasets.

Numerical equivalence is tested using strict floating-point tolerances.

## Testing philosophy

Tests should express model or software behavior rather than accidental properties of a particular test file.

For example, file-processing tests should prefer:

```python
len(output) == len(input_data)
```

over hardcoding the current number of example rows.

Fixed values are appropriate when they are an intentional part of the model or reference fixture, such as:

* the number of variables in the published model;
* the number of orthogonal components;
* the expected size of the canonical reference dataset.

When such values are used, named constants are preferred over unexplained numeric literals.

## Future input adapters

Future support is planned for direct prediction from paired quantification XML files.

The intended architecture is:

```text
quantification XML 1
        +
quantification XML 2
        ↓
XML-specific adapter
        ↓
canonical sample representation
        ↓
existing prediction pipeline
```

The XML parser will be responsible for extracting and combining the required variables and for any sample-identity checks required to establish that the two files belong to the same sample.

The mathematical core should remain independent of XML structure.

## Guiding principle

MetSCORE should remain small and maintainable.

New development tooling, dependencies, abstractions, and validation rules should be introduced when they solve a concrete project need rather than solely because they are common in larger Python projects.
