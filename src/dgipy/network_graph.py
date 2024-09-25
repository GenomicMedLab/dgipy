"""Provides functionality to create networkx graphs and pltoly figures for network visualization"""

import networkx as nx
import pandas as pd

LAYOUT_SEED = 7


def initalize_network(
    interactions: pd.DataFrame, terms: list, search_mode: str
) -> nx.Graph:
    """Create a networkx graph representing interactions between genes and drugs

    :param interactions: DataFrame containing drug-gene interaction data
    :param terms: List containing terms used to query interaction data
    :param search_mode: String indicating whether query was gene-focused or drug-focused
    :return: a networkx graph of drug-gene interactions
    """
    interactions_graph = nx.Graph()
    graphed_terms = set()

    for index in range(len(interactions["gene_name"]) - 1):
        if search_mode == "genes":
            graphed_terms.add(interactions["gene_name"][index])
        if search_mode == "drugs":
            graphed_terms.add(interactions["drug_name"][index])
        interactions_graph.add_node(
            interactions["gene_name"][index],
            label=interactions["gene_name"][index],
            isGene=True,
        )
        interactions_graph.add_node(
            interactions["drug_name"][index],
            label=interactions["drug_name"][index],
            isGene=False,
        )
        interactions_graph.add_edge(
            interactions["gene_name"][index],
            interactions["drug_name"][index],
            id=interactions["gene_name"][index]
            + " - "
            + interactions["drug_name"][index],
            approval=interactions["drug_approved"][index],
            score=interactions["interaction_score"][index],
            attributes=interactions["interaction_attributes"][index],
            sourcedata=interactions["interaction_sources"][index],
            pmid=interactions["interaction_pmids"][index],
        )

    graphed_terms = set(terms).difference(graphed_terms)
    for term in graphed_terms:
        if search_mode == "genes":
            interactions_graph.add_node(term, label=term, isGene=True)
        if search_mode == "drugs":
            interactions_graph.add_node(term, label=term, isGene=False)

    nx.set_node_attributes(
        interactions_graph, dict(interactions_graph.degree()), "node_degree"
    )
    return interactions_graph


def _add_node_attributes(interactions_graph: nx.Graph, search_mode: str) -> None:
    for node in interactions_graph.nodes:
        is_gene = interactions_graph.nodes[node]["isGene"]
        degree = interactions_graph.degree[node]
        if search_mode == "genes":
            if is_gene:
                if degree > 1:
                    set_color = "cyan"
                    set_size = 10
                else:
                    set_color = "blue"
                    set_size = 10
            else:
                if degree > 1:
                    set_color = "orange"
                    set_size = 7
                else:
                    set_color = "red"
                    set_size = 7
        if search_mode == "drugs":
            if is_gene:
                if degree > 1:
                    set_color = "cyan"
                    set_size = 7
                else:
                    set_color = "blue"
                    set_size = 7
            else:
                if degree > 1:
                    set_color = "orange"
                    set_size = 10
                else:
                    set_color = "red"
                    set_size = 10
        interactions_graph.nodes[node]["node_color"] = set_color
        interactions_graph.nodes[node]["node_size"] = set_size


def create_network(
    interactions: pd.DataFrame, terms: list, search_mode: str
) -> nx.Graph:
    """Create a networkx graph representing interactions between genes and drugs

    :param interactions: DataFrame containing drug-gene interaction data
    :param terms: List containing terms used to query interaction data
    :param search_mode: String indicating whether query was gene-focused or drug-focused
    :return: a networkx graph of drug-gene interactions
    """
    interactions_graph = initalize_network(interactions, terms, search_mode)
    _add_node_attributes(interactions_graph, search_mode)
    return interactions_graph


def generate_cytoscape(graph: nx.Graph) -> dict:
    """Create a cytoscape graph representing interactions between genes and drugs

    :param graph: networkx graph to be formatted as a cytoscape graph
    :return: a cytoscape graph of drug-gene interactions
    """
    pos = nx.spring_layout(graph, seed=LAYOUT_SEED, scale=4000)
    cytoscape_data = nx.cytoscape_data(graph)["elements"]
    cytoscape_node_data = cytoscape_data["nodes"]
    cytoscape_edge_data = cytoscape_data["edges"]
    for node in range(len(cytoscape_node_data)):
        node_pos = pos[cytoscape_node_data[node]["data"]["id"]]
        node_pos = {
            "position": {"x": int(node_pos[0].item()), "y": int(node_pos[1].item())}
        }
        cytoscape_node_data[node].update(node_pos)
    return cytoscape_node_data + cytoscape_edge_data
