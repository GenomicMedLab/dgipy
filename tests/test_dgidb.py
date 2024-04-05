from io import StringIO
from pathlib import Path
from typing import Callable

import pandas as pd
import pytest
import requests_mock

from dgipy.dgidb import get_categories, get_drug, get_drug_applications, get_gene, get_gene_list, get_interactions, get_source


def test_get_drugs(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with requests_mock.Mocker() as m, (
        fixtures_dir / "get_drug_api_response.json"
    ).open() as json_response, (
        fixtures_dir / "get_drug_filtered_api_response.json"
    ).open() as filtered_json_response:
        set_up_graphql_mock(m, json_response)

        results = get_drug(["Imatinib"])
        assert isinstance(results, pd.DataFrame), "Results object is a DataFrame"
        assert len(results), "DataFrame is non-empty"

        results_with_added_fake = get_drug(["imatinib", "not-real"])
        assert len(results_with_added_fake) == len(
            results
        ), "Gracefully ignore non-existent search terms"

        # handling filters
        filtered_results = get_drug(["imatinib", "metronidazole"], antineoplastic=True)
        assert len(filtered_results) == 1, "Metronidazole is filtered out"
        assert (
            filtered_results["drug"][0] == "IMATINIB"
        ), "Imatinib is retained by the filter"
        assert results["antineoplastic"].all(), "All results are antineoplastics"

        set_up_graphql_mock(m, filtered_json_response)
        filtered_results = get_drug(["imatinib", "metronidazole"], antineoplastic=False)
        assert len(filtered_results), "DataFrame is non-empty"
        assert "METRONIDAZOLE" in filtered_results["drug"].values

        # empty response
        set_up_graphql_mock(m, StringIO('{"data": {"drugs": {"nodes": []}}}'))
        empty_results = get_drug("not-real")
        assert len(empty_results) == 0, "Handles empty response"


def test_get_genes(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with requests_mock.Mocker() as m, (
        fixtures_dir / "get_gene_api_response.json"
    ).open() as json_response:
        set_up_graphql_mock(m, json_response)

        results = get_gene(["ereg"])
        assert isinstance(results, pd.DataFrame), "Results object is a DataFrame"
        assert len(results), "DataFrame is non-empty"

        results_with_added_fake = get_gene(["ereg", "not-real"])
        assert len(results_with_added_fake) == len(
            results
        ), "Gracefully ignore non-existent search terms"

        # empty response
        set_up_graphql_mock(m, StringIO('{"data": {"genes": {"nodes": []}}}'))
        empty_results = get_gene("not-real")
        assert len(empty_results) == 0, "Handles empty response"


def test_get_interactions_by_genes(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with requests_mock.Mocker() as m, (
        fixtures_dir / "get_interactions_by_genes_response.json"
    ).open() as genes_response, (
        fixtures_dir / "get_interactions_by_multiple_genes_response.json"
    ).open() as multiple_genes_response:
        set_up_graphql_mock(m, genes_response)
        results = get_interactions(["ereg"])
        assert isinstance(results, pd.DataFrame), "Results object is a DataFrame"
        assert len(results), "Results are non-empty"

        results = get_interactions(["ereg", "not-real"])
        assert len(results), "Handles additional not-real terms gracefully"

        # multiple terms
        set_up_graphql_mock(m, multiple_genes_response)
        multiple_gene_results = get_interactions(["ereg", "braf"])
        assert len(multiple_gene_results) > len(results), "Handles multiple genes at once"

        # empty response
        set_up_graphql_mock(m, StringIO('{"data": {"genes": {"nodes": []}}}'))
        empty_results = get_interactions(["not-real"])
        assert len(empty_results) == 0, "Handles empty response"


def test_get_interactions_by_drugs(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with requests_mock.Mocker() as m, (
        fixtures_dir / "get_interactions_by_drugs_response.json"
    ).open() as drugs_response, (
        fixtures_dir / "get_interactions_by_multiple_drugs_response.json"
    ).open() as multiple_drugs_response:
        set_up_graphql_mock(m, drugs_response)
        results = get_interactions(["sunitinib"], search="drugs")
        assert isinstance(results, pd.DataFrame), "Results object is a DataFrame"
        assert len(results), "Results are non-empty"

        results = get_interactions(["sunitinib", "not-real"], search="drugs")
        assert len(results), "Handles additional not-real terms gracefully"

        # multiple terms
        set_up_graphql_mock(m, multiple_drugs_response)
        multiple_gene_results = get_interactions(["sunitinib", "clonazepam"], search="drugs")
        assert len(multiple_gene_results) > len(results), "Handles multiple drugs at once"

        # empty response
        set_up_graphql_mock(m, StringIO('{"data": {"drugs": {"nodes": []}}}'))
        empty_results = get_interactions(["not-real"], search="drugs")
        assert len(empty_results) == 0, "Handles empty response"


def test_get_categories(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with requests_mock.Mocker() as m, (
        fixtures_dir / "get_categories_response.json"
    ).open() as categories_response:
        set_up_graphql_mock(m, categories_response)
        results = get_categories("BRAF")
        assert len(results), "Results are non-empty"
        assert "DRUG RESISTANCE" in results["categories"].values
        assert "DRUGGABLE GENOME" in results["categories"].values
        assert "CLINICALLY ACTIONABLE" in results["categories"].values


def test_get_sources(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with requests_mock.Mocker() as m, (
        fixtures_dir / "get_sources_response.json"
    ).open() as sources_response, (
        fixtures_dir / "get_sources_filtered_response.json"
    ).open() as filtered_sources_response:
        set_up_graphql_mock(m, sources_response)
        results = get_source()
        sources = results["sources"]["nodes"]
        assert len(sources) == 45, f"Incorrect # of sources: {len(sources)}"

        set_up_graphql_mock(m, filtered_sources_response)
        results = get_source("GENE")
        sources = results["sources"]["nodes"]
        assert len(sources) == 3, f"Incorrect # of sources: {len(sources)}"
        assert {s["sourceDbName"] for s in sources} == {"NCBI", "HGNC", "Ensembl"}, "Contains correct sources"


def test_get_gene_list(fixtures_dir: Path, set_up_graphql_mock: Callable):
    with requests_mock.Mocker() as m, (
        fixtures_dir / "get_gene_list_response.json"  # this fixture is truncated from the real response
    ).open() as gene_list_response:
        set_up_graphql_mock(m, gene_list_response)

        results = get_gene_list()
        assert len(results) == 9


def test_get_drug_applications(fixtures_dir, set_up_graphql_mock: Callable):
    with requests_mock.Mocker() as m, (
        fixtures_dir / "get_drug_applications_response.json"
    ).open() as drug_applications_response, (
        fixtures_dir / "get_drug_applications_drugsatfda_response.json"
    ).open() as drugsatfda_response:
        set_up_graphql_mock(m, drug_applications_response)
        m.get("https://api.fda.gov/drug/drugsfda.json?search=openfda.application_number:%22NDA212099%22", text=drugsatfda_response.read())
        results = get_drug_applications(["DAROLUTAMIDE"])
        assert len(results) == 1
        assert results.iloc[0]["description"] == "NUBEQA: 300MG Prescription TABLET"


@pytest.mark.performance
def test_get_interactions_benchmark(benchmark):
    """Skipped by default -- call pytest with `--performance` flag to run.

    See `conftest.py` for details.
    """
    query = "braf"
    results = benchmark.pedantic(
        get_interactions,
        args=(query,),
        kwargs={"search": "genes"},
        rounds=10,
        warmup_rounds=0,
        iterations=1,
    )
    assert results.columns[0] == "gene"
