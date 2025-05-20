import pickle
import random
import time

from network_generation_revised.network import Network
from multiprocessing.connection import Client

# 3.4%
DEATH_PROBABILITY = 0.034

# takes about 18.5 days to die
AVG_DEATH_TIME = 18.5*24
# standard deviation of 2 days
SD_DEATH_TIME = 2*24

# takes about 10 days to recover,includes  incubation time (according to doctor talha bin kashif), more importantly, 10 days to stop transmitting
AVG_RECOVERY_TIME = 10*24
# standard dev of 2 days
SD_RECOVERY_TIME = 2*24

# 25% chance two people in contact for an hour, one being infected, infects the other
BASE_TRANSMISSION_PROBABILITY = 0.5

# 5 to 24% probability that a normal node decides to be "alone" in a given hour.
BASE_ISOLATION_PROBABILITY_RANGE = (0.05, 0.24)

# the maximum isolation probability that an infected node can reach at the peak of its infection.
MAX_ISOLATION_PROBABILITY = 0.85

# min hourly delay
MIN_UPDATE_DELAY = 1


# probability that a node chooses to just be alone in an hour, used for infected nodes

def approximate_linear(x, p1, p2):

    """returns the y value corresponding to x, linear interpolation between p1 and p2"""

    (x0,y0) = p1
    (x1, y1) = p2

    assert x0 <= x <= x1

    return ((y1-y0)/(x1-x0))*(x-x0) + y0


metrics = {
    "S": 100_000,
    "I": 0,
    "R": 0,
    "D": 0,
    "h" : 0
}


def isolation_probabilty(G,node_id, absolute_hour):

    # 5 to 24%
    base_prob = random.uniform(*BASE_ISOLATION_PROBABILITY_RANGE)
    node = G.nodes[node_id]
    if node["status"] != "I":
        return base_prob

    # TODO: need to subtract incubation time, since during it, isolation prob won't be affected
    elif node["decision"]=="death":
        # people set to die will have their probability increase linearly to a maximum of 90% until they die
        return approximate_linear(absolute_hour, (node["infection_time"], base_prob), (node["decision_time"]+node["infection_time"], 0.9))
    else: # recovery
        # increases to midway of recovery, decreases back to normal till recover

        infect_time = node["infection_time"]
        recover_time = node["decision_time"] + infect_time

        mid_point = recover_time//2

        # maximum is MAX_TRANSMISSION_PROBABILITY
        if absolute_hour <= mid_point:
            return approximate_linear(absolute_hour, (infect_time, base_prob),(mid_point, MAX_ISOLATION_PROBABILITY))
        else:
            return approximate_linear(absolute_hour, (mid_point, MAX_ISOLATION_PROBABILITY), (recover_time, base_prob))



def sample_normal_distribution(mean: float, std_dev: float) -> int:
    """
    Generates a random number from a normal (Gaussian) distribution
    with the specified mean and standard deviation, and then rounds it
    to the nearest integer.

    Args:
        mean (float): The mean (average) of the normal distribution.
        std_dev (float): The standard deviation of the normal distribution.
                         Must be non-negative.

    Returns:
        int: A randomly generated integer based on the normal distribution.

    Raises:
        ValueError: If std_dev is negative.
    """
    if std_dev < 0:
        raise ValueError("Standard deviation (std_dev) cannot be negative.")

    # random.gauss(mu, sigma) generates a random float from a
    # Gaussian distribution with mean mu and standard deviation sigma.
    random_float = random.gauss(mean, std_dev)

    # Round the float to the nearest integer.
    # int(x + 0.5) for positive x, int(x - 0.5) for negative x is a common way for "round half up"
    # Alternatively, Python 3's round() rounds to the nearest even number for .5 cases.
    # For simplicity and common expectation, let's use a robust rounding method.
    if random_float >= 0:
        return int(random_float + 0.5)
    else:
        return int(random_float - 0.5)
    # Or, if Python 3's round-half-to-even is acceptable:
    # return round(random_float)

