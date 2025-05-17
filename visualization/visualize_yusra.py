# visualize_dataset.py

import json
import networkx as nx
import plotly.graph_objects as go

def visualize_graph_interactively(file_path):
    with open(file_path, "r") as f:
        data = json.load(f)

    G = nx.Graph()

    for node in data["nodes"]:
        G.add_node(node["id"])

    for edge in data["edges"]:
        G.add_edge(
            edge["source"],
            edge["target"],
            type=edge["type"],
            weight=edge["weight"],
            color=edge["color"]
        )

    pos = nx.spring_layout(G, seed=42)

    node_x, node_y = [], []
    for node in G.nodes():
        x, y = pos[node]
        node_x.append(x)
        node_y.append(y)

    node_trace = go.Scatter(
        x=node_x, y=node_y,
        mode='markers',
        marker=dict(size=10, color='gray'),
        hoverinfo='none'
    )

    # Create edge traces by type
    edge_traces = {}
    for relation_type in ["family", "friend", "acquaintance"]:
        edge_traces[relation_type] = go.Scatter(
            x=[], y=[],
            mode='lines',
            line=dict(width=RELATION_WIDTHS[relation_type], color=RELATION_COLORS[relation_type]),
            hoverinfo='none',
            name=relation_type.capitalize(),
            visible=True
        )

    for u, v in G.edges():
        edge = G[u][v]
        rel = edge["type"]
        x0, y0 = pos[u]
        x1, y1 = pos[v]
        edge_traces[rel].x = list(edge_traces[rel].x) + [x0, x1, None]
        edge_traces[rel].y = list(edge_traces[rel].y) + [y0, y1, None]


    fig = go.Figure(data=[*edge_traces.values(), node_trace])

    # Create visibility toggles
    visibility_map = {
        "All": [True, True, True, True],
        "Family": [True, False, False, True],
        "Friend": [False, True, False, True],
        "Acquaintance": [False, False, True, True],
    }

    fig.update_layout(
        title='Interactive Social Network Graph',
        showlegend=False,
        hovermode='closest',
        updatemenus=[
            dict(
                type="buttons",
                direction="left",
                buttons=[
                    dict(label=label, method="update",
                         args=[{"visible": visibilities}])
                    for label, visibilities in visibility_map.items()
                ],
                x=0.1, y=1.15, xanchor="left", yanchor="bottom"
            )
        ],
        margin=dict(l=20, r=20, t=50, b=20),
        xaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
        yaxis=dict(showgrid=False, zeroline=False, showticklabels=False),
    )

    fig.show()

# Define colors and widths
RELATION_COLORS = {
    "family": "red",
    "friend": "blue",
    "acquaintance": "green"
}

RELATION_WIDTHS = {
    "family": 3,
    "friend": 2,
    "acquaintance": 1
}

if __name__ == "__main__":
    visualize_graph_interactively("../network_generation/graph_data.json")
