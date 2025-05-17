import pickle
import time
import random

import networkx

# maximum number of people that a node can infect in an hour
MAX_CONTACTS_PER_HOUR = 1

hits = 0
misses = 0

def event_occurs(prob):
    return random.random() < prob

def ETP(TP, CI):
    return TP if CI==1 else TP + (1-TP)/(10*CI)

with open("../network_generation/rs_graph.gpickle","rb") as file:
    G:networkx.Graph = pickle.load(file)

initial_infected = random.randint(0,99_999)

infected = [initial_infected]
G.nodes[initial_infected]["type"] = "I"

def refresh_hourly_contacts():
    for node in G.nodes:
        G.nodes[node]["contacts"] = 0


refresh_hourly_contacts()
h = 0
while True:

    ch,cm = hits, misses
    a = time.time()

    num_infected = len(infected)

    for i in range(num_infected):

        infected_node = infected[i]

        for adj_node in G.neighbors(infected_node):

            if G.nodes[infected_node]["contacts"] >= MAX_CONTACTS_PER_HOUR:
                break

            edge = G[infected_node][adj_node]

            if G.nodes[adj_node]["type"] == "S" and event_occurs(edge["CP"]):

                G.nodes[infected_node]["contacts"] += 1
                G.nodes[adj_node]["contacts"] += 1


                if event_occurs(ETP(edge["TP"], edge["CI"])):
                    hits += 1
                    infected.append(adj_node)
                    G.nodes[adj_node]["type"] = "I"
                else:
                    misses += 1


    print("TRANSMIT METRICS", time.time() - a, h, len(infected))
    print("SANITY CHECKS", hits-ch, misses-cm)
    h+=1
    refresh_hourly_contacts()














