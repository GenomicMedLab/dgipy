"""Provides methods for performing different searches in DGIdb"""
import pandas as pd
import requests


# TODO: learn how to implement global variables to reflect which API end point to use
def __api_url(env: str = "local") -> str:
    url = "http://localhost:3000/api/graphql"

    if env == "local":
        url = "http://localhost:3000/api/graphql"

    if env == "staging":
        url = "https://staging.dgidb.org/api/graphql"

    if env == "production":
        url = "https://dgidb.org/api/graphql"

    return url


base_url = __api_url("local")


def format_filters(filter_dict: dict) -> str:
    """Take a dictionary of filters from a query method and transform it into a string for get_ methods

    :param filter_dict: a dictionary of supported filters. made during get_ methods
    :return: a formatted string for GraphQL queries in get_ methods
    """
    filter_string = ""

    for key in filter_dict:
        if filter_dict[key] is not None:
            value = (
                str(filter_dict[key]).lower()
                if isinstance(type(filter_dict[key]), bool)
                else f'"{filter_dict[key]}"'
            )
            # TO DO: catch for PMID?
            filter_string = filter_string + f", {key}: {value}"
        else:
            pass

    return filter_string


def get_drug(
    terms: list | str,
    use_pandas: bool = True,
    immunotherapy: str | None = None,
    antineoplastic: str | None = None,
) -> pd.DataFrame | dict:
    """Perform a record look up in DGIdb for a drug of interest

    :param terms: drug or drugs for record lookup
    :param use_pandas: boolean for whether pandas should be used to format response
    :param immunotherapy: filter option for results that are only immunotherapy
    :param antineoplastic: filter option for results that see antineoplastic use
    :return: record page results for drug in either a dataframe or json object
    """
    if isinstance(terms, list):
        terms = '","'.join(terms)

    filters = format_filters(
        {"immunotherapy": immunotherapy, "antiNeoplastic": antineoplastic}
    )

    query = (
        '{\ndrugs(names: ["'
        + terms.upper()
        + '"]'
        + filters
        + ") {\nnodes{\nname\nconceptId\ndrugAliases {\nalias\n}\ndrugAttributes {\nname\nvalue\n}\nantiNeoplastic\nimmunotherapy\napproved\ndrugApprovalRatings {\nrating\nsource {\nsourceDbName\n}\n}\ndrugApplications {\nappNo\n}\n}\n}\n}\n"
    )

    r = requests.post(base_url, json={"query": query}, timeout=20)

    if use_pandas is True:
        data = __process_drug(r.json())
    elif use_pandas is False:
        data = r.json()

    return data


def get_gene(terms: list | str, use_pandas: bool = True) -> pd.DataFrame | dict:
    """Perform a record look up in DGIdb for a gene of interest

    :param terms: gene or genes for record lookup
    :param use_pandas: boolean for whether pandas should be used to format response
    :return: record page results for gene in either a dataframe or json object
    """
    if isinstance(terms, list):
        terms = '","'.join(terms)

    query = (
        '{\ngenes(names: ["'
        + terms.upper()
        + '"]) {\nnodes\n{name\nlongName\nconceptId\ngeneAliases {\nalias\n}\ngeneAttributes {\nname\nvalue\n}\n}\n}\n}'
    )

    r = requests.post(base_url, json={"query": query}, timeout=20)

    if use_pandas is True:
        data = __process_gene(r.json())
    elif use_pandas is False:
        data = r.json()

    return data


