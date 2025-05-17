import pickle

import networkx as nx
import csv

def save_edge_list_semicolon_csv(G: nx.Graph, filename: str):
    with open(filename, mode='w', newline='') as csvfile:
        writer = csv.writer(csvfile, delimiter=';')
        writer.writerow(['source', 'target'])
        for source, target in G.edges():
            if G[source][target]["type"] == "friend":
                writer.writerow([source, target])

# Example usage
if __name__ == "__main__":
    with open("rs_graph.gpickle", "rb") as file:
        G = pickle.load(file)
    save_edge_list_semicolon_csv(G, 'friend_edges_semicolon.csv')