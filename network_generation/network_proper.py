import pickle
import time
from random import random

import networkx as nx
import numpy as np

def generate_edge_params(edge_type, seed=None):
    """
    Return a dict of TP, CI, and CP for a single edge of given type.

    Parameters
    ----------
    edge_type : str
        One of 'family', 'friend', 'work', or 'acquaintance'.
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    dict
        {'TP': float, 'CI': float, 'CP': float}
    """
    rng = random.Random(seed)
    # Transmission probability
    tp = round(rng.uniform(0.3, 0.4), 2)

    # Closeness index (one decimal)
    if edge_type == 'family':
        ci = round(rng.uniform(7.5, 10.0), 1)
        cp = round(rng.uniform(0.5, 0.7), 2)
    elif edge_type == 'friend':
        ci = round(rng.uniform(5.0, 7.5), 1)
        cp = round(rng.uniform(0.3, 0.4), 2)
    elif edge_type == 'work':
        ci = round(rng.uniform(2.5, 5.0), 1)
        cp = round(rng.uniform(0.3, 0.5), 2)
    elif edge_type == 'acquaintance':
        ci = round(rng.uniform(1.0, 2.5), 1)
        cp = round(rng.uniform(0.05, 0.1), 2)
    else:
        raise ValueError(f"Unknown edge type: {edge_type!r}")

    return {'TP': tp, 'CI': ci, 'CP': cp}


def generate_family(num_nodes,
                    avg_fam_size,
                    standard_dev,
                    interfamily_prob,
                    intrafamily_prob,
                    seed=None):
    """
    Generate family edges using an SBM with family sizes drawn from a normal distribution.

    Parameters
    ----------
    num_nodes : int
        Total number of nodes in the graph.
    avg_fam_size : float
        Mean of the normal distribution for family size.
    standard_dev : float
        Standard deviation of the normal distribution for family size.
    interfamily_prob : float
        Probability of edge between nodes in different families.
    intrafamily_prob : float
        Probability of edge between nodes within the same family.
    seed : int or None
        Random seed for reproducibility.

    Returns
    -------
    Graph
        An undirected Graph with 'family' edges only.
    list of int
        The sampled family sizes.
    """
    # set seed for reproducibility
    rng = np.random.default_rng(seed)
    # sample family sizes and adjust to sum to num_nodes
    sizes = []
    remaining = num_nodes
    while remaining > 0:
        size = int(max(1, rng.normal(avg_fam_size, standard_dev)))
        if size > remaining:
            size = remaining
        sizes.append(size)
        remaining -= size
    # build probability matrix
    k = len(sizes)
    p = np.full((k, k), interfamily_prob)
    np.fill_diagonal(p, intrafamily_prob)
    print(f"[Family] Sampling {k} families")
    # generate SBM
    sbm = nx.stochastic_block_model(sizes, p.tolist(), seed=seed)
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    count = 0
    for u, v in sbm.edges():
        G.add_edge(u, v, type='family')
        count += 1
    print(f"[Family] Added {count} family edges.")
    return G


def generate_scale_free(num_nodes, avg_degree, seed=None, edge_type='friend'):
    """
    Generate scale-free edges (friend or work).
    """
    print(f"[{edge_type.capitalize()}] Generating scale-free  with avg_degree={avg_degree}, seed={seed}")

    new_edges_added = int(avg_degree / 2)
    sf = nx.barabasi_albert_graph(num_nodes, new_edges_added, seed=seed)
    G = nx.Graph()
    G.add_nodes_from(range(num_nodes))
    count = 0
    for u, v in sf.edges():
        G.add_edge(u, v, type=edge_type)
        count += 1
    print(f"[{edge_type.capitalize()}] Added {count} edges.")
    return G


def generate_acquaintances(n, avg_degree, seed=None):
    """
    Generate random acquaintance edges.
    """
    print(f"[Acquaintance] Generating random graph with avg_degree={avg_degree}, seed={seed}")
    p = avg_degree / (n - 1)
    er = nx.fast_gnp_random_graph(n, p, seed=seed)
    G = nx.Graph()
    G.add_nodes_from(range(n))
    count = 0
    for u, v in er.edges():
        G.add_edge(u, v, type='acquaintance')
        count += 1
    print(f"[Acquaintance] Added {count} edges.")
    return G


def generate_graph(num_nodes,
                   avg_fam_size,
                   family_standard_dev,
                   interfamily_prob,
                   intrafamily_prob,
                   avg_friend_degree,
                   avg_work_degree,
                   avg_acquaintance_degree,
                   seed):
    """
    High-level graph generation combining multiple relationship types.
    """
    print(f"[Graph] Starting generation for n={num_nodes}")
    G = nx.Graph()
    G.add_nodes_from([(i, {'type': 'S'}) for i in range(num_nodes)])
    clash_counter = 0

    # family
    print("[Graph] Generating family layer...")
    fam = generate_family(num_nodes, avg_fam_size=avg_fam_size, standard_dev=family_standard_dev, interfamily_prob=interfamily_prob, intrafamily_prob=intrafamily_prob, seed=seed)
    for u, v, d in fam.edges(data=True):
            if G.has_edge(u, v):
                clash_counter += 1
            else:
                G.add_edge(u, v, **d, **generate_edge_params("family", seed))
    print("[Graph] Family layer merged.")

    # friends

    print("[Graph] Generating friend layer...")
    fr = generate_scale_free(num_nodes, avg_degree=avg_friend_degree, edge_type="friend", seed=seed)
    for u, v, d in fr.edges(data=True):
            if G.has_edge(u, v):
                clash_counter += 1
            else:
                G.add_edge(u, v, **d,**generate_edge_params("friend", seed))
    print("[Graph] Friend layer merged.")

    # work
    print("[Graph] Generating work layer...")
    wk = generate_scale_free(num_nodes, avg_degree=avg_work_degree, edge_type="work", seed=seed)
    for u, v, d in wk.edges(data=True):
        if G.has_edge(u, v):
                clash_counter += 1
        else:
                G.add_edge(u, v, **d,**generate_edge_params("work", seed))
    print("[Graph] Work layer merged.")

    # acquaintances
    ac = generate_acquaintances(num_nodes,avg_degree=avg_acquaintance_degree, seed=seed)
    for u, v, d in ac.edges(data=True):
            if G.has_edge(u, v):
                clash_counter += 1
            else:
                G.add_edge(u, v, **d,**generate_edge_params("acquaintance", seed))
    print("[Graph] Acquaintance layer merged.")

    print(f"[Graph] Edge-add clashes: {clash_counter}")
    return G




# Example usage:
if __name__ == "__main__":

    num_nodes = 100_000

    a = time.time()


    # edge paramters will be initialized, node parameters i,e the probabilities will be calculated at runtime,
    # the only parameter the nodes will have otherwise is time of infection, also assigned during simulation.
    # node layout calculation is left.

    G = generate_graph(num_nodes,
                       avg_fam_size = 12,
                       family_standard_dev = 5,
                       interfamily_prob=0.0001,
                       intrafamily_prob = 0.9999,
                       avg_friend_degree = 20,
                       avg_work_degree = 25,
                       avg_acquaintance_degree = 30,
                       seed=None)

    print(time.time() - a)
    with open('rs_graph.gpickle', 'wb') as f:
        pickle.dump(G, f, pickle.HIGHEST_PROTOCOL)


