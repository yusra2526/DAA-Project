import networkx as nx
import numpy as np
import json
import random
import pickle

# Set random seed for reproducibility
np.random.seed(42)
random.seed(42)

# Parameters for the SBM
n_communities = 4
sizes = [2] * n_communities 
n_nodes = sum(sizes)

# Probability matrix
p_in = 0.3
p_out = 0.05
prob_matrix = np.full((n_communities, n_communities), p_out)
np.fill_diagonal(prob_matrix, p_in)

# Generate the graph
G = nx.stochastic_block_model(sizes, prob_matrix)

# Assign random coordinates (0,0) to (1000,1000)
coords = {
    str(node): {
        'x': random.uniform(0, 1000),
        'y': random.uniform(0, 1000)
    }
    for node in G.nodes()
}

# Save coordinates to JSON
with open('coordinates.json', 'w') as f:
    json.dump(coords, f, indent=2)

# Save graph manually using pickle (still named .gpickle for compatibility)
with open('graph.gpickle', 'wb') as f:
    pickle.dump(G, f)

print(f"Generated SBM graph with {n_nodes} nodes and saved as 'graph.gpickle'")
print(f"Node coordinates saved in 'coordinates.json'")
