# DGIpy

[![image](https://img.shields.io/pypi/v/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![image](https://img.shields.io/pypi/l/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![image](https://img.shields.io/pypi/pyversions/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![Actions status](https://github.com/genomicmedlab/dgipy/workflows/CI/badge.svg)](https://github.com/genomicmedlab/dgipy/actions)

<!-- description -->
Python wrapper for accessing an instance of DGIdb v5 database
<!-- /description -->

## Installation

Install from [PyPI](https://pypi.org/project/dgipy/):

```shell
python3 -m pip install dgipy
```

## Development

Clone the repo and create a virtual environment:

```shell
git clone https://github.com/genomicmedlab/dgipy
cd dgipy
python3 -m virtualenv venv
source venv/bin/activate
```

Install development dependencies and `pre-commit`:

```shell
python3 -m pip install -e '.[dev,tests]'
pre-commit install
```

Check style with `ruff`:

```shell
python3 -m ruff format . && python3 -m ruff check --fix .
```

Run tests with `pytest`:

```shell
pytest
```
