"""Test `dgipy.network.construct`."""

import json
from pathlib import Path

from dgipy.network import construct


def test_construct(fixtures_dir: Path):
    results = json.load(
        (fixtures_dir / "construct_network_input_interactions.json").open()
    )
    graph = construct.construct_graph(results)
    assert len(graph.nodes) == 7
    assert len(graph.edges) == 6
    assert graph.nodes["hgnc:3443"]["long_name"] == "epiregulin"
    assert graph.nodes["ncit:C188574"]["approved"] is False
    assert graph.edges[("hgnc:3443", "iuphar.ligand:7836")]["attributes"][
        "Mechanism of Action"
    ] == ["Inhibition"]
