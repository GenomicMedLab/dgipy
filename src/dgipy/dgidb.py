"""Provides methods for performing different searches in DGIdb"""

import os
from enum import StrEnum

import pandas as pd
import requests
from gql import Client
from gql.transport.requests import RequestsHTTPTransport

import dgipy.queries as queries

API_ENDPOINT_URL = os.environ.get("DGIDB_API_URL", "https://dgidb.org/api/graphql")


def _get_client(api_url: str) -> Client:
    """Acquire GraphQL client.

    :param api_url: endpoint to request data at
    :return: GraphQL client
    """
    transport = RequestsHTTPTransport(url=api_url)
    return Client(transport=transport, fetch_schema_from_transport=True)


def get_drug(
    terms: list | str,
    use_pandas: bool = True,
    immunotherapy: bool | None = None,
    antineoplastic: bool | None = None,
    api_url: str | None = None,
) -> pd.DataFrame | dict:
    """Perform a record look up in DGIdb for a drug of interest

    :param terms: drug or drugs for record lookup
    :param use_pandas: boolean for whether pandas should be used to format response
    :param immunotherapy: filter option for results that are only immunotherapy
    :param antineoplastic: filter option for results that see antineoplastic use
    :param api_url: API endpoint for GraphQL request
    :return: record page results for drug in either a dataframe or json object
    """
    if isinstance(terms, str):
        terms = [terms]

    params: dict[str, bool | list] = {"names": terms}
    if immunotherapy is not None:
        params["immunotherapy"] = immunotherapy
    if antineoplastic is not None:
        params["antineoplastic"] = antineoplastic

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(queries.get_drugs.query, variable_values=params)

    if use_pandas is True:
        return _process_drug(result)
    return result


def get_gene(
    terms: list | str, use_pandas: bool = True, api_url: str | None = None
) -> pd.DataFrame | dict:
    """Perform a record look up in DGIdb for a gene of interest

    :param terms: gene or genes for record lookup
    :param use_pandas: boolean for whether pandas should be used to format response
    :param api_url: API endpoint for GraphQL request
    :return: record page results for gene in either a dataframe or json object
    """
    if isinstance(terms, str):
        terms = [terms]

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(queries.get_genes.query, variable_values={"names": terms})

    if use_pandas is True:
        return _process_gene(result)
    return result


def get_interactions(
    terms: list | str,
    search: str = "genes",
    use_pandas: bool = True,
    immunotherapy: bool | None = None,
    antineoplastic: bool | None = None,
    source: str | None = None,
    pmid: int | None = None,
    interaction_type: str | None = None,
    approved: str | None = None,
    api_url: str | None = None,
) -> pd.DataFrame | dict:
    """Perform an interaction look up for drugs or genes of interest

    :param terms: drugs or genes for interaction look up
    :param search: interaction search type. valid types are "drugs" or "genes"
    :param use_pandas: boolean for whether pandas should be used to format response
    :param immunotherapy: filter option for results that are used in immunotherapy
    :param antineoplastic: filter option for results that are part of antineoplastic regimens
    :param source: filter option for specific database of interest
    :param pmid: filter option for specific PMID
    :param interaction_type: filter option for specific interaction types
    :param approved: filter option for approved interactions
    :param api_url: API endpoint for GraphQL request
    :return: interaction results for terms in either a dataframe or a json object
    """
    if isinstance(terms, str):
        terms = [terms]
    params: dict[str, str | int | bool | list[str]] = {"names": terms}
    if immunotherapy is not None:
        params["immunotherapy"] = immunotherapy
    if antineoplastic is not None:
        params["antiNeoplastic"] = antineoplastic
    if source is not None:
        params["sourceDbName"] = source
    if pmid is not None:
        params["pmid"] = pmid
    if interaction_type is not None:
        params["interactionType"] = interaction_type
    if approved is not None:
        params["approved"] = approved

    if search == "genes":
        query = queries.get_interactions_by_gene.query
    elif search == "drugs":
        query = queries.get_interactions_by_drug.query
    else:
        msg = "Search type must be specified using: search='drugs' or search='genes'"
        raise Exception(msg)

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(query, variable_values=params)

    if use_pandas is True:
        if search == "genes":
            return _process_gene_search(result)
        return _process_drug_search(result)
    return result


def get_categories(
    terms: list | str, use_pandas: bool = True, api_url: str | None = None
) -> pd.DataFrame | dict:
    """Perform a category annotation lookup for genes of interest

    :param terms: Genes of interest for annotations
    :param use_pandas: boolean for whether pandas should be used to format a response
    :param api_url: API endpoint for GraphQL request
    :return: category annotation results for genes formatted in a dataframe or a json object
    """
    if isinstance(terms, str):
        terms = [terms]

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(
        queries.get_gene_categories.query, variable_values={"names": terms}
    )

    if use_pandas is True:
        return _process_gene_categories(result)
    return result


