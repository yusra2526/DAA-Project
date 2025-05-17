import random
import time



def get_family_member(person_id):

    """
    Returns the family member of a person if they have one, otherwise None.
    Family members are consecutive numbers where one is even and the other is odd.
    This only works for the kid and young_adult age group i.e age_groups kid and young_adult
    kids are in range [10k, 30k-1]
    young_adults are in range [30k, 50k-1]

    """

    if person_id % 2 == 0:  # Even person
        family_candidate = person_id + 1
    else:  # Odd person
        family_candidate = person_id - 1

    return family_candidate



def generate_friend_groups(node_range, pref_strength=0.7, candidate_sample_size=100, max_group_size=5):
    """
    Main function to assign people to friend groups based on the guidelines.

    - node_range is the inclusive range of node_ids we're assigning into friend_groups
    - pref_strength is the probability that two people with same target num_friend groups end up in the same friend group

    Maximum Group Size: The size of each friend group must be at MOST 5 people.
    Membership Distribution: The people (nodes) should be distributed across a certain number of friend groups according to these percentages:
        10% of people should be in 1 friend group each.
        20% of people should be in 2 friend groups each.
        40% of people should be in 3 friend groups each.
        20% of people should be in 4 friend groups each.
        10% of people should be in 5 friend groups each.
    Family Constraint: Two people from the same family cannot be in the same friend group.
        A "family" is defined as two people represented by numbers x and y if they are consecutive (e.g., x and x+1 or x and x-1) AND one number is odd and the other is even.
    Like-Minded Preference (Soft Rule): People prefer to make friends with "same-minded" people.
        For example, a person targeted to be in 1 friend group would prefer to form groups with other people who are also targeted for 1 friend group.
        This is not a hard rule, and there should be some randomness in group formation, allowing for mixing.

    returns friend_groups, person_data

    person_data[i] gives the friend_group_id list of node with id i.
    friend_groups[i] gives friend group with id i.

    """

    DISTRIBUTION_TARGETS = {
        1: 0.10,  # 10% of people in 1 group
        2: 0.20,  # 20% of people in 2 groups
        3: 0.40,  # 40% of people in 3 groups
        4: 0.20,  # 20% of people in 4 groups
        5: 0.10,  # 10% of people in 5 groups
    }


    person_ids_initial = list(range(node_range[0], node_range[1]+1))
    random.shuffle(person_ids_initial)  # Shuffle for random assignment of target group counts

    person_data = {}
    # Structure: { person_id: {'target': int, 'current': int, 'groups': list_of_group_ids} }

    # Assign target number of groups to each person
    current_idx = 0
    for target_count, percentage in DISTRIBUTION_TARGETS.items():
        num_in_category = int(len(person_ids_initial) * percentage)
        for _ in range(num_in_category):
            if current_idx < len(person_ids_initial):
                person = person_ids_initial[current_idx]
                person_data[person] = {'target': target_count, 'current': 0, 'groups': []}
                current_idx += 1

    # Distribute any remaining people due to rounding (should be few or none)
    # Assign them to the most common target category (3 groups) or any other default.
    default_target_for_remainder = 3
    while current_idx < len(person_ids_initial):
        person = person_ids_initial[current_idx]
        person_data[person] = {'target': default_target_for_remainder, 'current': 0, 'groups': []}
        current_idx += 1

    friend_groups = []
    group_id_counter = 0

    # Main loop: continue as long as someone needs to be in more groups
    # Iteration guard to prevent potential infinite loops if constraints are impossible
    max_iterations = len(person_ids_initial) * sum(DISTRIBUTION_TARGETS.keys())  # Generous upper bound
    iterations_done = 0

    while any(p_data['current'] < p_data['target'] for p_data in person_data.values()):
        iterations_done += 1
        if iterations_done > max_iterations:
            print(f"Warning: Max iterations ({max_iterations}) reached. Some assignments might be incomplete.")
            break

        # Identify people who still need to be placed in more groups
        people_still_needing_groups = [
            p_id for p_id, data in person_data.items() if data['current'] < data['target']
        ]

        if not people_still_needing_groups:
            break  # All assignments are met

        random.shuffle(people_still_needing_groups)
        seed_person = people_still_needing_groups[0]

        # Start a new group with the seed person
        new_group = [seed_person]
        current_group_members_set = {seed_person}
        current_group_families_set = set()
        seed_family_member = get_family_member(seed_person)
        if seed_family_member is not None:
            current_group_families_set.add(seed_family_member)

        seed_target_category = person_data[seed_person]['target']

        # Potential candidates to add to this group (must need groups, not be the seed)
        potential_add_pool = [p for p in people_still_needing_groups if p != seed_person]

        # Sample from this pool to keep candidate checking performant
        actual_sample_size = min(len(potential_add_pool), candidate_sample_size)
        candidate_sample_for_group = random.sample(potential_add_pool, actual_sample_size)

        # Try to add more members to the current group
        for _ in range(max_group_size - 1):  # Max members to add = MAX_GROUP_SIZE - 1 (seed)
            if not candidate_sample_for_group:  # No more candidates from our sample
                break

            eligible_for_this_slot = []
            # Check each candidate in the sample
            for p_cand in candidate_sample_for_group:
                # Basic checks: already in group or family constraints
                if p_cand in current_group_members_set:
                    continue
                if p_cand in current_group_families_set:  # p_cand is family of someone in new_group
                    continue

                p_cand_family = get_family_member(p_cand)
                if p_cand_family is not None and p_cand_family in current_group_members_set:  # p_cand's family is in new_group
                    continue

                # If all checks pass, this person is eligible for this slot
                eligible_for_this_slot.append(p_cand)

            if not eligible_for_this_slot:
                break  # No valid candidates found for this slot from the current sample

            # Apply like-minded preference to choose from eligible candidates
            chosen_candidate = None

            like_minded_eligible = [p for p in eligible_for_this_slot if
                                    person_data[p]['target'] == seed_target_category]
            other_eligible = [p for p in eligible_for_this_slot if person_data[p]['target'] != seed_target_category]

            random.shuffle(like_minded_eligible)  # Randomness within preference
            random.shuffle(other_eligible)

            if random.random() < pref_strength:  # Try preferred pool first
                if like_minded_eligible:
                    chosen_candidate = like_minded_eligible[0]
                elif other_eligible:  # Fallback to other pool
                    chosen_candidate = other_eligible[0]
            else:  # Try other pool first
                if other_eligible:
                    chosen_candidate = other_eligible[0]
                elif like_minded_eligible:  # Fallback to preferred pool
                    chosen_candidate = like_minded_eligible[0]

            if chosen_candidate:
                new_group.append(chosen_candidate)
                current_group_members_set.add(chosen_candidate)
                chosen_candidate_family = get_family_member(chosen_candidate)
                if chosen_candidate_family is not None:
                    current_group_families_set.add(chosen_candidate_family)

                # Remove the chosen candidate from *this specific group's sample*
                # so they are not considered again for another slot in this same group.
                candidate_sample_for_group.remove(chosen_candidate)
            else:
                break  # No one could be chosen (e.g. both pools were empty after filtering)

        # Finalize the formed group
        if new_group:  # Should always have at least the seed
            friend_groups.append(new_group)
            current_group_id = group_id_counter
            group_id_counter += 1
            for member in new_group:
                person_data[member]['current'] += 1
                person_data[member]['groups'].append(current_group_id)

    cleaned_person_data = {}

    for person_id in person_data.keys():
        cleaned_person_data[person_id] = person_data[person_id]["groups"]

    return friend_groups, cleaned_person_data






# Example Usage (assuming you have `final_friend_groups` from the previous code):

if __name__ == "__main__":

    start_time = time.time()

    final_friend_groups, final_person_data = generate_friend_groups()

    end_time = time.time()
    print(f"\nGenerated {len(final_friend_groups)} friend groups in {end_time - start_time:.2f} seconds.")




