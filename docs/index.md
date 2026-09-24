# MetSCORE

MetSCORE is a Python implementation of the serum NMR metabolomics-based metric for metabolic syndrome.

The software can be used through:

* the **Python API** for integration into analysis workflows;
* the **command-line interface** for file-based predictions;
* the **web application** for interactive use without requiring a local Python installation.

MetSCORE supports tabular CSV and Excel data as well as paired Bruker metabolite and lipoprotein XML reports.

This documentation covers the public Python API, supported input formats, web application, and implementation design decisions.

## Documentation

* [Web application](web-app.md) — interactive calculation from tabular data or Bruker XML reports.
* [API reference](api.md) — public Python interface.
* [Design decisions](design-decisions.md) — architectural and implementation decisions.
