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
    __update_selected_element(app)
    __update_selected_element_text(app)
    __update_neighbors_dropdown(app)
    __update_edge_info(app)

    return app


def __set_app_layout(app: dash.Dash) -> None:
    cytoscape_figure = cyto.Cytoscape(
        id="cytoscape-figure",
        layout={"name": "preset"},
        style={"width": "100%", "height": "800px"},
        stylesheet=[
            # Group Selectors
            {
                "selector": "node",
                "style": {"content": "data(label)"},
            },
            {"selector": "edge", "style": {"width": 0.75}},
            {
                "selector": "[node_degree > 1][isGene]",
                "style": {
                    "background-color": "cyan",
                },
            },
            {
                "selector": "[node_degree <= 1][isGene]",
                "style": {
                    "background-color": "blue",
                },
            },
            {
                "selector": "[node_degree > 1][!isGene]",
                "style": {
                    "background-color": "orange",
                },
            },
            {
                "selector": "[node_degree <= 1][!isGene]",
                "style": {
                    "background-color": "red",
                },
            },
        ],
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

    selected_element_text = dcc.Markdown(
        id="selected-element-text", children="No Element Selected"
    )

    neighbors_dropdown = dcc.Dropdown(id="neighbors-dropdown", multi=False)

    selected_edge_info = dcc.Markdown(
        id="selected-edge-info", children="No Edge Selected"
    )

    app.layout = html.Div(
        [
            # Variables
            dcc.Store(id="selected-element", data=""),
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
                                        html.P(selected_element_text),
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


def __update_selected_element(app: dash.Dash) -> None:
    @app.callback(
        Output("selected-element", "data"),
        [
            Input("cytoscape-figure", "tapNode"),
            Input("cytoscape-figure", "tapEdge"),
            Input("terms-dropdown", "value"),
        ],
    )
    def update(
        tap_node: dict | None, tap_edge: dict | None, terms_dropdown: list | None  # noqa: ARG001
    ) -> str | dict:
        if ctx.triggered_prop_ids:
            dash_trigger = next(iter(ctx.triggered_prop_ids.keys()))
            if dash_trigger == "terms-dropdown.value":
                return ""
            if dash_trigger == "cytoscape-figure.tapNode" and tap_node is not None:
                return tap_node
            if dash_trigger == "cytoscape-figure.tapEdge" and tap_edge is not None:
                return tap_edge
        return dash.no_update


def __update_selected_element_text(app: dash.Dash) -> None:
    @app.callback(
        Output("selected-element-text", "children"), Input("selected-element", "data")
    )
    def update(selected_element: str | dict) -> str:
        if selected_element != "":
            return selected_element["data"]["id"]
        return "No Node Selected"


def __update_neighbors_dropdown(app: dash.Dash) -> None:
    @app.callback(
        [
            Output("neighbors-dropdown", "options"),
            Output("neighbors-dropdown", "value"),
        ],
        Input("selected-element", "data"),
    )
    def update(selected_element: str | dict) -> tuple[list, None]:
        if (
            selected_element != ""
            and selected_element["group"] == "nodes"
            and selected_element["data"]["node_degree"] != 1
        ):
            neighbor_set = set()
            for edge in selected_element["edgesData"]:
                neighbor_set.add(edge["target"])
                neighbor_set.add(edge["source"])
                neighbor_set.remove(selected_element["data"]["id"])
            neighbor_list = list(neighbor_set)
            return neighbor_list, None
        return [], None


def __update_edge_info(app: dash.Dash) -> None:
    @app.callback(
        Output("selected-edge-info", "children"),
        [Input("selected-element", "data"), Input("neighbors-dropdown", "value")],
    )
    def update(selected_element: str | dict, selected_neighbor: str | None) -> str:
        if selected_element == "":
            return "No Edge Selected"

        edge_info = None
        if selected_element["group"] == "nodes" and selected_neighbor is not None:
            edge_name = None
            if selected_element["data"]["isGene"]:
                edge_name = selected_element["data"]["id"] + " - " + selected_neighbor
            else:
                edge_name = selected_neighbor + " - " + selected_element["data"]["id"]
            for edge in selected_element["edgesData"]:
                if edge["id"] == edge_name:
                    edge_info = edge
                    break
        if selected_element["group"] == "edges":
            edge_info = selected_element["data"]

        if (
            selected_element["group"] == "nodes" and selected_neighbor is not None
        ) or selected_element["group"] == "edges":
            return (
                "ID: "
                + str(edge_info["id"])
                + "\n\nApproval: "
                + str(edge_info["approval"])
                + "\n\nScore: "
                + str(edge_info["score"])
                + "\n\nAttributes: "
                + str(edge_info["attributes"])
                + "\n\nSource: "
                + str(edge_info["source"])
                + "\n\nPmid: "
                + str(edge_info["pmid"])
            )
        return "No Edge Selected"
