"""Provides functionality to create networkx graphs and pltoly figures for network visualization"""

import networkx as nx

LAYOUT_SEED = 7


def _initalize_network(interactions: dict, terms: list, search_mode: str) -> nx.Graph:
    interactions_graph = nx.Graph()
    graphed_terms = set()
    for row in zip(*interactions.values(), strict=True):
        row_dict = dict(zip(interactions.keys(), row, strict=True))
        if search_mode == "genes":
            graphed_terms.add(row_dict["gene_name"])
        if search_mode == "drugs":
            graphed_terms.add(row_dict["drug_name"])
        interactions_graph.add_node(
            row_dict["gene_name"],
            label=row_dict["gene_name"],
            type="gene",
        )
        interactions_graph.add_node(
            row_dict["drug_name"],
            label=row_dict["drug_name"],
            type="drug",
        )
        interactions_graph.add_edge(
            row_dict["gene_name"],
            row_dict["drug_name"],
            id=row_dict["gene_name"] + " - " + row_dict["drug_name"],
            approval=row_dict["drug_approved"],
            score=row_dict["interaction_score"],
            attributes=row_dict["interaction_attributes"],
            sourcedata=row_dict["interaction_sources"],
            pmid=row_dict["interaction_pmids"],
        )

    graphed_terms = set(terms).difference(graphed_terms)
    for term in graphed_terms:
        if search_mode == "genes":
            interactions_graph.add_node(term, label=term, type="gene")
        if search_mode == "drugs":
            interactions_graph.add_node(term, label=term, type="drug")

    return interactions_graph


def _add_node_attributes(interactions_graph: nx.Graph, search_mode: str) -> None:
    nx.set_node_attributes(
        interactions_graph, dict(interactions_graph.degree()), "node_degree"
    )
    for node in interactions_graph.nodes:
        node_type = interactions_graph.nodes[node]["type"]

        if (search_mode == "genes" and node_type == "drug") or (
            search_mode == "drugs" and node_type == "gene"
        ):
            neighbors = "Group: " + "-".join(list(interactions_graph.neighbors(node)))
            interactions_graph.nodes[node]["group"] = neighbors
        else:
            interactions_graph.nodes[node]["group"] = None


def create_network(interactions: dict, terms: list, search_mode: str) -> nx.Graph:
    """Create a networkx graph representing interactions between genes and drugs

    :param interactions: Dictionary containing drug-gene interaction data
    :param terms: List containing terms used to query interaction data
    :param search_mode: String indicating whether query was gene-focused or drug-focused
    :return: a networkx graph of drug-gene interactions
    """
    interactions_graph = _initalize_network(interactions, terms, search_mode)
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
    groups = set()
    for node in cytoscape_node_data:
        node_pos = pos[node["data"]["id"]]
        node.update({"position": {"x": node_pos[0], "y": node_pos[1]}})
        if "group" in node["data"]:
            group = node["data"].pop("group")
            groups.add(group)
            node["data"]["parent"] = group
    groups.remove(None)
    for group in groups:
        cytoscape_node_data.append(
            {"data": {"id": group, "type": "compound", "node_degree": 0}}
        )
    return cytoscape_node_data + cytoscape_edge_data
