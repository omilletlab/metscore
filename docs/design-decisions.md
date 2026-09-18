# MetSCORE Design Decisions

This document records the main architectural and implementation decisions behind the Python implementation of MetSCORE.

It is intended to explain choices that may not be obvious from the source code alone. It is a living document and should be updated when an important design decision changes.

## Project scope

MetSCORE provides a Python implementation of the MetSCORE metabolic syndrome model.

The package is designed to support:

* use as a Python library;
* prediction from pandas DataFrames;
* prediction from CSV and Excel files;
* direct prediction from paired Bruker metabolite and lipoprotein XML reports;
* additional input adapters in the future without coupling them to the mathematical implementation of the model.

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

The package separates model calculation from input and output handling.

The main architecture is:

```text
input adapters
    ↓
canonical tabular representation
    ↓
model-variable validation and ordering
    ↓
mathematical core
    ↓
prediction results
```

The mathematical core does not contain logic specific to CSV, Excel, XML, or other external formats.

This allows new input formats to be added without duplicating or modifying the model calculation.

Bruker XML support follows the same principle:

```text
Bruker XML
    ↓
generic Bruker report reader
    ↓
normalized Bruker report
    ↓
MetSCORE-specific Bruker adapter
    ↓
canonical DataFrame
    ↓
existing prediction pipeline
```

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

## Threshold and binary classification

The trained model parameters include a classification threshold inherited from the original MetSCORE implementation.

The current Python package does not use this threshold to generate a binary classification. MetSCORE is exposed as a continuous value between 0 and 1, which is considered sufficiently informative for the intended use of the package.

The original threshold corresponds approximately to a MetSCORE value of 0.5.

The threshold is retained in the packaged model parameters for completeness and reproducibility but is not currently exposed through the prediction outputs, Python API, or command-line interface.

If binary classification is added in the future, its interpretation and intended use should be defined explicitly rather than inferred from the presence of the stored threshold.

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

MetSCORE does not require a specific sample identifier column for ordinary tabular input.

Identifiers such as:

```text
sample_id
cic_id
patient
code
```

are treated like any other additional column and are preserved in tabular outputs.

The package does not impose or generate a sample identifier for tabular data because an identifier is not required for the mathematical model calculation.

Paired Bruker XML input is different because sample identity is required to establish that the metabolite and lipoprotein reports belong to the same sample.

For Bruker XML input:

* the original `SAMPLE name` value is retained in the normalized Bruker report for traceability;
* known legacy Bruker acquisition suffixes are removed when comparing sample identities;
* the normalized identifier is used as `sample_id` in the canonical tabular representation.

For example:

```text
19S20442_expno10.100000.11r
19S20442_expno10.100000.10r
```

are normalized to:

```text
19S20442
```

and are therefore treated as reports from the same sample.

Sample names that do not contain a known technical suffix are preserved unchanged.

## Bruker XML architecture

Bruker-specific functionality is intentionally divided into a generic reader and a MetSCORE-specific adapter.

The generic reader is implemented in:

```text
src/metscore/bruker.py
```

Its responsibility is to understand supported Bruker XML structures and normalize them into a common representation.

It does not know which variables are required by MetSCORE.

The MetSCORE-specific adapter is implemented in:

```text
src/metscore/bruker_input.py
```

Its responsibility is to:

* identify the metabolite and lipoprotein reports;
* verify that they belong to the same sample;
* extract the variables required by MetSCORE;
* validate their units;
* order them according to the trained model;
* create a canonical one-row DataFrame;
* pass that DataFrame through the existing prediction pipeline.

This separation is intentional. The generic Bruker reader may eventually be extracted into a separate utility package if other laboratory software needs to read the same reports.

## Bruker report types

The generic reader normalizes supported reports into two content-oriented types:

```text
metabolites
lipoproteins
```

The classification is based on report content and version metadata rather than on the filename.

Metabolite reports currently include structures associated with B.I.Quant / Quant-PS.

