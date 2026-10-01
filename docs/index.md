# MetSCORE

MetSCORE is a Python implementation of the serum NMR metabolomics-based metric for metabolic syndrome.

The software can be used through:

* the **Python API** for integration into analysis workflows;
* the **command-line interface** for file-based predictions;
* the **web interface** for interactive use through a graphical front end.

MetSCORE supports tabular CSV and Excel data as well as paired Bruker metabolite and lipoprotein XML reports.

This documentation covers the public Python API, supported input formats, and web interface.

## Installation and commands

Install MetSCORE from the repository with:

```bash
python -m pip install .
```

For Excel support:

```bash
python -m pip install ".[excel]"
```

To include the Streamlit web interface:

```bash
python -m pip install ".[app]"
```

The `app` extra also includes Excel support.

MetSCORE provides the following command-line entry points:

```text
metscore
metscore-examples
metscore-gui
```

`metscore` runs file-based prediction workflows.

`metscore-examples` exports the packaged example datasets to a user-accessible directory.

`metscore-gui` launches the local web interface and requires the `app` extra.

## Documentation

* [Web interface](web-app.md) — graphical calculation from tabular data or Bruker XML reports.
* [API reference](api.md) — public Python interface.