def get_interactions(
    terms: list | str,
    search: str = "genes",
    use_pandas: bool = True,
    immunotherapy: str | None = None,
    antineoplastic: str | None = None,
    sourcedbname: str | None = None,
    pmid: str | None = None,
    interactiontype: str | None = None,
    approved: str | None = None,
) -> pd.DataFrame | dict:
    """Perform an interaction look up for drugs or genes of interest

    :param terms: drugs or genes for interaction look up
    :param search: interaction search type. valid types are "drugs" or "genes"
    :param use_pandas: boolean for whether pandas should be used to format response
    :param immunotherapy: filter option for results that are used in immunotherapy
    :param antineoplastic: filter option for results that are part of antineoplastic regimens
    :param sourcedbname: filter option for specific databases of interest
    :param pmid: filter option for specific PMIDs:
    :param interactiontype: filter option for specific interaction types
    :param approved: filter option for approved interactions
    :return: interaction results for terms in either a dataframe or a json object
    """
    if isinstance(terms, list):
        terms = '","'.join(terms)

    if search == "genes":
        immunotherapy = None
        antineoplastic = None

    filters = format_filters(
        {
            "immunotherapy": immunotherapy,
            "antiNeoplastic": antineoplastic,
            "sourceDbName": sourcedbname,
            "pmid": pmid,
            "interactiontype": interactiontype,
            "approved": approved,
        }
    )

    if search == "genes":
        query = (
            '{\ngenes(names: ["'
            + terms.upper()
            + '"]'
            + filters
            + ") {\nnodes{\nname\nlongName\ngeneCategories{\nname\n}\ninteractions {\ninteractionAttributes {\nname\nvalue\n}\ndrug {\nname\napproved\n}\ninteractionScore\ninteractionClaims {\npublications {\npmid\ncitation\n}\nsource {\nfullName\nid\n}\n}\n}\n}\n}\n}"
        )
    elif search == "drugs":
        query = (
            '{\ndrugs(names: ["'
            + terms.upper()
            + '"]'
            + filters
            + ") {\nnodes{\nname\napproved\ninteractions {\ngene {\nname\n}\ninteractionAttributes {\nname\nvalue\n}\ninteractionScore\ninteractionClaims {\npublications {\npmid\ncitation\n}\nsource {\nfullName\nid\n}\n}\n}\n}\n}\n}"
        )
    else:
        msg = "Search type must be specified using: search='drugs' or search='genes'"
        raise Exception(msg)

    r = requests.post(base_url, json={"query": query}, timeout=20)

    if use_pandas is True:
        if search == "genes":
            data = __process_gene_search(r.json())
        elif search == "drugs":
            data = __process_drug_search(r.json())
        else:
            msg = (
                "Search type must be specified using: search='drugs', or search='genes'"
            )
            raise Exception(msg)

    elif use_pandas is False:
        return r.json()

    return data


def get_categories(terms: list | str, use_pandas: bool = True) -> pd.DataFrame | dict:
    """Perform a category annotation lookup for genes of interest

    :param terms: Genes of interest for annotations
    :param use_pandas: boolean for whether pandas should be used to format a response
    :return: category annotation results for genes formatted in a dataframe or a json object
    """
    if isinstance(terms, list):
        terms = '","'.join(terms)

    query = (
        '{\ngenes(names: ["'
        + terms.upper()
        + '"]) {\nnodes{\nname\nlongName\ngeneCategoriesWithSources{\nname\nsourceNames\n}\n}\n}\n}'
    )
    r = requests.post(base_url, json={"query": query}, timeout=20)

    if use_pandas is True:
        data = __process_gene_categories(r.json())
    elif use_pandas is False:
        data = r.json()

    return data


def get_source(search: str = "all") -> dict:
    """Perform a source lookup for relevant aggregate sources

    :param search: string to denote type of source to lookup
    :return: all sources of relevant type in a json object
    """
    valid_types = ["all", "drug", "gene", "interaction", "potentially_druggable"]

    if search.lower() not in valid_types:
        msg = "Type must be a valid source type: drug, gene, interaction, potentially_druggable"
        raise Exception(msg)

    if search == "all":
        query = "{\nsources {\nnodes {\nfullName\nsourceDbName\nsourceDbVersion\ndrugClaimsCount\ngeneClaimsCount\ninteractionClaimsCount\n}\n}\n}"

    else:
        query = (
            "{\nsources(sourceType: "
            + search.upper()
            + ") {\nnodes {\nfullName\nsourceDbName\nsourceDbVersion\ndrugClaimsCount\ngeneClaimsCount\ninteractionClaimsCount\n}\n}\n}"
        )

    r = requests.post(base_url, json={"query": query}, timeout=20)

    return r.json()


