import os

import pandas as pd
from kgx.graph.nx_graph import NxGraph
from kgx.sink import JsonSink, TsvSink
from kgx.transformer import Transformer
from kgx.validator import Validator

from dgipy import dgidb

TARGET_DIR = os.path.join(os.path.abspath(os.path.dirname(__file__)), "target")

def get_kgx_network_graph(terms: list | str, search: str = "genes") -> NxGraph:
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


def __fix_conceptid_prefix(concept_id: str) -> str:
    # Consult https://github.com/biolink/biolink-model/blob/master/biolink-model.yaml
    # for a list of valid prefixes
    prefix_rules = {
        "CHEMBL": "CHEMBL.MECHANISM",
        "IUPHAR.LIGAND": "IUPHAR.FAMILY",
        "NCBIGENE": "NCBIGene"
    }
    concept_id = concept_id.upper()
    prefix = concept_id.split(":")[0]
    suffix = concept_id.split(":")[1]
    if prefix in prefix_rules:
        return prefix_rules[prefix] + ":" + suffix
    return concept_id


def generate_kgx_json(graph: NxGraph) -> None:
    filepath = os.path.join(TARGET_DIR, "graph.json")
    t = Transformer()
    s = JsonSink(t, filename = filepath)
    for n, data in graph.nodes(data=True):
        s.write_node(data)
    for u, v, k, data in graph.edges(data=True, keys=True):
        s.write_edge(data)
    s.finalize()

def generate_kgx_tsv(graph: NxGraph) -> None:
    t = Transformer()
    s = TsvSink(
        owner = t,
        filename = os.path.join(TARGET_DIR, "graph"),
        format = "tsv",
        node_properties = {"id", "name", "category"},
        edge_properties = {"subject", "predicate", "object", "relation"},
    )
    for n, data in graph.nodes(data=True):
        s.write_node(data)
    for u, v, k, data in graph.edges(data=True, keys=True):
        s.write_edge(data)
    s.finalize()

def __initalize_network(interactions: pd.DataFrame, terms: list, search: str) -> NxGraph:
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
        id_dict = dict(zip(gene_data["gene"], gene_data["concept_id"], strict=False))
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
        id_dict = dict(zip(drug_data["drug"], drug_data["concept_id"], strict=False))
        for drug in ungraphed_drugs:
            interactions_graph.add_node(id_dict[drug], id=drug, category=[])
    return interactions_graph
