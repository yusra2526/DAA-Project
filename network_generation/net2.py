# generate_dataset.py

import random
import json
import networkx as nx

RELATION_TYPES = {
    "family": {"weight": 3, "color": "red"},
    "friend": {"weight": 2, "color": "blue"},
    "acquaintance": {"weight": 1, "color": "green"},
}

def generate_graph_data(num_nodes=100):
    nodes = [{"id": i} for i in range(num_nodes)]
    edges = []
    edge_set = set()

    def add_edge(u, v, edge_type):
        if u == v or (u, v) in edge_set or (v, u) in edge_set:
            return False
        edge_set.add((u, v))

        if edge_type == "family":
            TP = 0.07
            CP = round(random.uniform(0.5, 0.7), 3)
            CI = round(random.uniform(7.5, 10), 2)
        elif edge_type == "friend":
            TP = 0.05
            CP = round(random.uniform(0.3, 0.4), 3)
            CI = round(random.uniform(5, 7.5), 2)
        else:  # acquaintance
            TP = 0.02
            CP = round(random.uniform(0.05, 0.1), 3)
            CI = round(random.uniform(1, 2.5), 2)

        edges.append({
            "source": u,
            "target": v,
            "type": edge_type,
            "weight": RELATION_TYPES[edge_type]["weight"],
            "color": RELATION_TYPES[edge_type]["color"],
            "TP": TP,
            "CP": CP,
            "CI": CI
        })
        return True

    # === FAMILY CLUSTERS using SBM ===
    cluster_sizes = []
    remaining = num_nodes
    while remaining > 0:
        size = min(random.randint(2, 10), remaining)
        cluster_sizes.append(size)
        remaining -= size

    num_clusters = len(cluster_sizes)
    probs = [[0.9 if i == j else 0.01 for j in range(num_clusters)] for i in range(num_clusters)]
    sbm = nx.stochastic_block_model(cluster_sizes, probs, seed=random.randint(0, 1000))

    for u, v in sbm.edges():
        add_edge(u, v, "family")

    # === FRIEND NETWORK: add sparse edges between different clusters ===
    for node in range(num_nodes):
        num_friends = random.randint(0, int(0.25 * num_nodes))
        candidates = [i for i in range(num_nodes) if i != node]
        sampled_friends = random.sample(candidates, min(num_friends, len(candidates)))
        for f in sampled_friends:
            add_edge(node, f, "friend")

    # === ACQUAINTANCES: even sparser, looser connections ===
    for node in range(num_nodes):
        num_acquaintances = random.randint(0, int(0.3 * num_nodes))
        candidates = [i for i in range(num_nodes) if i != node]
        sampled_acquaintances = random.sample(candidates, min(num_acquaintances, len(candidates)))
        for a in sampled_acquaintances:
            add_edge(node, a, "acquaintance")

    return {"nodes": nodes, "edges": edges}

if __name__ == "__main__":
    data = generate_graph_data()
    with open("graph_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Graph data saved to graph_data.json")
