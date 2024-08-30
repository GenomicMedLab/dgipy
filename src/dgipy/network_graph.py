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

    for index in interactions.index:
        if search_mode == "genes":
            graphed_terms.add(interactions["gene"][index])
        if search_mode == "drugs":
            graphed_terms.add(interactions["drug"][index])
        interactions_graph.add_node(
            interactions["gene"][index], label=interactions["gene"][index], isGene=True
        )
        interactions_graph.add_node(
            interactions["drug"][index], label=interactions["drug"][index], isGene=False
        )
        interactions_graph.add_edge(
            interactions["gene"][index],
            interactions["drug"][index],
            id=interactions["gene"][index] + " - " + interactions["drug"][index],
            approval=interactions["approval"][index],
            score=interactions["score"][index],
            attributes=interactions["interaction_attributes"][index],
            sourcedata=interactions["source"][index],
            pmid=interactions["pmid"][index],
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
