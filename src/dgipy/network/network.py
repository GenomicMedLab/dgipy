"""make a network todo"""

import networkx as nx

from dgipy.data_utils import make_tabular


def _get_drug_node_inputs(query_result: dict) -> list[tuple[str, dict]]:
    # TODO attributes should be flattened
    if "drug_concept_id" not in query_result:
        return []

    nodes = []
    for row in make_tabular(query_result):
        nodes.append(  # noqa: PERF401
            (
                row["drug_concept_id"],
                {
                    k[5:]: v
                    for k, v in row.items()
                    if k.startswith("drug_") and k != "drug_concept_id"
                }.update({"type": "drug"}),
            )
        )
    return nodes


def _get_gene_node_inputs(query_result: dict) -> list[tuple[str, dict]]:
    # TODO attributes should be flattened
    if "gene_concept_id" not in query_result:
        return []

    nodes = []
    for row in make_tabular(query_result):
        nodes.append(  # noqa: PERF401
            (
                row["gene_concept_id"],
                {
                    k[5:]: v
                    for k, v in row.items()
                    if k.startswith("gene_") and k != "gene_concept_id"
                }.update({"type": "gene"}),
            )
        )
    return nodes


def _get_interaction_edges(query_result: dict) -> list[tuple[str, str, dict]]:
    # TODO attributes should be flattened
    if not ("drug_concept_id" in query_result and "gene_concept_id" in query_result):
        return []

    edges = []
    for row in make_tabular(query_result):
        edges.append(  # noqa: PERF401
            (
                row["gene_concept_id"],
                row["drug_concept_id"],
                {
                    k[5:]: v
                    for k, v in row.items()
                    if k.startswith("gene_") and k != "gene_concept_id"
                }.update({"type": "gene"}),
            )
        )
    return edges


def to_network(query_result: dict) -> nx.Graph:
    """Construct a networkx graph from a DGIpy query result.

    hash = concept id
    other stuff = add as attributes
    """
    graph = nx.Graph()

    graph.add_nodes_from(_get_gene_node_inputs(query_result))
    graph.add_nodes_from(_get_drug_node_inputs(query_result))
    graph.add_edges_from(_get_interaction_edges(query_result))
    # gene_cat_nodes, gene_cat_edges = _get_gene_category_entities(query_result)
    # graph.add_nodes_from(gene_cat_nodes)
    # graph.add_edges_from(gene_cat_edges)

    return graph
