from dgidb import dgidb
from dgidb import network_graph as ng
from dash import dash, dcc, html, Input, Output, State, ctx
import dash_bootstrap_components as dbc

def generate_app():  
    genes = dgidb.get_gene_list()
    plot = ng.generate_plotly(None)
    app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

    set_app_layout(app,plot,genes)
    update_plot(app)
    update_selected_node(app)
    update_selected_node_display(app)
    update_neighbor_dropdown(app)
    update_edge_info(app)

    return app

def set_app_layout(app,plot,genes):
    graph_display = dcc.Graph(
        id='network-graph',
        figure=plot,
        style={'width': '100%', 'height': '800px'}
    )
    
    genes_dropdown_display = dcc.Dropdown(
        id='gene-dropdown',
        options=[{'label': gene, 'value': gene} for gene in genes],
        multi=True
    )

    selected_node_display = dcc.Markdown(
        id='selected-node-text',
        children="No Node Selected"
    )
    
    neighbors_dropdown_display = dcc.Dropdown(
        id='neighbor-dropdown',
        multi=False
    )

    edge_info_display = dcc.Markdown(
        id='edge-info-text',
        children="No Edge Selected"
    )
    
    app.layout = html.Div([
        # Variables
        dcc.Store(id='selected-node', data=""),
        dcc.Store(id='graph'),

        # Layout
        dbc.Row([
            dbc.Col(
                dbc.Card(
                    graph_display,
                    body=True,
                    style={'margin': '10px'}
                ),
                width=8
            ),
            dbc.Col([
                dbc.Card(
                    [
                        dbc.CardHeader("Genes Dropdown Display"),
                        dbc.CardBody(genes_dropdown_display),
                    ],
                    style={'margin': '10px'}
                ),
                dbc.Card(
                    [
                        dbc.CardHeader("Neighbors Dropdown Display"),
                        dbc.CardBody(neighbors_dropdown_display),
                    ],
                    style={'margin': '10px'}
                ),
                dbc.Card(
                    dbc.CardBody(
                        [
                            html.H4("Selected Node/Edge:"),
                            html.P(selected_node_display),
                            html.H4("Selected Edge Info:"),
                            html.P(edge_info_display)
                        ]
                    ),
                    style={'margin': '10px'}
                )],
                width=4
            )
        ])
    ])

def update_plot(app):
    @app.callback(
        [Output('graph', 'data'), Output('network-graph', 'figure')],
        Input('gene-dropdown', 'value')
    )
    def update(selected_genes):
        if(selected_genes is not None):
            gene_interactions = dgidb.get_interactions(selected_genes)
            updated_graph = ng.create_network(gene_interactions,selected_genes)
            updated_plot = ng.generate_plotly(updated_graph)
            return ng.generate_json(updated_graph), updated_plot
        return None, ng.generate_plotly(None)

def update_selected_node(app):
    @app.callback(
        Output('selected-node', 'data'),
        [Input('network-graph', 'clickData'),Input('gene-dropdown', 'value')]
    )
    def update(clickData,newGene):
        if ctx.triggered_id == "gene-dropdown":
            return ""
        if clickData is not None and 'points' in clickData:
            selected_node = clickData['points'][0]
            if 'text' not in selected_node:
                return dash.no_update
            return selected_node
        return dash.no_update

def update_selected_node_display(app):
    @app.callback(
        Output('selected-node-text', 'children'),
        Input('selected-node', 'data')
    )
    def update(selected_node):
        if selected_node != "":
            return selected_node['text']
        return "No Node Selected"

def update_neighbor_dropdown(app):
    @app.callback(
        [Output('neighbor-dropdown', 'options'),Output('neighbor-dropdown', 'value')],
        Input('selected-node', 'data')
    )
    def update(selected_node):   
        if(selected_node != "" and selected_node['curveNumber'] != 1):
            return selected_node['customdata'], None
        else:
            return [], None

def update_edge_info(app):
    @app.callback(
        Output('edge-info-text', 'children'),
        [Input('selected-node', 'data'), Input('neighbor-dropdown', 'value')],
        State('graph', 'data')
    )
    def update(selected_node,selected_neighbor,graph):
        if selected_node == "":
            return "No Edge Selected"
        if(selected_node['curveNumber'] == 1):
            selected_data = get_node_data_from_id(graph['links'], selected_node['text'])
            return "ID: " + str(selected_data['id']) + "\n\nApproval: " + str(selected_data['approval']) + "\n\nScore: " + str(selected_data['score']) + "\n\nAttributes: " + str(selected_data['attributes']) + "\n\nSource: " + str(selected_data['source']) + "\n\nPmid: " + str(selected_data['pmid'])
        if selected_neighbor is not None:
            edge_node_id = None
            selected_node_is_gene = get_node_data_from_id(graph['nodes'], selected_node['text'])['isGene']
            selected_neighbor_is_gene = get_node_data_from_id(graph['nodes'], selected_neighbor)['isGene']
            if(selected_node_is_gene == selected_neighbor_is_gene):
                return dash.no_update
            elif(selected_node_is_gene):
                edge_node_id = selected_node['text'] + " - " + selected_neighbor
            elif(selected_neighbor_is_gene):
                edge_node_id = selected_neighbor + " - " + selected_node['text']
            selected_data = get_node_data_from_id(graph['links'], edge_node_id)
            if selected_data is None:
                return dash.no_update
            return "ID: " + str(selected_data['id']) + "\n\nApproval: " + str(selected_data['approval']) + "\n\nScore: " + str(selected_data['score']) + "\n\nAttributes: " + str(selected_data['attributes']) + "\n\nSource: " + str(selected_data['source']) + "\n\nPmid: " + str(selected_data['pmid'])
        return "No Edge Selected"
    
def get_node_data_from_id(nodes, node_id):
    for node in nodes:
        if node['id'] == node_id:
            return node
    return None