Lipoprotein reports currently include structures associated with B.I.LISA / PL-5009.

The XML filenames themselves are therefore not required to follow Bruker naming conventions, and paired files may be supplied in either order.

## Bruker value normalization

Different generations of Bruker metabolite reports expose quantitative values through different XML attributes.

The reader uses the following priority:

```text
rawConc
    ↓
value
    ↓
conc
```

`rawConc` is preferred when available because this reproduces the data-processing behavior used for the original MetSCORE workflow and retains the unrounded concentration provided by the report.

For example, a report may contain:

```text
conc = 0
rawConc = 0.022
```

in which case MetSCORE uses:

```text
0.022
```

rather than the rounded or censored `conc` value.

Legacy Quant-PS reports that expose concentrations through `value` remain supported.

A `conc` value is used as a fallback when neither `rawConc` nor `value` is available.

The corresponding unit is selected from the field associated with the chosen value representation.

## Bruker legacy compatibility

The XML reader is designed around observed report structures rather than hardcoded version-specific branches.

This is important because reports declaring the same nominal Quant-PS version have been observed with different XML structures.

The implementation therefore detects available fields directly instead of assuming that a particular software version always maps to a single structure.

Supported historical structures are represented by anonymized fixtures in:

```text
tests/fixtures/bruker/
```

These fixtures cover:

* metabolite reports using `rawConc`;
* metabolite reports using legacy `value`;
* metabolite reports falling back to `conc`;
* legacy lipoprotein reports;
* repeated parameter names.

Support should be understood as compatibility with the report structures represented and tested by the package, not as a claim that every historical or future Bruker XML format is automatically supported.

## Duplicate Bruker parameters

Some Bruker lipoprotein reports contain the same parameter name more than once in different report sections.

The reader accepts duplicate parameter names only when their normalized values are identical.

Identical duplicates are collapsed into one parameter.

If duplicate entries with the same parameter name contain conflicting normalized values, the reader raises an error rather than silently choosing one.

This avoids arbitrary data selection from internally inconsistent reports.

## Bruker unit validation

MetSCORE does not perform automatic unit conversion.

For direct Bruker XML prediction, the adapter validates that the variables required by the model use the expected units:

```text
metabolites     → mmol/L
lipoproteins    → mg/dL
```

A required variable with a missing or unexpected unit causes prediction to fail with an explanatory error.

This validation protects the trained model from receiving numerically valid values expressed on an incompatible scale.

## Analytical versus structural compatibility

The ability to parse an XML report and extract the required variables is separate from analytical equivalence.

MetSCORE was developed and validated using a specific Bruker IVDr analytical workflow.

The XML reader also supports report structures from other observed Bruker software or quantification versions when their structure can be normalized safely.

Successful parsing therefore means that the software understands the XML structure. It does not imply that measurements from different Bruker software versions, quantification algorithms, or analytical workflows have been demonstrated to be analytically interchangeable with those used to train MetSCORE.

## File-based predictions

File-based prediction supports:

* CSV;
* XLSX;
* paired Bruker XML reports.

CSV and XLSX input is converted to the existing tabular prediction interface.

Bruker XML input is first normalized through the Bruker reader and MetSCORE-specific adapter and then passed to the same tabular prediction interface.

No model-specific mathematics is implemented in the file-handling layer.

### Tabular default output

If no output path is provided for CSV or XLSX input, the generated file is written to the current working directory rather than to the directory containing the input file.

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

### Bruker XML default output

If no output path is provided for paired Bruker XML input, the normalized sample identifier is used:

```text
<sample_id>_metscore.csv
```

For example:

```text
AK00028V4_S1_metscore.csv
```

or, for a normalized legacy identifier:

```text
19S20442_metscore.csv
```

The default XML output is written to the current working directory.

Sample identifiers containing path separators or otherwise unsafe filename values are rejected rather than silently transformed into a filesystem path.

Existing output files are never overwritten silently.

## Excel support

Excel support is optional.

The base package supports DataFrames, CSV, and Bruker XML without requiring an Excel engine.

