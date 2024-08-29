"""Provides methods for performing different searches in DGIdb"""

import logging
import os
from enum import Enum

import requests
from gql import Client
from gql.transport.requests import RequestsHTTPTransport

import dgipy.queries as queries

_logger = logging.getLogger(__name__)

API_ENDPOINT_URL = os.environ.get("DGIDB_API_URL", "https://dgidb.org/api/graphql")


_logger = logging.getLogger(__name__)


def _get_client(api_url: str) -> Client:
    """Acquire GraphQL client.

    :param api_url: endpoint to request data at
    :return: GraphQL client
    """
    transport = RequestsHTTPTransport(url=api_url)
    return Client(transport=transport, fetch_schema_from_transport=True)


def _group_attributes(row: list[dict]) -> dict:
    grouped_dict = {}
    for attr in row:
        if attr["name"] in grouped_dict:
            grouped_dict[attr["name"]].append(attr["value"])
        else:
            grouped_dict[attr["name"]] = [attr["value"]]
    return grouped_dict


def get_drug(
    terms: list | str,
    immunotherapy: bool | None = None,
    antineoplastic: bool | None = None,
    api_url: str | None = None,
) -> dict:
    """Perform a record look up in DGIdb for a drug of interest

    :param terms: drug or drugs for record lookup
    :param immunotherapy: filter option for results that are only immunotherapy
    :param antineoplastic: filter option for results that see antineoplastic use
    :param api_url: API endpoint for GraphQL request
    :return: drug data
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

    output = {
        "name": [],
        "concept_id": [],
        "aliases": [],
        "attributes": [],
        "antineoplastic": [],
        "immunotherapy": [],
        "approved": [],
        "approval_ratings": [],
        "fda_applications": [],
    }
    for match in result["drugs"]["nodes"]:
        output["name"].append(match["name"])
        output["concept_id"].append(match["conceptId"])
        output["aliases"].append([a["alias"] for a in match["drugAliases"]])
        output["attributes"].append(_group_attributes(match["drugAttributes"]))
        output["antineoplastic"].append(match["antiNeoplastic"])
        output["immunotherapy"].append(match["immunotherapy"])
        output["approved"].append(match["approved"])
        output["approval_ratings"].append(
            [
                {"rating": r["rating"], "source": r["source"]["sourceDbName"]}
                for r in match["drugApprovalRatings"]
            ]
        )
        output["fda_applications"].append(
            [app["appNo"] for app in match["drugApplications"]]
        )
    return output


def get_gene(terms: list | str, api_url: str | None = None) -> dict:
    """Perform a record look up in DGIdb for a gene of interest

    :param terms: gene or genes for record lookup
    :param api_url: API endpoint for GraphQL request
    :return: gene data
    """
    if isinstance(terms, str):
        terms = [terms]

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    result = client.execute(queries.get_genes.query, variable_values={"names": terms})

    output = {
        "name": [],
        "concept_id": [],
        "aliases": [],
        "attributes": [],
    }
    for match in result["genes"]["nodes"]:
        output["name"].append(match["name"])
        output["concept_id"].append(match["conceptId"])
        output["aliases"].append([a["alias"] for a in match["geneAliases"]])
        output["attributes"].append(_group_attributes(match["geneAttributes"]))
    return output


def get_interactions(
    terms: list | str,
    search: str = "genes",
    immunotherapy: bool | None = None,
    antineoplastic: bool | None = None,
    source: str | None = None,
    pmid: int | None = None,
    interaction_type: str | None = None,
    approved: str | None = None,
    api_url: str | None = None,
) -> dict:
    """Perform an interaction look up for drugs or genes of interest

    :param terms: drugs or genes for interaction look up
    :param search: interaction search type. valid types are "drugs" or "genes"
    :param immunotherapy: filter option for results that are used in immunotherapy
    :param antineoplastic: filter option for results that are part of antineoplastic regimens
    :param source: filter option for specific database of interest
    :param pmid: filter option for specific PMID
    :param interaction_type: filter option for specific interaction types
    :param approved: filter option for approved interactions
    :param api_url: API endpoint for GraphQL request
    :return: interaction results for terms
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

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)

    if search == "genes":
        return _get_interactions_by_genes(params, client)
    if search == "drugs":
        return _get_interactions_by_drugs(params, client)
    msg = "Search type must be specified using: search='drugs' or search='genes'"
    raise Exception(msg)


