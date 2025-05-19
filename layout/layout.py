import random

import networkx
import pickle
from PIL import Image, ImageDraw

from network_generation_revised.network import Network


def convert_to_absolute_positions(positions, image_width, image_height, margin=10):
    """
    Converts relative layout positions to absolute pixel positions on an image.

    Parameters:
        positions (dict): Node positions from a layout algorithm {node: (x, y)}.
        image_width (int): Width of the image in pixels.
        image_height (int): Height of the image in pixels.
        margin (int): Margin in pixels around the layout (default: 50px).

    Returns:
        dict: Absolute positions in pixels {node: (x_px, y_px)}, if each node was a 1by1 pixel
    """
    xs, ys = zip(*positions.values())
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    abs_positions = {}

    for node, (x, y) in positions.items():
        # Normalize x and y to range [0, 1]
        norm_x = (x - min_x) / (max_x - min_x) if max_x != min_x else 0.5
        norm_y = (y - min_y) / (max_y - min_y) if max_y != min_y else 0.5

        # Scale to image dimensions, leaving margin
        x_px = int(margin + norm_x * (image_width - 2 * margin))
        y_px = int(margin + norm_y * (image_height - 2 * margin))

        # Flip y-axis for image coordinates
        y_px = image_height - y_px

        abs_positions[node] = (x_px, y_px)

    return abs_positions


def draw_initial_graph(node_positions, family_positions, house_color=(235, 235, 52), node_color=(0,255,0), image_size=(5000,5000)) -> Image.Image:

    """
    Draws a graph using absolute pixel positions, returned by convert_to_absolute_positions and returns a PIL image.
    """

    img = Image.new("RGB", image_size, (255,255,255))

    draw = ImageDraw.Draw(img)

    for node_center in family_positions.values():
        draw_house(draw, node_center,color=house_color)

    for node_position in node_positions.values():
        draw.rectangle(node_position, fill=node_color)

    return img

def calculate_family_positions(image_width, image_height):
    from cluster_compression import compress_network
    # 10k nodes and about 240k edges
    G = compress_network(Network.load_from_bin("../network_generation_revised/network.bin"))

    # k = 1/5 means the algo tries to realize a distance of 1/5*10k = 2k pixels between nodes
    # obviously, this may not actually be possible, so its a best-effort thing, and more iteration means
    # its more accurate to our description, 25 iterations take about 2 minutes.
    pos = networkx.spring_layout(G, iterations=50,k=1/50)

    abs_pos = convert_to_absolute_positions(pos, image_width=image_width, image_height=image_height)

    # we end up with a graph where each node is actually a family of 10 nodes

    # the current positions works well for NODE_RADIUS = 10 pixels which ends up assigning a 21x21 square to each family

    # the output is dictionary of fam_id -> center of family_space (x,y)
    with open("family_positions.bin", "wb") as file:
        pickle.dump(abs_pos, file)

# resolve family into
def calculate_node_positions_for_family(center, family)->list[tuple[int, tuple[tuple[int,int],tuple[int,int]]]]:

    """
    given a family and center of family, assigns absolute positions to its members
    returns (node_id, position) tuples, where each position is a tuple of (top_left, bottom_right).

    These are pretty hardcoded values according to a 21 by 21 house centered at center
    """
    (x,y) = center
    positions = []
    available_positions = [
        ((x-1, y-9),(x+1, y-6)),

        ((x - 3, y - 4), (x - 1, y - 1)),
        ((x + 1, y - 4), (x + 3, y - 1)),

        ((x - 5, y + 1), (x - 3, y + 4)),
        ((x - 1, y + 1), (x + 1, y + 4)),
        ((x + 3, y + 1), (x + 5, y + 4)),

        ((x - 7, y + 6), (x - 5, y + 9)),
        ((x - 3, y + 6), (x - 1, y + 9)),
        ((x + 1, y + 6), (x + 3, y + 9)),
        ((x + 5, y + 6), (x + 7, y + 9)),
    ]

    random.shuffle(available_positions)

    for i in range(10):
        positions.append((family[i], available_positions[i]))

    return positions

def calculate_node_positions(G:Network, family_positions:dict[int, tuple[int,int]]):

    families = G.families
    node_positions = {}
    for (fam_id, center) in family_positions.items():
        family = families[fam_id]
        node_position_pairs = calculate_node_positions_for_family(center, family)
        node_positions.update(node_position_pairs)

    with open("node_positions.bin","wb") as file:
        pickle.dump(node_positions, file)

def draw_house(drawer:ImageDraw.ImageDraw, center:tuple[int,int], color):

        """# draws a house, centered at center, in a 21by21 square around the given center, this is HARDCODED for our setup"""
        (x,y) =center

        # house roof
        drawer.line(((x-6,y-10),(x+6,y-10)),fill=color)
        drawer.line(((x - 7, y - 9), (x + 7, y - 9)), fill=color)
        drawer.line(((x - 8, y - 8), (x + 8, y - 8)), fill=color)
        drawer.line(((x - 9, y - 7), (x + 9, y - 7)), fill=color)
        drawer.line(((x - 10, y - 6), (x + 10, y - 6)), fill=color)
        drawer.line(((x - 10, y - 5), (x + 10, y - 5)), fill=color)

        # house base
        drawer.rectangle(((x - 8, y - 4), (x + 8, y + 10)), fill=color)

if __name__=="__main__":

    # FAMILY POSITIONS
    calculate_family_positions(image_width=5000, image_height=5000)
    # NODE POSITIONS
    with open("family_positions.bin", "rb") as family_pos_file:
        family_positions = pickle.load(family_pos_file)
    calculate_node_positions(Network.load_from_bin("../network_generation_revised/network.bin"),family_positions)


    with open("family_positions.bin","rb") as family_pos_file, open("node_positions.bin","rb") as node_pos_file:
        family_pos = pickle.load(family_pos_file)
        node_pos = pickle.load(node_pos_file)

    draw_initial_graph(family_positions=family_pos, node_positions=node_pos).show()

