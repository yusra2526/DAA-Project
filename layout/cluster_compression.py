import pickle
import networkx
from collections import defaultdict
from network_generation_revised.network import Network
from itertools import combinations
def compress_network(G:Network):

    """

    Generates a networkx graph, where each family in G is considered one node, and edges represent a friend_edge from one
    family to another.
    The weight of the edge represents how many edges are going from one family to another.
    This is for visualization only.

    :param G:
    :return:
    """

    # dictionary where keys are distinct cross-family edges and values are strength, i.e how many edges exist between these 2 families
    cross_family_edge_count = defaultdict(int)

    for friend_group in G.friend_groups:
        cross_family_edges = get_cross_family_edges(G, friend_group)
        for edge in cross_family_edges:
            cross_family_edge_count[edge] += 1


    compressed_G = networkx.Graph()

    # node i is actually family i
    compressed_G.add_nodes_from(range(10_000))

    for (edge,weight) in cross_family_edge_count.items():

        compressed_G.add_edge(*edge, weight=weight)

    return compressed_G


def get_cross_family_edges(G:Network,friend_group:list[int]):
    """
    given a list of family ids for a friend group
    returns all undirected edges formed between different families
    """

    family_ids = [G.nodes[node_id]["family_ids"] for node_id in friend_group]

    pairs = []

    for pair in combinations(family_ids, 2):
        if pair[0]!=pair[1]:
            pairs.append(frozenset(pair))

    return pairs


if __name__=="__main__":

     # G = compress_network(Network.load_from_bin("../network_generation_revised/network.bin"))
     # a = time.time()
     #
     # pos = networkx.spring_layout(G,iterations=75, k=1/5)
     #
     # print(time.time()-a)
     #
     # abs_pos = convert_to_absolute_positions(pos, image_width=10000, image_height=10000)
     # with open("positions.bin", "wb") as file:
     #      pickle.dump(abs_pos, file)

     with open("family_positions.bin", "rb") as file:
        abs_pos = pickle.load(file)
     img = draw_graph_image(abs_pos, node_radius=10, image_size=(10000,10000),shape="square").show()


