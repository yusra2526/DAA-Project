import networkx
import networkx as nx
import pickle
from PIL import Image, ImageDraw
from cluster_compression import compress_network
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
        dict: Absolute positions in pixels {node: (x_px, y_px)}.
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

        # Flip y-axis for image coordinates (optional)
        y_px = image_height - y_px

        abs_positions[node] = (x_px, y_px)

    return abs_positions


def draw_graph_image(positions, image_size=(800, 600), node_color=(0, 120, 255),
                     background_color=(255, 255, 255), node_radius=5, shape="circle") -> Image.Image:
    """
    Draws a graph using absolute pixel positions and returns a PIL image.

    Parameters:
        positions (dict): Absolute positions {node: (x_px, y_px)}.
        image_size (tuple): Size of the output image (width, height).
        node_color (tuple): RGB color of the nodes (e.g., (0, 120, 255)).
        background_color (tuple): RGB background color of the image.
        node_radius (int): Radius of the nodes in pixels.

    Returns:
        PIL.Image: The resulting image with the graph drawn.
    """
    img = Image.new("RGB", image_size, background_color)
    draw = ImageDraw.Draw(img)

    for x, y in positions.values():
        left_up = (x - node_radius, y - node_radius)
        right_down = (x + node_radius, y + node_radius)
        if shape=="circle":
            draw.ellipse([left_up, right_down], fill=node_color)
        else:
            draw.rectangle((left_up, right_down), fill=node_color)
    return img



if __name__=="__main__":

    # 10k nodes and about 240k edges
    G = compress_network(Network.load_from_bin("../network_generation_revised/network.bin"))

    # k = 1/5 means the algo tries to realize a distance of 1/5*10k = 2k pixels between nodes
    # obviously, this may not actually be possible, so its a best-effort thing, and more iteration means
    # its more accurate to our description, 25 iterations take about 2 minutes.
    pos = networkx.spring_layout(G,iterations=75, k=1/5)


    abs_pos = convert_to_absolute_positions(pos, image_width=10000, image_height=10000)

    # we end up with a graph where each node is actually a family of 10.

    with open("family_positions.bin", "wb") as file:
         pickle.dump(abs_pos, file)