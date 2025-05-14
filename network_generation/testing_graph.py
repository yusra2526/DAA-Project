import pickle
from collections import defaultdict

import networkx


with open('rs_graph.gpickle', 'rb') as f:
    G:networkx.Graph = pickle.load(f)



# Initialize a dictionary to store counts per type per node
type_counts_per_node = defaultdict(lambda: defaultdict(int))
edge_counts = {

    'family' : 0, 'friend' : 0, 'work' : 0, 'acquaintance' : 0

}


# Count edge types per node
for u, v, data in G.edges(data=True):
    edge_type = data.get('type')
    if edge_type:
        edge_counts[edge_type] += 1
        type_counts_per_node[u][edge_type] += 1
        type_counts_per_node[v][edge_type] += 1  # undirected, so count for both ends

# Collect counts per type across all nodes
type_stats = defaultdict(list)

for node_counts in type_counts_per_node.values():
    for edge_type, count in node_counts.items():
        type_stats[edge_type].append(count)

# Compute average, max, and min for each type
results = {}
for edge_type, counts in type_stats.items():
    results[edge_type] = {
        'average': sum(counts) / len(counts),
        'max': max(counts),
        'min': min(counts)
    }

# Print results
for edge_type, stats in results.items():
    print(f"Edge type '{edge_type}':")
    print(f"Total edges : {edge_counts[edge_type]}")
    print(f"  Average per node: {stats['average']:.2f}")
    print(f"  Max per node: {stats['max']}")
    print(f"  Min per node: {stats['min']}")

