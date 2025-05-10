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

    # 1. Family edges from Watts-Strogatz model
    ws = nx.watts_strogatz_graph(num_nodes, k=4, p=0.4)
    for u, v in ws.edges():
        edges.append({
            "source": u,
            "target": v,
            "type": "family",
            "weight": RELATION_TYPES["family"]["weight"],
            "color": RELATION_TYPES["family"]["color"]
        })

    # 2. Acquaintance edges from Barabási–Albert (scale-free) model
    sf = nx.barabasi_albert_graph(num_nodes, m=1)
    for u, v in sf.edges():
        if not any((e['source'] == v and e['target'] == u) or (e['source'] == u and e['target'] == v) for e in edges):
            edges.append({
                "source": u,
                "target": v,
                "type": "acquaintance",
                "weight": RELATION_TYPES["acquaintance"]["weight"],
                "color": RELATION_TYPES["acquaintance"]["color"]
            })

    # 3. Friend edges - Random undirected edges
    possible_pairs = [(a, b) for a in range(num_nodes) for b in range(a + 1, num_nodes)]
    random.shuffle(possible_pairs)
    friend_edges = 0
    for a, b in possible_pairs:
        if friend_edges >= num_nodes:
            break
        if not any((e['source'] == b and e['target'] == a) or (e['source'] == a and e['target'] == b) for e in edges):
            edges.append({
                "source": a,
                "target": b,
                "type": "friend",
                "weight": RELATION_TYPES["friend"]["weight"],
                "color": RELATION_TYPES["friend"]["color"]
            })
            friend_edges += 1

    return {"nodes": nodes, "edges": edges}

if __name__ == "__main__":
    data = generate_graph_data()
    with open("graph_data.json", "w") as f:
        json.dump(data, f, indent=4)
    print("Graph data saved to graph_data.json")
