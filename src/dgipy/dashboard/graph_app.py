"""Provides functionality to create a Dash web application for interacting with drug-gene data from DGIdb"""

import dash_bootstrap_components as dbc
import pandas as pd
from dash import Input, Output, State, ctx, dash, dcc, html

from dgipy import dgidb
from dgipy import network_graph as ng
from dgipy.data_utils import make_tabular


def generate_app() -> dash.Dash:
    """Initialize a Dash application object with a layout designed for visualizing: drug-gene interactions, options for user interactivity, and other visual elements.

    :return: a python dash app that can be run with run_server()
    """
    genes = [
        {"label": gene["gene_name"], "value": gene["gene_name"]}
        for gene in make_tabular(dgidb.get_all_genes())
    ]
    drugs = [
        {"label": drug["drug_name"], "value": drug["drug_name"]}
        for drug in make_tabular(dgidb.get_all_drugs())
    ]

    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    _set_app_layout(app)
    _update_plotly(app)
    _update_terms_dropdown(app, genes, drugs)
    _update_selected_node(app)
    _update_selected_node_text(app)
    _update_neighbors_dropdown(app)
    _update_edge_info(app)

    return app


def _set_app_layout(app: dash.Dash) -> None:
    plotly_figure = dcc.Graph(
        id="plotly-figure", style={"width": "100%", "height": "800px"}
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
                        dbc.Card(plotly_figure, body=True, style={"margin": "10px"}),
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


def _update_plotly(app: dash.Dash) -> None:
    @app.callback(
        [Output("graph", "data"), Output("plotly-figure", "figure")],
        Input("terms-dropdown", "value"),
        State("search-mode", "value"),
    )
    def update(
        terms: list | None, search_mode: str
    ) -> tuple[dict | None, ng.go.Figure]:
        if len(terms) != 0:
            interactions = pd.DataFrame(dgidb.get_interactions(terms, search_mode))
            network_graph = ng.create_network(interactions, terms, search_mode)
            plotly_figure = ng.generate_plotly(network_graph)
            return ng.generate_json(network_graph), plotly_figure
        return None, ng.generate_plotly(None)


def _update_terms_dropdown(app: dash.Dash, genes: list, drugs: list) -> None:
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


def _update_selected_node(app: dash.Dash) -> None:
    @app.callback(
        Output("selected-node", "data"),
        [Input("plotly-figure", "clickData"), Input("terms-dropdown", "value")],
    )
    def update(clickData: dict | None, new_gene: list | None) -> str | dict:  # noqa: N803, ARG001
        if ctx.triggered_id == "terms-dropdown":
            return ""
        if clickData is not None and "points" in clickData:
            selected_node = clickData["points"][0]
            if "text" not in selected_node:
                return dash.no_update
            return selected_node
        return dash.no_update


def _update_selected_node_text(app: dash.Dash) -> None:
    @app.callback(
        Output("selected-node-text", "children"), Input("selected-node", "data")
    )
    def update(selected_node: str | dict) -> str:
        if selected_node != "":
            return selected_node["text"]
        return "No Node Selected"


def _update_neighbors_dropdown(app: dash.Dash) -> None:
    @app.callback(
        [
            Output("neighbors-dropdown", "options"),
            Output("neighbors-dropdown", "value"),
        ],
        Input("selected-node", "data"),
    )
    def update(selected_node: str | dict) -> tuple[list, None]:
        if selected_node != "" and selected_node["curveNumber"] != 1:
            return selected_node["customdata"], None
        return [], None


def _update_edge_info(app: dash.Dash) -> None:
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
            selected_data = _get_node_data_from_id(
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
            selected_node_is_gene = _get_node_data_from_id(
                graph["nodes"], selected_node["text"]
            )["isGene"]
            selected_neighbor_is_gene = _get_node_data_from_id(
                graph["nodes"], selected_neighbor
            )["isGene"]
            if selected_node_is_gene == selected_neighbor_is_gene:
                return dash.no_update
            if selected_node_is_gene:
                edge_node_id = selected_node["text"] + " - " + selected_neighbor
            elif selected_neighbor_is_gene:
                edge_node_id = selected_neighbor + " - " + selected_node["text"]
            selected_data = _get_node_data_from_id(graph["links"], edge_node_id)
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


def _get_node_data_from_id(nodes: list, node_id: str) -> dict | None:
    for node in nodes:
        if node["id"] == node_id:
            return node
    return None
