"""Provides functionality to create a Dash web application for interacting with drug-gene data from DGIdb"""

import dash_bootstrap_components as dbc
import dash_cytoscape as cyto
from dash import Input, Output, State, ctx, dash, dcc, html

from dgipy import dgidb
from dgipy import network_graph as ng


def generate_app() -> dash.Dash:
    """Initialize a Dash application object with a layout designed for visualizing: drug-gene interactions, options for user interactivity, and other visual elements.

    :return: a python dash app that can be run with run_server()
    """
    genes = [
        {"label": gene["name"], "value": gene["name"]} for gene in dgidb.get_gene_list()
    ]
    drugs = [
        {"label": drug["name"], "value": drug["name"]} for drug in dgidb.get_drug_list()
    ]

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    __set_app_layout(app)
    __update_cytoscape(app)
    __update_terms_dropdown(app, genes, drugs)
    __update_selected_node(app)
    __update_selected_node_text(app)
    __update_neighbors_dropdown(app)
    #__update_edge_info(app)

    return app


def __set_app_layout(app: dash.Dash) -> None:
    cytoscape_figure = cyto.Cytoscape(
        id="cytoscape-figure",
        layout={"name": "preset"},
        style={"width": "100%", "height": "800px"},
        stylesheet=[
            # Group selectors
            {
                "selector": "node",
                "style": {
                    "content": "data(label)"
                },
            },
            {
                "selector": "edge",
                "style": {
                    "width": 0.75
                }
            },
            {
                "selector": "[node_degree > 1][isGene]",
                "style": {
                    "background-color": "cyan",
                }
            },
            {
                "selector": "[node_degree <= 1][isGene]",
                "style": {
                    "background-color": "blue",
                }
            },
            {
                "selector": "[node_degree > 1][!isGene]",
                "style": {
                    "background-color": "orange",
                }
            },
            {
                "selector": "[node_degree <= 1][!isGene]",
                "style": {
                    "background-color": "red",
                }
            }
        ]
    )

    search_mode = dcc.RadioItems(
        id="search-mode",
        options=[
            {"label": "Gene Search", "value": "genes"},
            {"label": "Drug Search", "value": "drugs"},
        ],
        value="genes",
    )

    terms_dropdown = dcc.Dropdown(
        id="terms-dropdown", optionHeight=75, multi=True, value=[]
    )

    selected_node_text = dcc.Markdown(
        id="selected-node-text", children="No Node Selected"
    )

    neighbors_dropdown = dcc.Dropdown(id="neighbors-dropdown", multi=False)

    selected_edge_info = dcc.Markdown(
        id="selected-edge-info", children="No Edge Selected"
    )

    app.layout = html.Div(
        [
            # Variables
            dcc.Store(id="selected-node", data=""),
            dcc.Store(id="graph"),
            # Layout
            dbc.Row(
                [
                    dbc.Col(
                        dbc.Card(cytoscape_figure, body=True, style={"margin": "10px"}),
                        width=8,
                    ),
                    dbc.Col(
                        [
                            dbc.Card(
                                [
                                    dbc.CardHeader("Search Mode"),
                                    dbc.CardBody(search_mode),
                                ],
                                style={"margin": "10px"},
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader("Terms Dropdown"),
                                    dbc.CardBody(terms_dropdown),
                                ],
                                style={"margin": "10px"},
                            ),
                            dbc.Card(
                                [
                                    dbc.CardHeader("Neighbors Dropdown"),
                                    dbc.CardBody(neighbors_dropdown),
                                ],
                                style={"margin": "10px"},
                            ),
                            dbc.Card(
                                dbc.CardBody(
                                    [
                                        html.H4("Selected Node/Edge:"),
                                        html.P(selected_node_text),
                                        html.H4("Selected Edge Info:"),
                                        html.P(selected_edge_info),
                                    ]
                                ),
                                style={"margin": "10px"},
                            ),
                        ],
                        width=4,
                    ),
                ]
            ),
        ]
    )


def __update_cytoscape(app: dash.Dash) -> None:
    @app.callback(
        Output("cytoscape-figure", "elements"),
        Input("terms-dropdown", "value"),
        State("search-mode", "value"),
    )
    def update(terms: list | None, search_mode: str) -> dict:
        if len(terms) != 0:
            interactions = dgidb.get_interactions(terms, search_mode)
            network_graph = ng.initalize_network(interactions, terms, search_mode)
            return ng.generate_cytoscape(network_graph)
        return {}


