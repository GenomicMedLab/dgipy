# DGIpy

[![image](https://img.shields.io/pypi/v/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![image](https://img.shields.io/pypi/l/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![image](https://img.shields.io/pypi/pyversions/dgipy.svg)](https://pypi.python.org/pypi/dgipy)
[![Actions status](https://github.com/genomicmedlab/dgipy/actions/workflows/checks.yaml/badge.svg)](https://github.com/genomicmedlab/dgipy/actions)

<!-- description -->
Python wrapper for accessing an instance of DGIdb v5 database. Currently supported searches will return individual interaction data for drugs or genes, category annotations for genes, or information for drugs.
<!-- /description -->

## Installation

Install from [PyPI](https://pypi.org/project/dgipy/):

```shell
python3 -m pip install dgipy
```

## Usage

DGIpy is built around query methods that wrap a GraphQL client and fetch data from the public DGIdb API endpoint. By default, data returned in a columnar format (i.e., as a dictionary where keys are column names and values are lists representing column data).

```pycon
>>> from dgipy import get_gene
>>> results = get_gene(["BRAF"])
>>> results["gene_name"][0], results["gene_concept_id"][0], results["gene_aliases"][0][:5]
('BRAF', 'hgnc:1097', ['B-RAF PROTO-ONCOGENE, SERINE/THREONINE KINASE', 'BRAF1', 'BRAF-1', 'UCSC:UC003VWC.5', 'VEGA:OTTHUMG00000157457'])
```

This orientation enables easy use within the dataframe library of your choosing:

```pycon
>>> import pandas as pd
>>> pd.DataFrame(results)
   name concept_id                                            aliases                                         attributes
0  BRAF  hgnc:1097  [B-RAF PROTO-ONCOGENE, SERINE/THREONINE KINASE...  {'BRAF MUT': ['Reported Genome Event Targeted'...
>>>
>>> import polars as pl  # not included in DGIpy dependencies
>>> pl.DataFrame(results)
shape: (1, 4)
┌──────┬────────────┬─────────────────────────────────┬─────────────────────────────────┐
│ name ┆ concept_id ┆ aliases                         ┆ attributes                      │
│ ---  ┆ ---        ┆ ---                             ┆ ---                             │
│ str  ┆ str        ┆ list[str]                       ┆ struct[14]                      │
╞══════╪════════════╪═════════════════════════════════╪═════════════════════════════════╡
│ BRAF ┆ hgnc:1097  ┆ ["B-RAF PROTO-ONCOGENE, SERINE… ┆ {["0"],["Swiss-Prot"],["Report… │
└──────┴────────────┴─────────────────────────────────┴─────────────────────────────────┘
```

## Graph App

### Setup

dgipy must be imported from dgidb first:

    import dgipy

To generate and run the app, run the following command:

    app = dgipy.generate_app()
    if __name__ == '__main__':
        app.run_server()

Once the server is running, The dash app can be viewed at its default URL 'http://127.0.0.1:8050/'

### Utilization

This app displays a visual network of drug-gene interactions (queried using dgidb.py), with selectable nodes and edges for user interactivity. Users can query genes, which will allow the network to show all drugs connected to the said genes. Additionally, the network will reveal drugs that two genes share. Drugs that are only connected to one gene are considered "single-degree drugs", while drugs that are connected to two genes are considered "multi-degree drugs". The unique colorations for single-degree drugs, multi-degree drugs, and genes can be viewed in the graph legend on the right side.

The main network graph on the left provides many options to view and interact with the graph: Zooming in/out of the graph, panning the graph, reseting the graph perspective, etc. Alongside these options, the user can hover over nodes to reveal their name, and select them by clicking on the node. Users can also select edges (lines between nodes), by hovering on the center of an edge and clicking (just like nodes). Selected Nodes/Edges will appear on the right-side info box under "Selected Node/Edge:".

The "Genes Dropdown Display" provides a dropdown menu listing every available queryable gene. Multiple genes can be selected to create larger networks. Specific Genes can also be typed to narrow down search results in the dropdown menu list.

The "Neighbors Dropdown Display" provides a dropdown menu listing every neighbor for a selected node. This also allows users to select edges between two nodes without utilizing the graph. Only when selecting a node (drug/gene) will a dropdown display neigbors. An edge has no neighbors, and therefore will not display anything.

As previously mentioned, "Selected Node/Edge" will update when a node or edge is selected on the graph by the user. "Selected Edge Info" will update when either 1) the user selects an edge directly from the graph, or 2) the user selects a node (drug/gene) and uses the "Neighbors Dropdown Display" to select an neighbor to view an edge.

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
