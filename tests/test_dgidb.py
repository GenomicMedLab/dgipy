import pandas as pd
import pytest

from dgipy.dgidb import get_interactions,get_categories,get_drug


def test_get_interactions():
    """Test that interactions works correctly"""
    # Search types work correctly
    query = "braf"
    with pytest.raises(Exception) as excinfo:
        results = get_interactions(query, search="fake")
    assert "Search type must be specified" in str(excinfo.value)

    # Default search type functions correct as 'gene' and not 'drug'
    query = "imatinib"
    results = get_interactions(query)
    assert len(results) == 0

    # Use pandas default is correctly set to 'true'
    query = "braf"
    results = get_interactions(query)
    assert type(results) == type(pd.DataFrame())

    # Use pandas can be toggled to 'false' and returns a dictionary response object
    query = "braf"
    results = get_interactions(query, use_pandas=False)
    assert type(results) != type(pd.DataFrame())
    assert type(results) == type(dict())

    # Gene search types work correctly
    query = "braf"
    results = get_interactions(query, search="genes")
    assert results.columns[0] == "gene"

    # Gene search is not grabbing drugs
    query = "imatinib"
    results = get_interactions(query, search="genes")
    assert len(results) == 0

    # Drug search types work correctly
    query = "imatinib"
    results = get_interactions(query, search="drugs")
    assert type(results) == type(pd.DataFrame())
    assert results.columns[0] == "drug"

    # Drug search is not grabbing genes
    query = "XPO1"
    results = get_interactions(query, search="drugs")
    assert len(results) == 0


def test_get_categories():
    """Test that categories works correctly"""
    # Categories search builds a dataframe (with use_pandas default set to 'true')
    query = "braf"
    results = get_categories(query)
    assert type(results) == type(pd.DataFrame())

    # Categories does not return drugs data
    query = "imatinib"
    results = get_categories(query)
    assert len(results) == 0

    # Use pandas can be toggled to 'false' and returns a dictionary response object
    query = "imatinib"
    results = get_categories(query, use_pandas=False)
    assert type(results) != type(pd.DataFrame())
    assert type(results) == type(dict())


def test_get_drugs():
    """Test that drug profile works correctly"""
    # Drug search builds a dataframe (with use_pandas default set to 'true')
    query = "imatinib"
    results = get_drug(query)
    assert type(results) == type(pd.DataFrame())

    # Drug search does not return gene data
    query = "XPO1"
    results = get_drug(query)
    assert (len(results)) == 0

    # Use pandas can be toggled to 'false' and returns dictionary response object
    query = "imatinib"
    results = get_drug(query, use_pandas=False)
    assert type(results) != type(pd.DataFrame())
    assert type(results) == type(dict())


def test_get_interactions_benchmark(benchmark):
    query = "braf"
    results = benchmark.pedantic(get_interactions, args=(query,), kwargs={"search": "genes"},rounds=10,warmup_rounds=0,iterations=1)
    assert results.columns[0] == "gene"
