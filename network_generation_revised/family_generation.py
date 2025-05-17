
def generate_families(age_group_to_node_range):

    """
    generate families for 100k nodes, with age_groups pre-defined
    puts 1 baby
    2 kids
    2 young adults
    3/4 adults
    1/2 olds
    in each family
    family_size=10

    returns families, family_index
    family_index[i] gives family_id of node_id i
    families[i] gives the family with family_id of i
    family is a list of nodes that are in one family

    """
    NUM_NODES = 100_000
    FAMILY_SIZE = 10
    NUM_FAMILIES = NUM_NODES//FAMILY_SIZE

    # pointers to keep track of nodes that have already been made part of a family
    babies = 0
    kids = 0
    young_adults = 0
    adults =0
    olds = 0

    families = []

    # family_index[i] gives the family_index of the ith node
    family_index = {}

    for i in range(NUM_FAMILIES):

        family = []
        for _ in range(1):
            family.append(age_group_to_node_range["baby"][0] + babies)
            babies+=1
        for _ in range(2):
            family.append(age_group_to_node_range["kid"][0] + kids)
            kids += 1
        for _ in range(2):
            family.append(age_group_to_node_range["young_adult"][0] + young_adults)
            young_adults += 1
        for _ in range(4 if i%2==0 else 3):
            family.append(age_group_to_node_range["adult"][0] + adults)
            adults+=1
        for _ in range(1 if i%2==0 else 2):
            family.append(age_group_to_node_range["old"][0] + olds)
            olds += 1

        for node_id in family:
            family_index[node_id] = i

        families.append(family)

    return families, family_index



