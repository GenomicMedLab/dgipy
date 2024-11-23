import pytest

from dgipy.dgidb import get_interactions
from dgipy.network_graph import create_network, generate_cytoscape


def test_create_network():
    interactions = get_interactions("BRAF")
    terms = ["BRAF"]
    search_mode = "genes"
    assert create_network(interactions, terms, search_mode)

def test_generate_cytoscape():
    interactions = get_interactions("BRAF")
    terms = ["BRAF"]
    search_mode = "genes"
    network = create_network(interactions, terms, search_mode)
    assert generate_cytoscape(network)
