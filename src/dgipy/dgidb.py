"""Provides methods for performing different searches in DGIdb"""

import os

import pandas as pd
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
    :return: TODO
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
    :return: TODO
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
        output["aliases"].append([[a["alias"] for a in match["geneAliases"]]])
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
) -> pd.DataFrame | dict:
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

    # if use_pandas is True:
    #     if search == "genes":
    #         return _process_gene_search(result)
    #     return _process_drug_search(result)
    return result  # noqa: RET504


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


def get_categories(terms: list | str, api_url: str | None = None) -> dict:
    """Perform a category annotation lookup for genes of interest

    :param terms: Genes of interest for annotations
    :param api_url: API endpoint for GraphQL request
    :return: category annotation results for genes formatted in a dataframe or a json object
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
        "concept_id": [],
        "full_name": [],
        "category": [],
        "sources": [],
    }
    for result in results["genes"]["nodes"]:
        name = result["name"]
        concept_id = result["conceptId"]
        long_name = result["longName"]
        for cat in result["geneCategoriesWithSources"]:
            output["gene"].append(name)
            output["concept_id"].append(concept_id)
            output["full_name"].append(long_name)
            output["category"].append(cat["name"])
            output["sources"].append(cat["sourceNames"])
    return output


def get_source(search: str = "all", api_url: str | None = None) -> dict:
    """Perform a source lookup for relevant aggregate sources

    :param search: string to denote type of source to lookup
    :param api_url: API endpoint for GraphQL request
    :return: all sources of relevant type in a json object
    """
    valid_types = ["all", "drug", "gene", "interaction", "potentially_druggable"]
    if search.lower() not in valid_types:
        msg = "Type must be a valid source type: drug, gene, interaction, potentially_druggable"
        raise Exception(msg)

    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    params = {} if search.lower() == "all" else {"sourceType": search}
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
    :return: todo
    """
    api_url = api_url if api_url else API_ENDPOINT_URL
    client = _get_client(api_url)
    results = client.execute(queries.get_all_genes.query)
    genes = {"name": [], "concept_id": []}
    for result in results["genes"]["nodes"]:
        genes["name"].append(result["name"])
        genes["concept_id"].append(result["conceptId"])
    return genes


def get_drug_applications(
    terms: list | str, api_url: str | None = None
) -> pd.DataFrame | dict:
    """Perform a look up for ANDA/NDA applications for drug or drugs of interest

    :param terms: drug or drugs of interest
    :param api_url: API endpoint for GraphQL request
    :return: all ANDA/NDA applications for drugs of interest in json or DataFrame
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
        "description": [],
    }

    for result in results["drugs"]["nodes"]:
        name = result["name"]
        for app in result["drugApplications"]:
            output["name"].append(name)
            application_number = app["appNo"].split(".")[1].replace(":", "").upper()
            output["application"].append(application_number)
            # output["description"].append(_get_openfda_description(application_number))
    return output


# def _openfda_data(dataframe: pd.DataFrame) -> pd.DataFrame:
#     openfda_base_url = (
#         "https://api.fda.gov/drug/drugsfda.json?search=openfda.application_number:"
#     )
#     terms = list(dataframe["application"])
#     descriptions = []
#     for term in terms:
#         r = requests.get(
#             f'{openfda_base_url}"{term}"', headers={"User-Agent": "Custom"}, timeout=20
#         )
#         try:
#             r.json()["results"][0]["products"]
#
#             f = []
#             for product in r.json()["results"][0]["products"]:
#                 brand_name = product["brand_name"]
#                 marketing_status = product["marketing_status"]
#                 dosage_form = product["dosage_form"]
#                 # active_ingredient = product["active_ingredients"][0]["name"]
#                 dosage_strength = product["active_ingredients"][0]["strength"]
#                 f.append(
#                     f"{brand_name}: {dosage_strength} {marketing_status} {dosage_form}"
#                 )
#
#             descriptions.append(" | ".join(f))
#         except:
#             descriptions.append("none")
#
#     return dataframe.assign(description=descriptions)