def _get_interactions_by_genes(
    params: dict,
    client: Client,
) -> dict:
    results = client.execute(queries.get_interactions_by_gene.query, params)
    output = {
        "gene_name": [],
        "gene_long_name": [],
        "drug_name": [],
        "approved": [],
        "interaction_score": [],
        "interaction_attributes": [],
        "sources": [],
        "pmids": [],
    }
    for result in results["genes"]["nodes"]:
        gene_name = result["name"]
        long_name = result["longName"]
        for interaction in result["interactions"]:
            output["gene_name"].append(gene_name)
            output["gene_long_name"].append(long_name)
            output["drug_name"].append(interaction["drug"]["name"])
            output["approved"].append(interaction["drug"]["approved"])
            output["interaction_score"].append(interaction["interactionScore"])
            output["interaction_attributes"].append(
                _group_attributes(interaction["interactionAttributes"])
            )

            pubs = []
            sources = []
            for claim in interaction["interactionClaims"]:
                sources.append(claim["source"]["sourceDbName"])
                pubs += [p["pmid"] for p in claim["publications"]]
            output["pmids"].append(pubs)
            output["sources"].append(sources)
    return output


def _get_interactions_by_drugs(
    params: dict,
    client: Client,
) -> dict:
    results = client.execute(queries.get_interactions_by_drug.query, params)
    output = {
        "drug_name": [],
        "gene_name": [],
        "interaction_score": [],
        "approved": [],
        "interaction_attributes": [],
        "sources": [],
        "pmids": [],
    }
    for result in results["drugs"]["nodes"]:
        drug_name = result["name"]
        approval = result["approved"]
        for interaction in result["interactions"]:
            output["drug_name"].append(drug_name)
            output["gene_name"].append(interaction["gene"]["name"])
            output["interaction_score"].append(interaction["interactionScore"])
            output["approved"].append(approval)
            output["interaction_attributes"].append(
                _group_attributes(interaction["interactionAttributes"])
            )
            pubs = []
            sources = []
            for claim in interaction["interactionClaims"]:
                sources.append(claim["source"]["sourceDbName"])
                pubs += [p["pmid"] for p in claim["publications"]]
            output["pmids"].append(pubs)
            output["sources"].append(sources)
    return output


def get_categories(terms: list | str, api_url: str | None = None) -> dict:
    """Perform a category annotation lookup for genes of interest

    :param terms: Genes of interest for annotations
    :param api_url: API endpoint for GraphQL request
    :return: category annotation results for genes
    """
    if isinstance(terms, str):
        terms = [terms]

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    results = client.execute(
        queries.get_gene_categories.query, variable_values={"names": terms}
    )
    output = {
        "gene": [],
        "full_name": [],
        "category": [],
        "sources": [],
    }
    for result in results["genes"]["nodes"]:
        name = result["name"]
        long_name = result["longName"]
        for cat in result["geneCategoriesWithSources"]:
            output["gene"].append(name)
            output["full_name"].append(long_name)
            output["category"].append(cat["name"])
            output["sources"].append(cat["sourceNames"])
    return output


class SourceType(str, Enum):
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

    :param source_type: type of source to look up. Fetches all sources otherwise.
    :param api_url: API endpoint for GraphQL request
    :return: all sources of relevant type in a json object
    :raise TypeError: if invalid kind of data given as ``source_type`` param.
    """
    source_param = source_type.value.upper() if source_type is not None else None
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    params = {} if source_type is None else {"sourceType": source_param}
    results = client.execute(queries.get_sources.query, variable_values=params)
    output = {
        "name": [],
        "short_name": [],
        "version": [],
        "drug_claims": [],
        "gene_claims": [],
        "interaction_claims": [],
    }
    for result in results["sources"]["nodes"]:
        output["name"].append(result["fullName"])
        output["short_name"].append(result["sourceDbName"])
        output["version"].append(result["sourceDbVersion"])
        output["drug_claims"].append(result["drugClaimsCount"])
        output["gene_claims"].append(result["geneClaimsCount"])
        output["interaction_claims"].append(result["interactionClaimsCount"])
    return output


def get_gene_list(api_url: str | None = None) -> dict:
    """Get all gene names present in DGIdb

    :param api_url: API endpoint for GraphQL request
    :return: list of genes in DGIdb
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    results = client.execute(queries.get_all_genes.query)
    genes = {"name": [], "concept_id": []}
    for result in results["genes"]["nodes"]:
        genes["name"].append(result["name"])
        genes["concept_id"].append(result["conceptId"])
    return genes