Excel support is installed using:

```bash
pip install "metscore[excel]"
```

This currently installs `openpyxl`.

If Excel functionality is requested without the optional dependency installed, MetSCORE raises an explanatory error containing the installation command.

## Command-line interface

The CLI intentionally has no `predict` subcommand.

Prediction is the primary operation of MetSCORE, so the interface is kept direct.

A single input represents tabular data:

```bash
metscore input.csv
```

or:

```bash
metscore input.xlsx
```

Two inputs represent paired Bruker XML reports:

```bash
metscore metabolites.xml lipoproteins.xml
```

The XML files may be supplied in either order because their roles are detected from their contents.

Explicit output paths remain supported:

```bash
metscore input.csv --output results.csv
```

```bash
metscore metabolites.xml lipoproteins.xml -o results.csv
```

The CLI interprets input count deliberately:

```text
1 input  → CSV/XLSX prediction
2 inputs → paired Bruker XML prediction
```

A single XML file is rejected with an explanatory message because Bruker prediction requires both metabolite and lipoprotein reports.

More than two inputs are also rejected.

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

## Bruker XML testing

Bruker XML support is tested independently at several layers.

The generic XML reader is tested for:

* current and legacy metabolite structures;
* `rawConc`, `value`, and `conc` selection;
* lipoprotein reports;
* identical duplicate parameters;
* conflicting duplicate parameters;
* legacy sample-name normalization.

The MetSCORE-specific Bruker adapter is tested for:

* exact agreement between XML-derived variable sets and the model variables;
* arbitrary ordering of the two reports;
* sample identity validation;
* missing required variables;
* unavailable numeric values;
* metabolite and lipoprotein unit validation;
* canonical model-variable ordering;
* end-to-end prediction from XML files.

File and CLI tests separately verify:

* default output naming;
* explicit output paths;
* refusal to overwrite existing files;
* XML input validation;
* unsafe sample identifiers;
* two-input CLI routing;
* XML input in either order;
* incorrect input counts.

Each layer is tested according to its own responsibility rather than repeatedly testing the full model pipeline in every test.

## Testing philosophy

Tests should express model or software behavior rather than accidental properties of a particular test file.

For example, file-processing tests should prefer:

```python
len(output) == len(input_data)
```

over hardcoding the current number of example rows.

Fixed values are appropriate when they are an intentional part of the model or reference fixture, such as:

* the number and identity of variables in the published model;
* the number of orthogonal components;
* the expected size of the canonical reference dataset.

When such values are used, named constants or explicit model definitions are preferred over unexplained numeric literals.

Tests should also be scoped to the layer being tested.

For example, CLI routing tests may mock the file-prediction function rather than repeatedly parsing XML and running the mathematical model, because parser and prediction behavior are already validated independently.

## Future input adapters

Additional input formats should follow the same architecture used for Bruker XML:

```text
external format
    ↓
format-specific adapter
    ↓
canonical tabular representation
    ↓
existing prediction pipeline
```

Format-specific concerns such as parsing, sample matching, naming conventions, metadata interpretation, or unit validation should remain outside the mathematical core.

The mathematical implementation of MetSCORE should remain independent of the origin and storage format of the input data.

## Potential extraction of Bruker utilities

The generic Bruker XML reader currently lives inside the MetSCORE package because direct XML input is a concrete MetSCORE requirement.

However, its design is intentionally independent of MetSCORE-specific variable selection.

If additional laboratory tools require the same Bruker XML parsing functionality, the generic reader may be extracted into a separate shared utility package.

Such an extraction should move the generic normalization behavior and its tests while leaving the MetSCORE-specific adapter inside this project.

A separate package should only be created when there is a concrete second use case rather than pre-emptively increasing project complexity.

## Guiding principle

MetSCORE should remain small and maintainable.

New development tooling, dependencies, abstractions, validation rules, and package boundaries should be introduced when they solve a concrete project need rather than solely because they are common in larger Python projects.