def evaluate_node_changes(G:Network,infected:list,h:int,conn):

    """implements death, recovery or persistence of node
       just changes status for now
       and removes from infected list
       also resets contact status
    """


    to_remove_indices = []
    for (i,node_id) in enumerate(infected):

        if h >= G.nodes[node_id]["infection_time"] + G.nodes[node_id]["decision_time"]:

            if G.nodes[node_id]["decision"] == "death":

                metrics[G.nodes[node_id]["status"]] -= 1
                G.nodes[node_id]["status"] = "D"
                metrics["D"] += 1

                conn.send((node_id,"D"))
            else:
                metrics[G.nodes[node_id]["status"]] -= 1
                G.nodes[node_id]["status"] = "R"
                metrics["R"] += 1

                conn.send((node_id, "R"))


            to_remove_indices.append(i)


    # the correct way to delete multiple elements from a list, so indices of earlier elements don't change
    for i in reversed(to_remove_indices):
        del infected[i]

    # refresh hourly states, {free, alone, }
    for node in G.nodes:
        node["contact_status"] = "free"


def event_occurs(prob):
    "takes probability of event, and returns true if it occurs with that probability"
    return random.random() < prob


def infect_node(G: Network, node_id, absolute_hour,conn):
    """
    marks the node as infected and writes all changes in the Network data structure accordingly.
    hour_time is the absolute hour the infection occurred
    Changes:
    - status -> I
    - assign a infection_decision, whether it's going to die or recover
    - assign a corresponding decision_time, how many hours to live/die depending on decision
    - changes color
    """

    G.nodes[node_id]["status"] = "I"

    decision = "death" if event_occurs(DEATH_PROBABILITY) else "recovery"
    G.nodes[node_id]["decision"] = decision
    G.nodes[node_id]["infection_time"] = absolute_hour
    if decision == "death":
        G.nodes[node_id]["decision_time"] = sample_normal_distribution(AVG_DEATH_TIME, SD_DEATH_TIME)
    else:
        G.nodes[node_id]["decision_time"] = sample_normal_distribution(AVG_RECOVERY_TIME, SD_RECOVERY_TIME)

    metrics["S"] -= 1
    metrics["I"] += 1

    conn.send((node_id,"I"))


def spread_infection_global(G:Network, infected:list[int], time_of_day:int, absolute_hour,conn):

    n = len(infected)
    # infected will have new elements appended to it, as we spread infection, to avoid iterating over them as well
    # we limit iterations to original length
    for i in range(n):
        node_id = infected[i]
        spread_infection_per_node(node_id, G, infected, time_of_day, absolute_hour=absolute_hour,conn=conn)


def get_contact(node_id, G:Network, absolute_hour,type, same_age:bool=False, max_attempts = 10):

    """

    :param node_id: the node_id to get a contact for.
    :param G:  graph
    :param type: type of contact to get
    :param same_age: if family contact, same-age or not.
    :return: (contact,total_candidates), if valid contact found in the max_attempts, None otherwise
    """


    node = G.nodes[node_id]
    if type=="family":
        family:list[int] = G.families[node["family_ids"]]
        if not same_age:
            candidates = family
        else:
            candidates = [fam_node_id for fam_node_id in family if G.get_age_group(fam_node_id)==G.get_age_group(node_id)]

    elif type=="stranger":
        candidates = None
    elif type=="friend":
         candidates = []
         for friend_group_id in node["friend_group_ids"]:
             candidates += G.friend_groups[friend_group_id]
    elif type=="work":
        candidates = G.communities[node["comm_id"]]

    else:
        raise TypeError("Invalid contact type")

    # is a possibility for toddlers, same-age family contact type, the candidate will be the node itself
    if candidates and len(candidates)==1:
        return None

    for _ in range(max_attempts):
        if candidates:
            # to deal with the possibility of getting the node itself as the candidate, can happen since the node itself is also in the friend groups
            while True:
                candidate = random.choice(candidates)
                if candidate != node_id:
                    break
            if G.nodes[candidate]["status"]=="S" and G.nodes[candidate]["contact_status"]=="free":

                # possibility that candidate decided to be alone:
                if event_occurs(isolation_probabilty(G, candidate, absolute_hour=absolute_hour)):
                    G.nodes[candidate]["contact_status"]="alone"
                    continue
                else:
                    return candidate, len(candidates)
        else:
            candidate = random.randrange(*G.age_group_to_node_range["adult"])
            if G.nodes[candidate]["status"]=="S" and G.nodes[candidate]["contact_status"]=="free":
                return candidate, 35_000 # chose between 35k adults

    return None

