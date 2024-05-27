from typing import List, Union

import pandas as pd
from kgx.graph.nx_graph import NxGraph
from kgx.source import GraphSource
from kgx.transformer import Transformer
from kgx.validator import Validator

from dgipy import dgidb


def get_kgx_interaction(terms: Union[List, str]):
    interactions = dgidb.get_interactions(terms)
    interactions["gene_concept_id"] = interactions["gene_concept_id"].apply(
        __fix_conceptid_prefix
    )
    interactions["drug_concept_id"] = interactions["drug_concept_id"].apply(
        __fix_conceptid_prefix
    )
    network_graph = __initalize_network(interactions, terms)

    validator = Validator(verbose=True)
    validator.validate(network_graph)
    errors = validator.get_errors()
    if len(errors) > 0:
        print(errors)
        return None

    transformer = Transformer()
    source = GraphSource(transformer)
    graph = source.parse(graph=network_graph)


def __fix_conceptid_prefix(concept_id: str):
    prefix_rules = {"CHEMBL": "CHEMBL.MECHANISM", "IUPHAR.LIGAND": "IUPHAR.FAMILY"}
    concept_id = concept_id.upper()
    prefix = concept_id.split(":")[0]
    id = concept_id.split(":")[1]
    if prefix in prefix_rules:
        return prefix_rules[prefix] + ":" + id
    return concept_id


def __initalize_network(interactions: pd.DataFrame, selected_genes: List) -> NxGraph:
    interactions_graph = NxGraph()
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
    ungraphed_genes = set(selected_genes).difference(graphed_genes)
    for gene in ungraphed_genes:
        interactions_graph.add_node("<Placeholder>", id=gene, category=[])
    return interactions_graph
