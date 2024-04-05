import pandas as pd
from pathlib import Path
import pytest
import requests_mock

from dgipy.dgidb import get_interactions,get_categories,get_drug, get_gene


def test_get_drugs(fixtures_dir: Path):
    terms = ["imatinib"]
    with requests_mock.Mocker() as m, (fixtures_dir / "get_drug_api_response.json").open() as json_response, (fixtures_dir / "get_drug_filtered_api_response.json").open() as filtered_json_response:
        m.post("https://dgidb.org/api/graphql", text=json_response.read())

        results = get_drug(terms)
        assert isinstance(results, pd.DataFrame), "Results object is a DataFrame"
        assert len(results), "DataFrame is non-empty"

        results_with_added_fake = get_drug(terms + ["not-real"])
        assert len(results_with_added_fake) == len(results), "Gracefully ignore non-existent search terms"

        m.post("https://dgidb.org/api/graphql", text="{\"data\": {\"drugs\": {\"nodes\": []}}}")
        empty_results = get_drug("not-real")
        assert len(empty_results) == 0, "Handles empty response"

        filtered_results = get_drug(terms + ["metronidazole"], antineoplastic=True)
        assert len(filtered_results), "DataFrame is non-empty"
        assert filtered_results["drug"][0] == "IMATINIB"
        assert results["antineoplastic"].all(), "All results are antineoplastics"

        m.post("https://dgidb.org/api/graphql", text=filtered_json_response)
        filtered_results = get_drug(terms + ["metronidazole"], antineoplastic=False)
        assert len(filtered_results), "DataFrame is non-empty"
        assert filtered_results["drug"][0] == "METRONIDAZOLE"


def test_get_genes(fixtures_dir: Path):
    terms = ["BRAF"]
    with requests_mock.Mocker() as m, (fixtures_dir / "get_gene_api_response.json").open() as json_response:
        m.post("https://dgidb.org/api/graphql", text=json_response.read())

        results = get_gene(terms)
        assert isinstance(results, pd.DataFrame), "Results object is a DataFrame"
        assert len(results), "DataFrame is non-empty"

        results_with_added_fake = get_gene(terms + ["not-real"])
        assert len(results_with_added_fake) == len(results), "Gracefully ignore non-existent search terms"

        m.post("https://dgidb.org/api/graphql", text="{\"data\": {\"genes\": {\"nodes\": []}}}")
        empty_results = get_gene("not-real")
        assert len(empty_results) == 0, "Handles empty response"


def test_get_interactions():
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


def test_get_interactions_benchmark(benchmark):
    query = "braf"
    results = benchmark.pedantic(get_interactions, args=(query,), kwargs={"search": "genes"},rounds=10,warmup_rounds=0,iterations=1)
    assert results.columns[0] == "gene"
