import pickle

from family_generation import generate_families
from friend_group_generation import generate_friend_groups
from community_generation import generate_work_communities
"""

All sizes are fixed for a 100k size population.
Variability can be introduced later if desired.

"""

"returns the inclusive node range allocated to the age group"
age_group_to_node_range:dict[str, tuple[int, int]] = {
    "baby" : (0,10_000-1),
    "kid":(10_000, 30_000 - 1),
    "young_adult":(30_000, 50_000 - 1),
    "adult":(50_000, 85_000 - 1),
    "old":(85_000, 100_000 - 1)
}

def get_age_group(node_id)->str|None:
    for age_group in ["baby", "kid", "young_adult", "adult", "old"]:
        node_range = age_group_to_node_range[age_group]
        if node_id >= node_range[0] and node_id <= node_range[1]:
            return age_group
    return None

profession_group_to_node_range: dict[str, tuple[int, int]] = {
    "A": (50_000, 59_711),
    "B": (59_712, 72_836),
    "C": (72_837, 84_999)
}

# 2. Function to get profession group from a node_id
def get_profession_group(node_id: int) -> str | None:

    """
    Returns the profession group string for a given node_id.
    Returns None if the node_id does not fall into any defined profession group range.
    """
    for profession_group, node_range in profession_group_to_node_range.items():
        if node_range[0] <= node_id <= node_range[1]:
            return profession_group
    return None


class Network:
    def __init__(self, nodes, families, friend_groups, communities):
        self.nodes:list[dict] = nodes
        self.families:list[list] = families
        self.friend_groups:list[list] = friend_groups
        self.communities:list[list] = communities

    def get_age_group(self, node_id) -> str | None:
        for age_group in ["baby", "kid", "young_adult", "adult", "old"]:
            node_range = age_group_to_node_range[age_group]
            if node_range[0] <= node_id <= node_range[1]:
                return age_group
        return None

    def get_profession_group(self, node_id: int) -> str | None:

        """
        Returns the profession group string for a given node_id.
        Returns None if the node_id does not fall into any defined profession group range.
        """
        for profession_group, node_range in profession_group_to_node_range.items():
            if node_range[0] <= node_id <= node_range[1]:
                return profession_group
        return None


def generate_network():

    # node IDs are in [0,100k)

    nodes = [{}]*100_000

    print("Generating families")
    families, family_index = generate_families(age_group_to_node_range)
    print("Generated families")

    for node,fam_index in family_index.items():
        nodes[node]["family_ids"] = fam_index


    print("Generating friend groups of kids")
    kids_friend_groups, kid_friend_group_index = generate_friend_groups(age_group_to_node_range["kid"])
    print("Generated friend groups of kids")

    for node_id, kfg_indexes in kid_friend_group_index.items():
        nodes[node_id]["friend_group_ids"] = kfg_indexes

    print("Generating friend groups of young_adults")
    young_adults_friend_groups, young_adults_friend_group_index = generate_friend_groups(age_group_to_node_range["young_adult"])
    print("Generating friend groups of young_adults")

    # merging friend groups lists into one
    friend_groups = kids_friend_groups + young_adults_friend_groups

    for node_id, yafg_indexes in young_adults_friend_group_index.items():
        # yafg_ids are re-indexed for the new merged list
        nodes[node_id]["friend_group_ids"] = [yafg_id + len(kids_friend_groups) for yafg_id in yafg_indexes]


    print("Generating profession A communities")
    profA_communitites, profA_comm_index = generate_work_communities(profession_group_to_node_range["A"], 15, 30)
    print("Generated profession A communities")

    for node_id, comm_index in profA_comm_index.items():
        nodes[node_id]["comm_id"] = comm_index

    print("Generating profession B communities")
    profB_communitites, profB_comm_index = generate_work_communities(profession_group_to_node_range["B"], 10, 20)
    print("Generated profession B communities")

    communities = profA_communitites + profB_communitites

    for node_id, comm_index in profB_comm_index.items():
        nodes[node_id]["comm_id"] = comm_index + len(profA_communitites)

    return Network(nodes, families, friend_groups, communities)

if __name__ == "__main__":
    network = generate_network()

    with open("network.bin", "wb") as file:
        pickle.dump(network,file)