# generate_dataset.py

import random
import json
import networkx as nx

RELATION_TYPES = {
    "family": {"weight": 3, "color": "red"},
    "friend": {"weight": 2, "color": "blue"},
    "acquaintance": {"weight": 1, "color": "green"},
}

def generate_graph_data(num_nodes=100, num_families=10):
    nodes = [{"id": i} for i in range(num_nodes)]
    edges = []

    # Step 1: FAMILY CLUSTERS (Tight clusters using SBM)
    family_size = num_nodes // num_families
    sizes = [family_size] * num_families
    probs = [[0.9 if i == j else 0.01 for j in range(num_families)] for i in range(num_families)]  # dense inside, sparse between
    sbm = nx.stochastic_block_model(sizes, probs)

    for u, v in sbm.edges():
        edges.append({
            "source": u,
            "target": v,
            "type": "family",
            "weight": RELATION_TYPES["family"]["weight"],
            "color": RELATION_TYPES["family"]["color"]
        })

    # Step 2: FRIENDS (Scale-free network)
    sf = nx.barabasi_albert_graph(num_nodes, m=2)
    for u, v in sf.edges():
        if not any((e['source'] == v and e['target'] == u) or (e['source'] == u and e['target'] == v) for e in edges):
            edges.append({
                "source": u,
                "target": v,
                "type": "friend",
                "weight": RELATION_TYPES["friend"]["weight"],
                "color": RELATION_TYPES["friend"]["color"]
            })

    # Step 3: ACQUAINTANCES (Random undirected edges)
    possible_pairs = [(a, b) for a in range(num_nodes) for b in range(a + 1, num_nodes)]
    random.shuffle(possible_pairs)
    acquaintance_edges = 0
    max_acquaintances = num_nodes  # limit to num_nodes random acquaintance edges
    for a, b in possible_pairs:
        if acquaintance_edges >= max_acquaintances:
            break
        if not any((e['source'] == b and e['target'] == a) or (e['source'] == a and e['target'] == b) for e in edges):
            edges.append({
                "source": a,
                "target": b,
                "type": "acquaintance",
                "weight": RELATION_TYPES["acquaintance"]["weight"],
                "color": RELATION_TYPES["acquaintance"]["color"]
            })
            acquaintance_edges += 1

    return {"nodes": nodes, "edges": edges}

if __name__ == "__main__":
    data = generate_graph_data()
    with open("graph_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Graph data saved to graph_data.json")
