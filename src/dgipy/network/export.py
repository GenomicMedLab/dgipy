"""Define methods for exporting to common knowledge graph frameworks."""

import networkx as nx


def to_pykeen(graph: nx.Graph) -> list[tuple[str, str, str]]:
    """Export to PyKEEN triple set. Typically, you'd save this output to a TSV.

    PyKEEN likes very straightforward triples. There's probably work we could do to
    better characterize the interaction, and also add attributes as additional triples.
    As it stands, this method is VERY basic.

    :param graph: graph constructed from DGIpy results.
    :return: list of triples (e.g. to save to TSV)
    """
    triples = []
    for gene_id, drug_id in graph.edges:
        gene = graph.nodes[gene_id]["name"]
        drug = graph.nodes[drug_id]["name"]
        triples.append((gene, "has_drug_target_interaction_with", drug))
        triples.append((drug, "has_drug_target_interaction_with", gene))

    return triples