def establish_contact(G, node_id1, node_id2):
    G.nodes[node_id1]["contact_status"] = node_id2
    G.nodes[node_id2]["contact_status"] = node_id1


def infection_probability(total_candidates):
    """The idea is, the less people the person has to meet, the more intense the contact"""
    return BASE_TRANSMISSION_PROBABILITY + BASE_TRANSMISSION_PROBABILITY*(1/total_candidates)


def determine_contact_type(G:Network,node_id, time_of_day):
    """determines the contact_type dependeing on the classification of the node and the time of day
        returns (contact_Type, same_age) if its a family contact, (contact_type,) otherwise
    """

    if time_of_day <= 7 or time_of_day == 23:
        # same-age group family contacts
        return ("family", True)
    else:
        age_group = G.get_age_group(node_id)
        if age_group in ["baby", "old"]:
            return ("family", False)
        elif age_group == "kid":
            # 8 AM to 5 PM
            if 8 <= time_of_day <= 17:
                return ("friend",)

            else:
                return ("family", False)

        elif age_group == "young_adult":
            if 8 <= time_of_day <= 17:
                return ("friend",)
                pass
            else:
                # 75% cross-age group family contacts, 25% friend group
                if event_occurs(0.75):
                    return ("family", False)
                else:
                    return ("friend",)
        else:  # adults
            profession_group = G.get_profession_group(node_id)
            if profession_group == "C":  # work from home , stay at home parents
                if event_occurs(0.1):
                    return ("stranger",)
                else:
                    return ("family", False)
            elif profession_group == "B":
                if 8 <= time_of_day <= 17:

                    return ("work",)
                else:
                    if event_occurs(0.2):
                        return ("stranger",)
                    else:
                        return ("family", False)
            else:  # profession type A
                if 8 <= time_of_day <= 21:
                    if event_occurs(0.8):
                        return ("stranger",)
                    else:
                        return ("work",)
                else:
                    return ("family", False)



def spread_infection_per_node(node_id, G:Network, infected:list[int], time_of_day:int, absolute_hour,conn):

    if event_occurs(isolation_probabilty(G, node_id, absolute_hour)):
        G.nodes[node_id]["contact_status"] = "alone"
        return

    result = get_contact(node_id, G, absolute_hour, *determine_contact_type(G,node_id, time_of_day))
    if not result:
        return
    else:
        victim_id, total_candidates = result
        establish_contact(G, node_id, victim_id)
        if event_occurs(infection_probability(total_candidates)):
            infect_node(G, victim_id, absolute_hour,conn)
            infected.append(victim_id)




def run_simulation(G: Network,conn):

    # states for now are S(susceptible), I(infected), R(recovered), D(died)

    # everyone starts as susceptible
    for node in G.nodes:
        node["status"] = "S"

    # first infected node, should be an adult
    first_infected = random.randint(*(Network.age_group_to_node_range["adult"]))

    infect_node(G, first_infected, 0,conn=conn)

    h = 0

    infected = [first_infected]

    while True:

        start = time.time()

        # time starts from 5 PM
        time_of_day = (h + 17) % 24

        evaluate_node_changes(G, infected, h,conn=conn)

        print(h, time_of_day, len(infected))
        spread_infection_global(G, infected, time_of_day, h,conn=conn)

        h += 1

        end =  time.time()
        print("actual time taken", end-start)


        time.sleep(max(0.0, MIN_UPDATE_DELAY-(end-start)))


        metrics["h"] = h
        conn.send((-1, metrics))



if __name__ == "__main__":

    conn = Client(address=('localhost', 6000), authkey=b'secret')

    with open("../network_generation_revised/network.bin", "rb") as file:
        G = pickle.load(file)

    run_simulation(G,conn)