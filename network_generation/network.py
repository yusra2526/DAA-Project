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

        # TP is based on intuition: frequency of transmission attempts
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

    for node in range(num_nodes):
        others = [i for i in range(num_nodes) if i != node]

        # FAMILY: 2–10 members
        num_family = random.randint(2, min(10, num_nodes - 1))
        family = random.sample(others, num_family)
        for f in family:
            add_edge(node, f, "family")

        # FRIENDS: 0–25% of other nodes
        num_friends = random.randint(0, int(0.25 * num_nodes))
        possible_friends = [i for i in others if not (node, i) in edge_set and not (i, node) in edge_set]
        friends = random.sample(possible_friends, min(num_friends, len(possible_friends)))
        for f in friends:
            add_edge(node, f, "friend")

        # ACQUAINTANCES: 0–30% of other nodes
        num_acquaintances = random.randint(0, int(0.3 * num_nodes))
        possible_acquaintances = [i for i in others if not (node, i) in edge_set and not (i, node) in edge_set]
        acquaintances = random.sample(possible_acquaintances, min(num_acquaintances, len(possible_acquaintances)))
        for a in acquaintances:
            add_edge(node, a, "acquaintance")

    return {"nodes": nodes, "edges": edges}

if __name__ == "__main__":
    data = generate_graph_data()
    with open("graph_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Graph data saved to graph_data.json")
