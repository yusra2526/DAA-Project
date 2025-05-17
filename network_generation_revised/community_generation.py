import random


def generate_work_communities(
        node_range: tuple[int, int],
        min_size: int,
        max_size: int
) -> tuple[list[list[int]], dict[int, int]]:
    """
    Divides node IDs within a given range into distinct communities.
    Each node ID belongs to at most one community.
    Communities adhere to min_size and max_size.

    Args:
        node_range (tuple[int, int]): Inclusive (start_id, end_id) of node IDs.
        min_size (int): Minimum size of a community.
        max_size (int): Maximum size of a community.

    Returns:
        tuple[list[list[int]], dict[int, int]]:
            - A list of communities (each community is a list of node IDs).
            - A dictionary mapping node_ids to their community_id (index in the communities list).
    """
    start_id, end_id = node_range
    if not (0 <= min_size):
        raise ValueError("min_size must be non-negative (typically >= 1).")
    if not (min_size <= max_size):
        raise ValueError("min_size cannot be greater than max_size.")
    if start_id > end_id:
        # Or raise ValueError("start_id in node_range cannot be greater than end_id.")
        return [], {}

    num_nodes_in_range = end_id - start_id + 1
    if num_nodes_in_range == 0 or num_nodes_in_range < min_size:
        return [], {}

    available_node_ids = list(range(start_id, end_id + 1))
    random.shuffle(available_node_ids)

    communities: list[list[int]] = []
    community_index: dict[int, int] = {}

    current_node_list_idx = 0  # Index for iterating through shuffled available_node_ids

    while current_node_list_idx < num_nodes_in_range:
        remaining_nodes_count = num_nodes_in_range - current_node_list_idx
        if remaining_nodes_count < min_size:
            break

        possible_max_for_this_community = min(max_size, remaining_nodes_count)
        community_size = random.randint(min_size, possible_max_for_this_community)

        nodes_left_after_this_community = remaining_nodes_count - community_size
        if 0 < nodes_left_after_this_community < min_size:
            potential_new_size = community_size + nodes_left_after_this_community
            if potential_new_size <= max_size:
                community_size = potential_new_size

        new_community_members: list[int] = []
        for _ in range(community_size):
            if current_node_list_idx < num_nodes_in_range:
                new_community_members.append(available_node_ids[current_node_list_idx])
                current_node_list_idx += 1
            else:
                break

        if min_size <= len(new_community_members) <= max_size:
            community_id = len(communities)
            sorted_community = sorted(new_community_members)  # Sort for consistent output/order
            communities.append(sorted_community)
            for node_id in sorted_community:  # or new_community_members if order doesn't matter for index
                community_index[node_id] = community_id
        # else: This chunk of nodes couldn't form a valid community (should be rare with current logic)

    return communities, community_index


if __name__=="__main__":

    comms,comm_indexes = generate_work_communities((0,7874), 15, 30)

    for node_id, comm_id in comm_indexes.items():
        print(node_id, comm_id)
