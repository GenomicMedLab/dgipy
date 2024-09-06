"""Construct a NetworkX graph from DGIpy query results."""

import networkx as nx

from dgipy.data_utils import make_tabular


def _get_gene_nodes(result_table: list[dict]) -> list[tuple[str, dict]]:
    if result_table and "gene_concept_id" not in result_table[0]:
        return []

    nodes = []
    for row in result_table:
        node_attrs = {"type": "gene"}
        node_attrs.update(
            {
                k[5:]: v
                for k, v in row.items()
                if k.startswith("gene_") and not k.startswith("gene_concept_id")
            }
        )
        nodes.append((row["gene_concept_id"], node_attrs))
    return nodes


def _get_drug_nodes(result_table: list[dict]) -> list[tuple[str, dict]]:
    if result_table and "drug_concept_id" not in result_table[0]:
        return []

    nodes = []
    for row in result_table:
        node_attrs = {"type": "drug"}
        node_attrs.update(
            {
                k[5:]: v
                for k, v in row.items()
                if k.startswith("drug_") and not k.startswith("drug_concept_id")
            }
        )
        nodes.append((row["drug_concept_id"], node_attrs))
    return nodes


def _get_interaction_edges(result_table: list[dict]) -> list[tuple[str, str, dict]]:
    if result_table and (
        "drug_concept_id" not in result_table[0]
        or "gene_concept_id" not in result_table[0]
    ):
        return []

    edges = []
    for row in result_table:
        edge_attrs = {"type": "drug_gene_interaction"}
        edge_attrs.update(
            {k[12:]: v for k, v in row.items() if k.startswith("interaction_")}
        )
        edges.append((row["gene_concept_id"], row["drug_concept_id"], edge_attrs))
    return edges


def construct_graph(query_result: dict) -> nx.Graph:
    """Construct a NetworkX graph from a DGIpy query result (i.e., a columnar dict).

    >>> import dgipy
    ... from dgipy.network.construct import construct_graph
    >>> genes = dgipy.get_genes(["BRAF", "ABL1"])
    >>> graph = construct_graph(genes)

    :param query_result: result object directly from DGIpy output. In general, columns
        with names starting with ``"drug_"`` will be added as attributes of drug nodes,
        ``"gene_"`` (excluding ``"gene_category_"``) as attributes of gene nodes, and
        ``"interaction"`` as part of interaction edges.
    :return: nx.Graph, where any included drug, gene, and gene category instances are
        nodes, and edges are drawn between interacting genes and drugs, as well as
        genes and their corresponding gene categories.
    """
    graph = nx.Graph()
    result_table = make_tabular(query_result)

    graph.add_nodes_from(_get_gene_nodes(result_table))
    graph.add_nodes_from(_get_drug_nodes(result_table))
    graph.add_edges_from(_get_interaction_edges(result_table))

    return graph
