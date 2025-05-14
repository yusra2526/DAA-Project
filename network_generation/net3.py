import json
import random
import networkx as nx
from collections import defaultdict

NUM_NODES = 100_000

# Edge type definitions
EDGE_TYPES = {
    "family": {
        "avg_degree": 12,
        "CP_range": (0.5, 0.7),
        "CI_range": (7.5, 10),
        "graph_type": "SBM"
    },
    "friend": {
        "avg_degree": 20,
        "CP_range": (0.3, 0.4),
        "CI_range": (5, 7.5),
        "graph_type": "scale_free"
    },
    "work": {
        "avg_degree": 25,
        "CP_range": (0.3, 0.5),
        "CI_range": (2.5, 5),
        "graph_type": "scale_free"
    },
    "acquaintance": {
        "avg_degree": 30,
        "CP_range": (0.05, 0.1),
        "CI_range": (1, 2.5),
        "graph_type": "erdos_renyi"
    }
}

# Node infection parameters
def get_node_params():
    return {
        "P_D_params": {"slope": 0.034 / (10 * 24), "intercept_t": 5 * 24},
        "P_R_params": {"slope": 1 / (25 * 24), "intercept_t": 5 * 24}
    }

# Edge attributes
def get_edge_params(edge_type):
    TP = round(random.uniform(0.01, 0.05), 4)  # Universal range
    CP = round(random.uniform(*EDGE_TYPES[edge_type]["CP_range"]), 3)
    CI = round(random.uniform(*EDGE_TYPES[edge_type]["CI_range"]), 2)
    return TP, CP, CI

def generate_family_graph():
    sizes = [random.randint(6, 18) for _ in range(NUM_NODES // 12)]
    probs = [[0.999 if i == j else 0.0001 for j in range(len(sizes))] for i in range(len(sizes))]
    G = nx.stochastic_block_model(sizes, probs)
    nx.set_edge_attributes(G, "family", "type")
    return G

def generate_scale_free_edges(G, edge_type, total_edges):
    while G.number_of_edges() < total_edges:
        u, v = random.sample(range(NUM_NODES), 2)
        if u != v and not G.has_edge(u, v):
            G.add_edge(u, v, type=edge_type)
    return G

def generate_erdos_renyi_edges(G, total_edges, edge_type):
    p = total_edges / (NUM_NODES * (NUM_NODES - 1) / 2)
    ER = nx.erdos_renyi_graph(NUM_NODES, p)
    for u, v in ER.edges():
        if not G.has_edge(u, v):
            G.add_edge(u, v, type=edge_type)
    return G

def assign_edge_attributes(G):
    for u, v, data in G.edges(data=True):
        edge_type = data["type"]
        TP, CP, CI = get_edge_params(edge_type)
        G[u][v].update({"TP": TP, "CP": CP, "CI": CI})
    return G

def assign_node_attributes(G):
    for node in G.nodes():
        params = get_node_params()
        G.nodes[node].update(params)
    return G

def generate_full_graph():
    print("Generating family graph...")
    G = generate_family_graph()

    print("Adding friend edges...")
    G = generate_scale_free_edges(G, "friend", NUM_NODES * EDGE_TYPES["friend"]["avg_degree"] // 2)

    print("Adding work edges...")
    G = generate_scale_free_edges(G, "work", NUM_NODES * EDGE_TYPES["work"]["avg_degree"] // 2)

    print("Adding acquaintance edges...")
    G = generate_erdos_renyi_edges(G, NUM_NODES * EDGE_TYPES["acquaintance"]["avg_degree"] // 2, "acquaintance")

    print("Assigning attributes...")
    G = assign_edge_attributes(G)
    G = assign_node_attributes(G)

    return G

def save_graph(G, filename="graph_data.json"):
    data = {
        "nodes": {n: G.nodes[n] for n in G.nodes()},
        "edges": [(u, v, G[u][v]) for u, v in G.edges()]
    } 
    with open(filename, "w") as f:
        json.dump(data, f, indent=2)

if __name__ == "__main__":
    G = generate_full_graph()
    print(f"Generated graph with {G.number_of_nodes()} nodes and {G.number_of_edges()} edges.")
    save_graph(G)