class SourceType(StrEnum):
    """Constrain source types for :py:method:`dgipy.dgidb.get_source` method."""

    DRUG = "drug"
    GENE = "gene"
    INTERACTION = "interaction"
    POTENTIALLY_DRUGGABLE = "potentially_druggable"


def get_source(
    source_type: SourceType | None = None, api_url: str | None = None
) -> dict:
    """Perform a source lookup for relevant aggregate sources

    >>> from dgipy import get_source, SourceType
    >>> sources = get_source(SourceType.POTENTIALLY_DRUGGABLE)

    :param source_type: string to denote type of source to lookup
    :param api_url: API endpoint for GraphQL request
    :return: all sources of relevant type in a json object
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    params = {} if source_type is None else {"sourceType": source_type.value.upper()}
    return client.execute(queries.get_sources.query, variable_values=params)


def get_gene_list(api_url: str | None = None) -> list:
    """Get all gene names present in DGIdb

    :param api_url: API endpoint for GraphQL request
    :return: a full list of genes present in dgidb
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(queries.get_all_genes.query)
    genes = result["genes"]["nodes"]
    genes.sort(key=lambda i: i["name"])
    return genes


def get_drug_applications(
    terms: list | str, use_pandas: bool = True, api_url: str | None = None
) -> pd.DataFrame | dict:
    """Perform a look up for ANDA/NDA applications for drug or drugs of interest

    :param terms: drug or drugs of interest
    :param use_pandas: boolean for whether to format response in DataFrame
    :param api_url: API endpoint for GraphQL request
    :return: all ANDA/NDA applications for drugs of interest in json or DataFrame
    """
    if isinstance(terms, str):
        terms = [terms]

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(
        queries.get_drug_applications.query, variable_values={"names": terms}
    )

    if use_pandas is True:
        data = _process_drug_applications(result)
        return _openfda_data(data)
    return result


def _process_drug(results: dict) -> pd.DataFrame:
    drug_list = []
    concept_list = []
    alias_list = []
    attribute_list = []
    antineoplastic_list = []
    immunotherapy_list = []
    approved_list = []
    rating_list = []
    application_list = []

    for match in results["drugs"]["nodes"]:
        drug_list.append(match["name"])
        concept_list.append(match["conceptId"])
        alias_list.append("|".join([alias["alias"] for alias in match["drugAliases"]]))
        current_attributes = [
            ": ".join([attribute["name"], attribute["value"]])
            for attribute in match["drugAttributes"]
        ]
        attribute_list.append(" | ".join(current_attributes))
        antineoplastic_list.append(str(match["antiNeoplastic"]))
        immunotherapy_list.append(str(match["immunotherapy"]))
        approved_list.append(str(match["approved"]))
        application_list.append(
            "|".join(app["appNo"] for app in match["drugApplications"])
        )
        current_ratings = [
            ": ".join([rating["source"]["sourceDbName"], rating["rating"]])
            for rating in match["drugApprovalRatings"]
        ]
        rating_list.append(" | ".join(current_ratings))

    return pd.DataFrame().assign(
        drug=drug_list,
        concept_id=concept_list,
        aliases=alias_list,
        attributes=attribute_list,
        antineoplastic=antineoplastic_list,
        immunotherapy=immunotherapy_list,
        approved=approved_list,
        approval_ratings=rating_list,
        applications=application_list,
    )


def _process_gene(results: dict) -> pd.DataFrame:
    gene_list = []
    alias_list = []
    concept_list = []
    attribute_list = []

    for match in results["genes"]["nodes"]:
        gene_list.append(match["name"])
        alias_list.append("|".join([alias["alias"] for alias in match["geneAliases"]]))
        current_attributes = [
            ": ".join([attribute["name"], attribute["value"]])
            for attribute in match["geneAttributes"]
        ]
        attribute_list.append(" | ".join(current_attributes))
        concept_list.append(match["conceptId"])

    return pd.DataFrame().assign(
        gene=gene_list,
        concept_id=concept_list,
        aliases=alias_list,
        attributes=attribute_list,
    )