def __update_terms_dropdown(app: dash.Dash, genes: list, drugs: list) -> None:
    @app.callback(
        Output("terms-dropdown", "options"),
        Input("search-mode", "value"),
    )
    def update(search_mode: str) -> list:
        if search_mode == "genes":
            return genes
        if search_mode == "drugs":
            return drugs
        return None


def __update_selected_node(app: dash.Dash) -> None:
    @app.callback(
        Output("selected-node", "data"),
        [Input("cytoscape-figure", "tapNode"), Input("terms-dropdown", "value")],
    )
    def update(tapNode: dict | None, new_gene: list | None) -> str | dict:  # noqa: N803
        if ctx.triggered_id == "terms-dropdown":
            return ""
        if tapNode is not None:
            print(tapNode)
            return tapNode
        return dash.no_update


def __update_selected_node_text(app: dash.Dash) -> None:
    @app.callback(
        Output("selected-node-text", "children"), Input("selected-node", "data")
    )
    def update(selected_node: str | dict) -> str:
        if selected_node != "":
            return selected_node["data"]["id"]
        return "No Node Selected"


def __update_neighbors_dropdown(app: dash.Dash) -> None:
    @app.callback(
        [
            Output("neighbors-dropdown", "options"),
            Output("neighbors-dropdown", "value"),
        ],
        Input("selected-node", "data"),
    )
    def update(selected_node: str | dict) -> tuple[list, None]:
        if selected_node != "" and selected_node["data"]["node_degree"] != 1:
            neighbor_list = []
            for edge in selected_node["edgesData"]:
                neighbor_list.append(edge["source"])
            print(neighbor_list)
            return neighbor_list, None
        return [], None


def __update_edge_info(app: dash.Dash) -> None:
    @app.callback(
        Output("selected-edge-info", "children"),
        [Input("selected-node", "data"), Input("neighbors-dropdown", "value")],
        State("graph", "data"),
    )
    def update(
        selected_node: str | dict,
        selected_neighbor: str | None,
        graph: dict | None,
    ) -> str:
        if selected_node == "":
            return "No Edge Selected"
        if selected_node["curveNumber"] == 1:
            selected_data = __get_node_data_from_id(
                graph["links"], selected_node["text"]
            )
            return (
                "ID: "
                + str(selected_data["id"])
                + "\n\nApproval: "
                + str(selected_data["approval"])
                + "\n\nScore: "
                + str(selected_data["score"])
                + "\n\nAttributes: "
                + str(selected_data["attributes"])
                + "\n\nSource: "
                + str(selected_data["source"])
                + "\n\nPmid: "
                + str(selected_data["pmid"])
            )
        if selected_neighbor is not None:
            edge_node_id = None
            selected_node_is_gene = __get_node_data_from_id(
                graph["nodes"], selected_node["text"]
            )["isGene"]
            selected_neighbor_is_gene = __get_node_data_from_id(
                graph["nodes"], selected_neighbor
            )["isGene"]
            if selected_node_is_gene == selected_neighbor_is_gene:
                return dash.no_update
            if selected_node_is_gene:
                edge_node_id = selected_node["text"] + " - " + selected_neighbor
            elif selected_neighbor_is_gene:
                edge_node_id = selected_neighbor + " - " + selected_node["text"]
            selected_data = __get_node_data_from_id(graph["links"], edge_node_id)
            if selected_data is None:
                return dash.no_update
            return (
                "ID: "
                + str(selected_data["id"])
                + "\n\nApproval: "
                + str(selected_data["approval"])
                + "\n\nScore: "
                + str(selected_data["score"])
                + "\n\nAttributes: "
                + str(selected_data["attributes"])
                + "\n\nSource: "
                + str(selected_data["source"])
                + "\n\nPmid: "
                + str(selected_data["pmid"])
            )
        return "No Edge Selected"


def __get_node_data_from_id(nodes: list, node_id: str) -> dict | None:
    for node in nodes:
        if node["id"] == node_id:
            return node
    return None
