import networkx as nx
import plotly.graph_objects as go

PLOTLY_SEED = 7

def initalize_network(interactions,selected_genes):
    interactions_graph = nx.Graph()
    graphed_genes = set()
    for index in interactions.index:
        graphed_genes.add(interactions['gene'][index])
        interactions_graph.add_node(interactions['gene'][index],isGene=True)
        interactions_graph.add_node(interactions['drug'][index],isGene=False)
        interactions_graph.add_edge(
            interactions['gene'][index],interactions['drug'][index],
            id=interactions['gene'][index]+" - "+interactions['drug'][index],
            approval=interactions['approval'][index],
            score=interactions['score'][index],
            attributes=interactions['interaction_attributes'][index],
            source=interactions['source'][index],
            pmid=interactions['pmid'][index]
        )
    ungraphed_genes = set(selected_genes).difference(graphed_genes)
    for gene in ungraphed_genes:
        interactions_graph.add_node(gene,isGene=True)
    return interactions_graph

def add_node_attributes(interactions_graph):
    for node in interactions_graph.nodes:
        is_gene = interactions_graph.nodes[node]['isGene']
        if(is_gene):
            set_color = "cyan"
            set_size = 10
        else:
            degree = interactions_graph.degree[node]
            if(degree > 1):
                set_color = "orange"
                set_size = 7
            else: 
                set_color = "red"
                set_size = 7
        interactions_graph.nodes[node]['node_color'] = set_color
        interactions_graph.nodes[node]['node_size'] = set_size

def create_network(interactions,selected_genes):
    interactions_graph = initalize_network(interactions,selected_genes)
    add_node_attributes(interactions_graph)
    return interactions_graph

def generate_plotly(graph):
    layout = go.Layout(
        hovermode='closest',
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        showlegend=True
    )
    fig = go.Figure(layout=layout)
    
    if(graph is not None):
        pos = nx.spring_layout(graph, seed=PLOTLY_SEED)

        trace_nodes = create_trace_nodes(graph,pos)
        trace_edges = create_trace_edges(graph,pos)

        fig.add_trace(trace_edges[0])
        fig.add_trace(trace_edges[1])
        for trace_group in trace_nodes:
            fig.add_trace(trace_group)

    return fig

def create_trace_nodes(graph,pos):
    nodes_by_group = {
        'cyan': {'node_x': [], 'node_y': [], 'node_text': [], 'node_color': [], 'node_size': [], 'neighbors': [], 'legend_name': "genes"},
        'orange': {'node_x': [], 'node_y': [], 'node_text': [], 'node_color': [], 'node_size': [], 'neighbors': [], 'legend_name': "multi-degree drugs"},
        'red': {'node_x': [], 'node_y': [], 'node_text': [], 'node_color': [], 'node_size': [], 'neighbors': [], 'legend_name': "single-degree drugs"}
    }

    for node in graph.nodes():
        node_color = graph.nodes[node]['node_color']
        node_size = graph.nodes[node]['node_size']
        x, y = pos[node]
        nodes_by_group[node_color]['node_x'].append(x)
        nodes_by_group[node_color]['node_y'].append(y)
        nodes_by_group[node_color]['node_text'].append(str(node))
        nodes_by_group[node_color]['node_color'].append(node_color)
        nodes_by_group[node_color]['node_size'].append(node_size)
        nodes_by_group[node_color]['neighbors'].append(list(graph.neighbors(node)))

    trace_nodes = []
    for node_group,node in nodes_by_group.items():
        trace_group = go.Scatter(
            x=node['node_x'],
            y=node['node_y'],
            mode='markers',
            marker=dict(
                symbol='circle',
                size=node['node_size'],
                color=node['node_color']
            ),
            text=node['node_text'],
            name=node['legend_name'],
            customdata=node['neighbors'],
            hoverinfo='text',
            visible=True,
            showlegend=True
        )
        trace_nodes.append(trace_group)

    return trace_nodes

def create_trace_edges(graph,pos):
    edge_x = []
    edge_y = []

    i_edge_x = []
    i_edge_y = []
    i_edge_id = []

    for edge in graph.edges():
        x0, y0 = pos[edge[0]]
        x1, y1 = pos[edge[1]]
        edge_x.append(x0)
        edge_x.append(x1)
        edge_x.append(None)
        edge_y.append(y0)
        edge_y.append(y1)
        edge_y.append(None)

        i_edge_x.append((x0+x1)/2)
        i_edge_y.append((y0+y1)/2)
        i_edge_id.append(graph.edges[edge]['id'])

    trace_edges = go.Scatter(
        x=edge_x,
        y=edge_y,
        mode='lines',
        line=dict(width=0.5,color='gray'),
        hoverinfo='none',
        showlegend=False
    )

    i_trace_edges = go.Scatter(
        x=i_edge_x,
        y=i_edge_y, 
        mode='markers',
        marker_size=0.5,
        text=i_edge_id,
        hoverinfo='text',
        showlegend=False
    )

    return trace_edges,i_trace_edges

def generate_json(graph):
    return nx.node_link_data(graph)