def _process_gene_search(results: dict) -> pd.DataFrame:
    interactionscore_list = []
    drugname_list = []
    approval_list = []
    interactionattributes_list = []
    gene_list = []
    longname_list = []
    sources_list = []
    pmids_list = []
    # genecategories_list = []

    for match in results["genes"]["nodes"]:
        current_gene = match["name"]
        current_longname = match["longName"]

        # TO DO: Evaluate if categories should be returned as part of interactions search. Seems useful but also redundant?
        # list_string = []
        # for category in match['geneCategories']:
        #     list_string.append(f"{category['name']}")
        # current_genecategories = " | ".join(list_string)

        for interaction in match["interactions"]:
            gene_list.append(current_gene)
            # genecategories_list.append(current_genecategories)
            longname_list.append(current_longname)
            drugname_list.append(interaction["drug"]["name"])
            approval_list.append(str(interaction["drug"]["approved"]))
            interactionscore_list.append(interaction["interactionScore"])

            list_string = [
                f"{attribute['name']}: {attribute['value']}"
                for attribute in interaction["interactionAttributes"]
            ]
            interactionattributes_list.append(" | ".join(list_string))

            list_string = []
            sub_list_string = []
            for claim in interaction["interactionClaims"]:
                list_string.append(f"{claim['source']['sourceDbName']}")
                sub_list_string = []
                for publication in claim["publications"]:
                    sub_list_string.append(f"{publication['pmid']}")
            sources_list.append(" | ".join(list_string))
            pmids_list.append(" | ".join(sub_list_string))

    return pd.DataFrame().assign(
        gene=gene_list,
        drug=drugname_list,
        longname=longname_list,
        # categories=genecategories_list,
        approval=approval_list,
        score=interactionscore_list,
        interaction_attributes=interactionattributes_list,
        source=sources_list,
        pmid=pmids_list,
    )


def _process_gene_categories(results: dict) -> pd.DataFrame:
    gene_list = []
    categories_list = []
    sources_list = []
    longname_list = []

    for match in results["genes"]["nodes"]:
        current_gene = match["name"]
        current_longname = match["longName"]

        for category in match["geneCategoriesWithSources"]:
            gene_list.append(current_gene)
            longname_list.append(current_longname)
            categories_list.append(category["name"])
            sources_list.append(" | ".join(category["sourceNames"]))

    return pd.DataFrame().assign(
        gene=gene_list,
        longname=longname_list,
        categories=categories_list,
        sources=sources_list,
    )


def _process_drug_search(results: dict) -> pd.DataFrame:
    interactionscore_list = []
    genename_list = []
    approval_list = []
    interactionattributes_list = []
    drug_list = []
    sources_list = []
    pmids_list = []

    for match in results["drugs"]["nodes"]:
        current_drug = match["name"]
        current_approval = str(match["approved"])

        for interaction in match["interactions"]:
            drug_list.append(current_drug)
            genename_list.append(interaction["gene"]["name"])
            interactionscore_list.append(interaction["interactionScore"])
            approval_list.append(current_approval)

            list_string = [
                f"{attribute['name']}: {attribute['value']}"
                for attribute in interaction["interactionAttributes"]
            ]
            interactionattributes_list.append("| ".join(list_string))

            list_string = []
            sub_list_string = []
            for claim in interaction["interactionClaims"]:
                list_string.append(f"{claim['source']['sourceDbName']}")
                sub_list_string = []
                for publication in claim["publications"]:
                    sub_list_string.append(f"{publication['pmid']}")

            sources_list.append(" | ".join(list_string))
            pmids_list.append(" | ".join(sub_list_string))

    return pd.DataFrame().assign(
        drug=drug_list,
        gene=genename_list,
        approval=approval_list,
        score=interactionscore_list,
        interaction_attributes=interactionattributes_list,
        source=sources_list,
        pmid=pmids_list,
    )


def _process_drug_applications(data: dict) -> pd.DataFrame:
    drug_list = []
    application_list = []

    for node in data["drugs"]["nodes"]:
        current_drug = node["name"]
        for application in node["drugApplications"]:
            drug_list.append(current_drug)
            application = application["appNo"].split(".")[1].replace(":", "").upper()
            application_list.append(application)

    return pd.DataFrame().assign(drug=drug_list, application=application_list)


def _openfda_data(dataframe: pd.DataFrame) -> pd.DataFrame:
    openfda_base_url = (
        "https://api.fda.gov/drug/drugsfda.json?search=openfda.application_number:"
    )
    terms = list(dataframe["application"])
    descriptions = []
    for term in terms:
        r = requests.get(
            f'{openfda_base_url}"{term}"', headers={"User-Agent": "Custom"}, timeout=20
        )
        try:
            r.json()["results"][0]["products"]

            f = []
            for product in r.json()["results"][0]["products"]:
                brand_name = product["brand_name"]
                marketing_status = product["marketing_status"]
                dosage_form = product["dosage_form"]
                # active_ingredient = product["active_ingredients"][0]["name"]
                dosage_strength = product["active_ingredients"][0]["strength"]
                f.append(
                    f"{brand_name}: {dosage_strength} {marketing_status} {dosage_form}"
                )

            descriptions.append(" | ".join(f))
        except:
            descriptions.append("none")

    return dataframe.assign(description=descriptions)
