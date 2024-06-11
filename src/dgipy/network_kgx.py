from typing import List, Union

import pandas as pd
from kgx.graph.nx_graph import NxGraph
from kgx.validator import Validator

from dgipy import dgidb


def get_kgx_network_graph(terms: Union[List, str], search: str = "genes"):
    interactions = dgidb.get_interactions(terms, search)
    interactions["gene_concept_id"] = interactions["gene_concept_id"].apply(
        __fix_conceptid_prefix
    )
    interactions["drug_concept_id"] = interactions["drug_concept_id"].apply(
        __fix_conceptid_prefix
    )
    network_graph = __initalize_network(interactions, terms, search)

    validator = Validator(verbose=True)
    validator.validate(network_graph)
    errors = validator.get_errors()
    if len(errors) > 0:
        print(errors)

    return network_graph


def __fix_conceptid_prefix(concept_id: str):
    prefix_rules = {"CHEMBL": "CHEMBL.MECHANISM", "IUPHAR.LIGAND": "IUPHAR.FAMILY"}
    concept_id = concept_id.upper()
    prefix = concept_id.split(":")[0]
    id = concept_id.split(":")[1]
    if prefix in prefix_rules:
        return prefix_rules[prefix] + ":" + id
    return concept_id


def __initalize_network(interactions: pd.DataFrame, terms: List, search: str) -> NxGraph:
    interactions_graph = NxGraph()
    if search == "genes":
        graphed_genes = set()
        for index in interactions.index:
            graphed_genes.add(interactions["gene"][index])
            interactions_graph.add_node(
                interactions["gene_concept_id"][index],
                id=interactions["gene"][index],
                category=[],
            )
            interactions_graph.add_node(
                interactions["drug_concept_id"][index],
                id=interactions["drug"][index],
                category=[],
            )
            interactions_graph.add_edge(
                subject_node=interactions["gene_concept_id"][index],
                object_node=interactions["drug_concept_id"][index],
                id=interactions["gene_concept_id"][index]
                + " - "
                + interactions["drug_concept_id"][index],
                subject=interactions["gene"][index],
                object=interactions["drug"][index],
                predicate="biolink:related_to",
                knowledge_level="",
                agent_type="",
            )
        ungraphed_genes = list(set(terms).difference(graphed_genes))
        gene_data = dgidb.get_gene(ungraphed_genes)
        id_dict = dict(zip(gene_data["gene"],gene_data["concept_id"]))
        for gene in ungraphed_genes:
            interactions_graph.add_node(id_dict[gene], id=gene, category=[])
    elif search == "drugs":
        graphed_drugs = set()
        for index in interactions.index:
            graphed_drugs.add(interactions["drug"][index])
            interactions_graph.add_node(
                interactions["drug_concept_id"][index],
                id=interactions["drug"][index],
                category=[],
            )
            interactions_graph.add_node(
                interactions["gene_concept_id"][index],
                id=interactions["gene"][index],
                category=[],
            )
            interactions_graph.add_edge(
                subject_node=interactions["drug_concept_id"][index],
                object_node=interactions["gene_concept_id"][index],
                id=interactions["drug_concept_id"][index]
                + " - "
                + interactions["gene_concept_id"][index],
                subject=interactions["drug"][index],
                object=interactions["gene"][index],
                predicate="biolink:related_to",
                knowledge_level="",
                agent_type="",
            )
        ungraphed_drugs = list(set(terms).difference(graphed_drugs))
        drug_data = dgidb.get_drug(ungraphed_drugs)
        id_dict = dict(zip(drug_data["drug"],drug_data["concept_id"]))
        for drug in ungraphed_drugs:
            interactions_graph.add_node(id_dict[drug], id=drug, category=[])
    return interactions_graph
