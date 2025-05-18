import networkx as nx
import numpy as np
import json
import pickle

# Load the graph from the .gpickle file using pickle
with open('graph.gpickle', 'rb') as f:
    G = pickle.load(f)

# Calculate layout using spring layout
pos = nx.spring_layout(G, k=1, iterations=50, seed=42)

# Convert layout to top-left origin system (0,0 to 1000,1000)
coords = {
    str(node): {
        'x': float(x * 1000),
        'y': float((1 - y) * 1000)
    }
    for node, (x, y) in pos.items()
}

# Save layout coordinates to JSON
with open('layout_coordinates.json', 'w') as f:
    json.dump(coords, f, indent=2)

# Print some stats
x_vals = [c['x'] for c in coords.values()]
y_vals = [c['y'] for c in coords.values()]

print(f"Generated layout coordinates for {len(coords)} nodes")
print(f"X range: {min(x_vals):.2f} to {max(x_vals):.2f}")
print(f"Y range: {min(y_vals):.2f} to {max(y_vals):.2f}")
print("Coordinates saved in 'layout_coordinates.json'")
