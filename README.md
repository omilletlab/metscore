# MetSCORE

Python implementation of **MetSCORE**, a quantitative metric based on serum NMR metabolomics for evaluating metabolic syndrome risk.

## About MetSCORE

MetSCORE is a metabolic model that integrates quantitative serum metabolite and lipoprotein measurements obtained by NMR spectroscopy into a continuous score ranging from 0 to 1.

The model was developed to provide a quantitative molecular representation of metabolic syndrome and was originally described in:

> Gil-Redondo R, Conde R, Bruzzone C, et al. **MetSCORE: a molecular metric to evaluate the risk of metabolic syndrome based on serum NMR metabolomics.** *Cardiovascular Diabetology*. 2024;23:272. [doi:10.1186/s12933-024-02363-3](https://doi.org/10.1186/s12933-024-02363-3)

This package provides an independent Python implementation of the trained MetSCORE model. Model parameters are distributed with the package, so prediction does **not require R, R packages, or serialized R model objects**.

The implementation supports prediction from individual or multiple samples and exposes the MetSCORE value together with the underlying predictive (`t_pred`) and orthogonal (`t_orth`) model scores.

**Documentation:** https://omilletlab.github.io/metscore/

## Contents

- [About MetSCORE](#about-metscore)
- [Web interface](#web-interface)
- [Installation](#installation)
- [Input data](#input-data)
- [Python usage](#python-usage)
- [Command-line usage](#command-line-usage)
- [Bruker XML input](#bruker-xml-input)
- [Output](#output)
- [Example data](#example-data)
- [Model validation](#model-validation)
- [Citation](#citation)
- [Development](#development)
- [License](#license)

## Web interface

MetSCORE includes a Streamlit web interface that provides a graphical front end to the same prediction workflows exposed through the Python API and command-line interface.

The interface supports:

* CSV and Excel files containing one or multiple samples;
* paired Bruker metabolite and lipoprotein XML reports.

The application uses the same validated Python implementation and prediction pipeline as the package.

Bundled example inputs can be run or downloaded directly from the web interface for both tabular and Bruker XML workflows.

See the [web interface documentation](docs/web-app.md) for details.

## Installation

MetSCORE requires **Python 3.11 or newer**.

### Install from source

Clone the repository and install the package with `pip`:

```bash
git clone https://github.com/omilletlab/metscore.git
cd metscore
python -m pip install .
```

For optional Excel (`.xlsx`) support, install the `excel` extra:

```bash
python -m pip install ".[excel]"
```

The base installation supports the Python API, CSV input, and Bruker XML input. Excel support is kept optional to avoid installing additional dependencies when it is not needed.

## Input data

MetSCORE expects tabular quantitative serum NMR data in which **each row represents one sample**.

### Analytical origin and units

The original MetSCORE model was developed and validated using serum ^1H-NMR data acquired on **Bruker Avance IVDr 600 MHz spectrometers**. Serum metabolites were quantified using **B.I.Quant-PS 2.0.0**, whereas lipoprotein classes and subclasses were quantified using **B.I.LISA (Lipoprotein Subclass Analysis) PL-5009-01/001**.

The MetSCORE input variables therefore follow the definitions and units of this Bruker IVDr workflow:

| Variable                 | Type        | Expected unit |
| ------------------------ | ----------- | ------------- |
| `L5TG`                   | Lipoprotein | mg/dL         |
| `HDFC`                   | Lipoprotein | mg/dL         |
| `H3TG`                   | Lipoprotein | mg/dL         |
| `H4FC`                   | Lipoprotein | mg/dL         |
| `V1PL`                   | Lipoprotein | mg/dL         |
| `L2FC`                   | Lipoprotein | mg/dL         |
| `L6TG`                   | Lipoprotein | mg/dL         |
| `Alanine`                | Metabolite  | mmol/L        |
| `Citric acid`            | Metabolite  | mmol/L        |
| `Creatine`               | Metabolite  | mmol/L        |
| `Creatinine`             | Metabolite  | mmol/L        |
| `Formic acid`            | Metabolite  | mmol/L        |
| `Glucose`                | Metabolite  | mmol/L        |
| `Glutamic acid`          | Metabolite  | mmol/L        |
| `Glycine`                | Metabolite  | mmol/L        |
| `Isoleucine`             | Metabolite  | mmol/L        |
| `Lactic acid`            | Metabolite  | mmol/L        |
| `Methionine`             | Metabolite  | mmol/L        |
| `Phenylalanine`          | Metabolite  | mmol/L        |
| `Proline`                | Metabolite  | mmol/L        |
| `Sarcosine`              | Metabolite  | mmol/L        |
| `Trimethylamine-N-oxide` | Metabolite  | mmol/L        |

Input values must use the same variable definitions and units as those used during model development. **MetSCORE does not perform automatic unit conversion.**

The model was developed and validated using the Bruker IVDr analytical workflow described above. Measurements obtained using other NMR platforms or quantification algorithms should not be assumed to be interchangeable solely because they have similar variable names or units.

### Tabular structure

Column names must match the model variable names exactly.

The order of the columns does **not** matter when using the pandas DataFrame or file-based interfaces. MetSCORE identifies the required variables by name and automatically reorders them internally according to the trained model.

Additional columns are allowed and are preserved in the output. These may contain, for example, sample identifiers, cohort information, batch information, or other metadata.

A specific sample identifier column is **not required**.

For example, both of the following are valid inputs:

```text id="etyk46"
sample_id    L5TG    HDFC    ...    Trimethylamine-N-oxide
sample_001   1.72    15.50   ...    0.017
sample_002   1.42     4.95   ...    0.012
```

and:

```text id="8t2yo7"
L5TG    HDFC    ...    Trimethylamine-N-oxide
1.72    15.50   ...    0.017
1.42     4.95   ...    0.012
```

All model variables must contain numeric, finite values. Missing or non-numeric values in required model variables are not accepted.

Internally, MetSCORE applies the same preprocessing used during model development, including the `log10(x + 1)` transformation and autoscaling with the stored model parameters.

## Python usage

### pandas DataFrame

For most Python workflows, the recommended interface is `metscore.predict()`.

```python
import pandas as pd

import metscore

data = pd.read_csv("samples.csv")

result = metscore.predict(data)
```

Each row is treated as one sample. Required model variables are identified by column name and automatically reordered internally, so the original column order does not matter.

`predict()` returns a **new DataFrame** and does not modify the input object in place.

The original columns are preserved and the following prediction columns are appended:

* `MetSCORE`
* `t_pred`
* `t_orth_1`

For example:

```python
print(
    result[
        [
            "sample_id",
            "MetSCORE",
            "t_pred",
            "t_orth_1",
        ]
    ].head()
)
```

A `sample_id` column is not required; it is shown here only as an example of user-provided metadata.

The prediction columns can also be accessed directly:

```python
scores = result["MetSCORE"]
predictive_scores = result["t_pred"]
orthogonal_scores = result["t_orth_1"]
```

Additional columns present in the input DataFrame are retained unchanged in the returned DataFrame.

### NumPy array

For lower-level workflows, MetSCORE also provides `predict_array()`.

```python
import metscore

result = metscore.predict_array(x)
```

`x` may contain one sample or multiple samples:

```text
single sample:    (n_variables,)
multiple samples: (n_samples, n_variables)
```

Unlike the DataFrame interface, NumPy arrays do not contain variable names. Therefore, columns **must follow the exact model-variable order shown in the input-variable table above**.

For most users working with named tabular data, `metscore.predict()` is preferred because it validates and reorders model variables automatically.

`predict_array()` returns a `PredictionResult` object containing:

```python
result.metscore
result.t_pred
result.t_orth
```

For `n` samples and the current MetSCORE model:

```text
result.metscore.shape  -> (n,)
result.t_pred.shape    -> (n,)
result.t_orth.shape    -> (n, 1)
```

The `t_orth` output is always two-dimensional so that the interface remains compatible with models containing more than one orthogonal component.


## Command-line usage

MetSCORE can be used directly from the terminal with either tabular input or paired Bruker XML reports.

For a CSV file:

```bash
metscore samples.csv
```

For an Excel file:

```bash
metscore samples.xlsx
```

For paired Bruker metabolite and lipoprotein XML reports:

```bash
metscore metabolites.xml lipoproteins.xml
```

The two XML files may be provided in either order. See the [Bruker XML input](#bruker-xml-input) section for details about supported report structures and validation.

If no output path is provided for CSV or XLSX input, MetSCORE writes the result to the **current working directory** using the input filename with `_metscore` appended.

For example:

```text
input:
/data/shared/samples.csv

current working directory:
/home/user/analysis

output:
/home/user/analysis/samples_metscore.csv
```

For paired Bruker XML input, the default filename is based on the normalized sample identifier:

```text
<sample_id>_metscore.csv
```

An explicit output path can be provided with `-o` or `--output`:

```bash
metscore samples.csv --output results.csv
```

or:

```bash
metscore metabolites.xml lipoproteins.xml -o results.csv
```

The output format is determined by the output file extension. CSV and XLSX are currently supported.

Existing output files are not overwritten automatically. If the requested output path already exists, MetSCORE exits with an error instead of replacing the file.

Excel input or output requires the optional dependency:

```bash
pip install "metscore[excel]"
```

The CLI uses the same prediction pipeline as the Python API; no separate model implementation is used for terminal predictions.

## Bruker XML input

MetSCORE can calculate predictions directly from paired Bruker metabolite and lipoprotein quantification reports.

From Python, paired Bruker XML reports can be processed directly through the public API:

```python
import metscore

result = metscore.predict_bruker_files(
    "metabolites.xml",
    "lipoproteins.xml",
)
```

The two XML files may be provided in either order. The returned DataFrame contains the normalized sample identifier, the 22 MetSCORE input variables, and the model outputs.

Two XML files are required for each sample:

* a metabolite report generated by **B.I.Quant / Quant-PS**
* a lipoprotein report generated by **B.I.LISA / PL-5009**

The files may be provided in either order:

```bash
metscore metabolites.xml lipoproteins.xml
```

or:

```bash
metscore lipoproteins.xml metabolites.xml
```

MetSCORE identifies the report type from the XML content, so the filenames themselves do not need to follow a particular naming convention.

The two reports are checked to ensure that they correspond to the same sample. Known technical suffixes present in legacy Bruker sample identifiers are normalized automatically when comparing reports.

For metabolite reports, MetSCORE uses the unrounded `rawConc` value when it is available. Older report structures that provide values through `value` or `conc` fields are also supported.

Only the variables required by the MetSCORE model are extracted from the reports. Their units are validated before prediction:

* metabolites must be reported in `mmol/L`
* lipoprotein variables must be reported in `mg/dL`

If no output path is specified, the prediction is written to the current working directory using the normalized sample identifier:

```text
<sample_id>_metscore.csv
```

For example:

```text
SAMPLE001_metscore.csv
```

An explicit output path can be provided with `-o` or `--output`:

```bash
metscore metabolites.xml lipoproteins.xml -o predictions.csv
```

CSV and XLSX output are supported. Excel output requires the optional `excel` dependency.

The XML reader supports both current and legacy Bruker report structures represented in the package test suite. Reading a report successfully indicates that its structure is supported by the software; it does not imply analytical equivalence between different Bruker software or quantification versions.


## Output

For tabular and file-based predictions, MetSCORE preserves the original input columns and appends the model outputs at the end.

The current model adds:

* `MetSCORE`
* `t_pred`
* `t_orth_1`

### `MetSCORE`

`MetSCORE` is the final continuous model output, obtained by applying the logistic transformation to the predictive OPLS score.

Values range from 0 to 1.

Higher values indicate a metabolic profile more strongly associated with the metabolic syndrome phenotype represented by the original model.

MetSCORE should be interpreted as a continuous molecular score rather than as a standalone clinical diagnosis.

### `t_pred`

`t_pred` is the predictive OPLS score used by the logistic model to calculate MetSCORE.

It represents the position of each sample along the predictive component of the trained model.

### `t_orth_1`

`t_orth_1` is the score of the first orthogonal OPLS component.

Orthogonal components capture structured variation in the input data that is separated from the predictive component.

The current MetSCORE model contains one orthogonal component. The Python implementation is designed to support additional orthogonal components if required by future model versions.

### Example output

A file containing:

```text
sample_id    L5TG    HDFC    ...    Trimethylamine-N-oxide
sample_001   1.72    15.50   ...    0.017
sample_002   1.42     4.95   ...    0.012
```

will produce an output with the original columns preserved and prediction columns appended:

```text
sample_id    L5TG    HDFC    ...    MetSCORE    t_pred    t_orth_1
sample_001   1.72    15.50   ...    0.2273      0.4636    -0.8164
sample_002   1.42     4.95   ...    0.6459      1.9530    -0.0989
```

The order of samples is preserved.

## Example data

The repository includes example inputs for all currently supported input formats:

```text
examples/
├── example_data.csv
├── example_data.xlsx
└── bruker/
    ├── sample_001_metabolites.xml
    └── sample_001_lipoproteins.xml
```

The CSV and Excel files contain the same 100 example samples with anonymized identifiers (`sample_001`, `sample_002`, ...).

The paired Bruker XML files represent `sample_001` from the tabular example dataset using the supported metabolite and lipoprotein report structures. The quantitative values in the XML files correspond to the same 22 MetSCORE input variables as `sample_001` in the CSV and Excel files.

These examples can be used to test the Python API, command-line interface, and web interface.

### Tabular example

From the command line:

```bash
metscore examples/example_data.csv
```

or:

```bash
metscore examples/example_data.xlsx
```

From Python:

```python
import pandas as pd

import metscore

data = pd.read_csv("examples/example_data.csv")
result = metscore.predict(data)
```

The same CSV or Excel file can also be uploaded directly through the tabular workflow of the web interface.

### Bruker XML example

From the command line:

```bash
metscore \
  examples/bruker/sample_001_metabolites.xml \
  examples/bruker/sample_001_lipoproteins.xml
```

From Python:

```python
import metscore

result = metscore.predict_bruker_files(
    "examples/bruker/sample_001_metabolites.xml",
    "examples/bruker/sample_001_lipoproteins.xml",
)
```

The same two XML files can also be uploaded through the Bruker XML workflow of the web interface.

Automated tests verify that the CSV and Excel example datasets are equivalent and that the Bruker XML example produces the same MetSCORE prediction as `sample_001` in the tabular example data.

## Model validation

The Python implementation is validated against predictions generated using the original MetSCORE model implementation.

Reference predictions for the 100 example samples are stored in:

```text id="wew0oc"
tests/fixtures/original_model_predictions.csv
```

The reference dataset contains the expected values for:

* `MetSCORE`
* `t_pred`
* `t_orth_1`

Automated tests compare the Python implementation against these reference predictions using strict floating-point tolerances.

This validation verifies that the Python implementation reproduces the numerical behavior of the original trained model while remaining independent of R at runtime.

## Citation

If you use MetSCORE in your research, please cite the original publication describing the model:

> Gil-Redondo R, Conde R, Bruzzone C, Seco ML, Bizkarguenaga M, González-Valle B, de Diego A, Laín A, Habisch H, Haudum C, Verheyen N, Obermayer-Pietsch B, Margarita S, Pelusi S, Verde I, Oliveira N, Sousa A, Zabala-Letona A, Santos-Martin A, Loizaga-Iriarte A, Unda-Urzaiz M, Kazenwadel J, Berezhnoy G, Geisler T, Gawaz M, Cannet C, Schäfer H, Diercks T, Trautwein C, Carracedo A, Madl T, Valenti L, Spraul M, Lu SC, Embade N, Mato JM, Millet O. **MetSCORE: a molecular metric to evaluate the risk of metabolic syndrome based on serum NMR metabolomics.** *Cardiovasc Diabetol.* 2024 Jul 24;23(1):272. [doi:10.1186/s12933-024-02363-3](https://doi.org/10.1186/s12933-024-02363-3)

## Development

Development uses `uv` for environment and dependency management.

Clone the repository:

```bash
git clone https://github.com/omilletlab/metscore.git
cd metscore
```

Create the development environment, including optional Excel support:

```bash
uv sync --extra excel
```

Run the full test suite with:

```bash
uv run pytest
```

### Run the web interface locally

The Streamlit web interface is maintained as a separate development dependency group.

Run it locally with:

```bash
uv run --group app streamlit run app/streamlit_app.py
```

The application will be available through the local Streamlit server, typically at:

```text
http://localhost:8501
```

## License

This software is available for academic and non-commercial research use.
Commercial use requires prior written authorization from CIC bioGUNE.

See the [LICENSE](LICENSE) file for details.