def _get_openfda_data(app_no: str) -> list[tuple]:
    url = f'https://api.fda.gov/drug/drugsfda.json?search=openfda.application_number:"{app_no}"'
    response = requests.get(url, headers={"User-Agent": "Custom"}, timeout=20)
    try:
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        _logger.error("Request to %s failed: %s", url, e)
        raise e
    data = response.json()
    return [
        (
            product["brand_name"],
            product["marketing_status"],
            product["dosage_form"],
            product["active_ingredients"][0]["strength"],
        )
        for product in data["results"][0]["products"]
    ]


def get_drug_applications(terms: list | str, api_url: str | None = None) -> dict:
    """Perform a look up for ANDA/NDA applications for drug or drugs of interest

    :param terms: drug or drugs of interest
    :param api_url: API endpoint for GraphQL request
    :return: all ANDA/NDA applications for drugs of interest
    """
    if isinstance(terms, str):
        terms = [terms]

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    results = client.execute(
        queries.get_drug_applications.query, variable_values={"names": terms}
    )
    output = {
        "name": [],
        "application": [],
        "brand_name": [],
        "marketing_status": [],
        "dosage_form": [],
        "dosage_strength": [],
    }

    for result in results["drugs"]["nodes"]:
        name = result["name"]
        for app in result["drugApplications"]:
            application_number = app["appNo"].split(".")[1].replace(":", "").upper()
            for (
                brand_name,
                marketing_status,
                dosage_form,
                dosage_strength,
            ) in _get_openfda_data(application_number):
                output["name"].append(name)
                output["application"].append(application_number)
                output["brand_name"].append(brand_name)
                output["marketing_status"].append(marketing_status)
                output["dosage_form"].append(dosage_form)
                output["dosage_strength"].append(dosage_strength)

    return output


def get_clinical_trials(
    terms: str | list,
) -> dict:
    """Perform a look up for clinical trials data for drug or drugs of interest

    :param terms: drug or drugs of interest
    :return: all clinical trials data for drugs of interest in a DataFrame
    """
    base_url = "https://clinicaltrials.gov/api/v2/studies?format=json"

    if isinstance(terms, str):
        terms = [terms]

    output = {
        "search_term": [],
        "trial_id": [],
        "brief": [],
        "study_type": [],
        "min_age": [],
        "age_groups": [],
        "pediatric": [],
        "conditions": [],
        "interventions": [],
    }

    for drug in terms:
        intr_url = f"&query.intr={drug}"
        full_uri = base_url + intr_url  # TODO: + cond_url + term_url
        response = requests.get(full_uri, timeout=20)
        try:
            response.raise_for_status()
        except requests.exceptions.RequestException as e:
            _logger.error("Clinical trials lookup to URL %s failed: %s", full_uri, e)
            raise e
        if response.status_code != 200:
            _logger.error(
                "Received status code %s from request to %s -- returning empty dataframe",
                response.status_code,
                full_uri,
            )
        else:
            data = response.json()

            for study in data["studies"]:
                output["search_term"].append(drug)
                output["trial_id"].append(
                    study["protocolSection"]["identificationModule"]["nctId"]
                )
                output["brief"].append(
                    study["protocolSection"]["identificationModule"]["briefTitle"]
                )
                output["study_type"].append(
                    study["protocolSection"]["designModule"]["studyType"]
                )
                try:
                    output["min_age"].append(
                        study["protocolSection"]["eligibilityModule"]["minimumAge"]
                    )
                except KeyError:
                    output["min_age"].append(None)

                age_groups = study["protocolSection"]["eligibilityModule"]["stdAges"]

                output["age_groups"].append(age_groups)
                output["pediatric"].append("CHILD" in age_groups)
                output["conditions"].append(
                    study["protocolSection"]["conditionsModule"]["conditions"]
                )
                try:
                    output["interventions"].append(
                        study["protocolSection"]["armsInterventionsModule"]
                    )
                except:
                    output["interventions"].append(None)
    return output