def get_gene_list() -> list:
    """Get all gene names present in DGIdb

    :return: a full list of genes present in dgidb
    """
    query = "{\ngenes {\nnodes {\nname\n}\n}\n}"
    r = requests.post(base_url, json={"query": query}, timeout=20)
    gene_list = []
    for match in r.json()["data"]["genes"]["nodes"]:
        gene_name = match["name"]
        gene_list.append(gene_name)
    gene_list.sort()
    return gene_list


def get_drug_applications(
    terms: list | str, use_pandas: bool = True
) -> pd.DataFrame | dict:
    """Perform a look up for ANDA/NDA applications for drug or drugs of interest

    :param terms: drug or drugs of interest
    :param use_pandas: boolean for whether to format response in DataFrame
    :return: all ANDA/NDA applications for drugs of interest in json or DataFrame
    """
    if isinstance(terms, list):
        terms = '","'.join(terms)

    query = (
        '{\ndrugs(names: ["'
        + terms.upper()
        + '"]) {\nnodes{\nname \ndrugApplications {\nappNo\n}\n}\n}\n}\n'
    )

    r = requests.post(base_url, json={"query": query}, timeout=20)

    if use_pandas is True:
        data = __process_drug_applications(r.json())
        data = __openfda_data(data)
    elif use_pandas is False:
        data = r.json()

    return data


def __process_drug(results: dict) -> pd.DataFrame:
    drug_list = []
    concept_list = []
    alias_list = []
    attribute_list = []
    antineoplastic_list = []
    immunotherapy_list = []
    approved_list = []
    rating_list = []
    application_list = []

    for match in results["data"]["drugs"]["nodes"]:
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


def __process_gene(results: dict) -> pd.DataFrame:
    gene_list = []
    alias_list = []
    concept_list = []
    attribute_list = []

    for match in results["data"]["genes"]["nodes"]:
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


def __process_gene_search(results: dict) -> pd.DataFrame:
    interactionscore_list = []
    drugname_list = []
    approval_list = []
    interactionattributes_list = []
    gene_list = []
    longname_list = []
    sources_list = []
    pmids_list = []
    # genecategories_list = []

    for match in results["data"]["genes"]["nodes"]:
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

            list_string = []
            for attribute in interaction["interactionAttributes"]:
                list_string.append(f"{attribute['name']}: {attribute['value']}")
            interactionattributes_list.append(" | ".join(list_string))

            list_string = []
            sub_list_string = []
            for claim in interaction["interactionClaims"]:
                list_string.append(f"{claim['source']['fullName']}")
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


def __process_gene_categories(results: dict) -> pd.DataFrame:
    gene_list = []
    categories_list = []
    sources_list = []
    longname_list = []

    for match in results["data"]["genes"]["nodes"]:
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


def __process_drug_search(results: dict) -> pd.DataFrame:
    interactionscore_list = []
    genename_list = []
    approval_list = []
    interactionattributes_list = []
    drug_list = []
    sources_list = []
    pmids_list = []

    for match in results["data"]["drugs"]["nodes"]:
        current_drug = match["name"]
        current_approval = str(match["approved"])

        for interaction in match["interactions"]:
            drug_list.append(current_drug)
            genename_list.append(interaction["gene"]["name"])
            interactionscore_list.append(interaction["interactionScore"])
            approval_list.append(current_approval)

            list_string = []
            for attribute in interaction["interactionAttributes"]:
                list_string.append(f"{attribute['name']}: {attribute['value']}")

            interactionattributes_list.append("| ".join(list_string))

            list_string = []
            sub_list_string = []
            for claim in interaction["interactionClaims"]:
                list_string.append(f"{claim['source']['fullName']}")
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


def __process_drug_applications(data: dict) -> pd.DataFrame:
    drug_list = []
    application_list = []

    for node in data["data"]["drugs"]["nodes"]:
        current_drug = node["name"]
        for application in node["drugApplications"]:
            drug_list.append(current_drug)
            application = application["appNo"].split(".")[1].replace(":", "").upper()
            application_list.append(application)

    return pd.DataFrame().assign(drug=drug_list, application=application_list)


def __openfda_data(dataframe: pd.DataFrame) -> pd.DataFrame:
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
