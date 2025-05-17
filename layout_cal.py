import networkx as nx
import numpy as np
import json
import pickle

def calculate_layout_from_existing_graph(graph_path, image_size=10000):
    # Step 1: Load existing graph from gpickle
    with open(graph_path, 'rb') as f:
        G = pickle.load(f)

    # Step 2: Compute fast spectral layout
    positions = nx.spectral_layout(G)

    # Step 3: Normalize layout to fit image_size x image_size
    coords = np.array(list(positions.values()))
    min_x, min_y = coords.min(axis=0)
    max_x, max_y = coords.max(axis=0)

    scale = image_size - 1
    normalized = ((coords - [min_x, min_y]) / ([max_x - min_x, max_y - min_y]) * scale)

    # Step 4: Convert to pixel bounding boxes (2x2 squares)
    node_boxes = {}
    for node, (x, y) in zip(G.nodes(), normalized):
        x = int(round(x))
        y = int(round(y))
        node_boxes[node] = [x - 1, y - 1, x + 1, y + 1]

    return node_boxes

# Example usage:
layout = calculate_layout_from_existing_graph("graph.gpickle", image_size=10000)

# Save layout as JSON
with open("layout.json", "w") as f:
    json.dump(layout, f)

print("Layout saved to 'layout.json'")

