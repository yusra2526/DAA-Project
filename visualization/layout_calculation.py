import pickle

import networkx as nx
from fa2_modified import ForceAtlas2
import time
from PIL import Image, ImageDraw
def run_forceatlas2_with_progress(
    G: nx.Graph,
    iterations: int = 1000,
    log_every: int = 100,
    initial_pos=None
) -> dict:
    """
    Run ForceAtlas2 layout with Barnes-Hut, returning raw node positions (x, y).
    Provides progress feedback every `log_every` iterations.

    Args:
        G: networkx graph.
        iterations: total FA2 iterations.
        log_every: iterations between progress logs.
        initial_pos: Optional dict {node: (x,y)} to start from.

    Returns:
        dict: {node: (x, y)} raw positions.
    """
    fa2 = ForceAtlas2(
        outboundAttractionDistribution=False,
        linLogMode=False,
        adjustSizes=False,
        edgeWeightInfluence=1.0,
        jitterTolerance=1.0,
        barnesHutOptimize=True,
        barnesHutTheta=1.2,
        scalingRatio=2.0,
        strongGravityMode=False,
        gravity=1.0,
        verbose=False
    )

    if initial_pos is None:
        # Use a fast spring layout as initialization
        initial_pos = nx.spring_layout(G, dim=2, seed=42, iterations=10)

    pos = initial_pos
    start_time = time.time()

    for i in range(iterations):
        pos = fa2.forceatlas2_networkx_layout(G, pos)

        if (i + 1) % log_every == 0 or i == iterations - 1:
            elapsed = time.time() - start_time
            print(f"[{i + 1}/{iterations}] iterations done, elapsed {elapsed:.1f}s")

    return pos


def normalize_positions(
    pos: dict,
    image_width: int,
    image_height: int,
    node_size: int
) -> dict:
    """
    Normalize raw (x,y) positions to fit within image dimensions,
    and calculate top-left and bottom-right corners for square nodes.

    Args:
        pos: dict {node: (x, y)} raw layout positions.
        image_width: canvas width in pixels.
        image_height: canvas height in pixels.
        node_size: node square size in pixels.

    Returns:
        dict: {node: ((top_x, top_y), (bottom_x, bottom_y))}
    """
    xs = [x for x, y in pos.values()]
    ys = [y for x, y in pos.values()]

    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)

    def normalize(val, min_val, max_val):
        if max_val == min_val:
            return 0.5  # avoid division by zero
        return (val - min_val) / (max_val - min_val)

    node_positions = {}

    for node, (x, y) in pos.items():
        norm_x = normalize(x, min_x, max_x)
        norm_y = normalize(y, min_y, max_y)

        # Ensure nodes stay fully inside image
        top_left_x = int(norm_x * (image_width - node_size))
        top_left_y = int(norm_y * (image_height - node_size))

        bottom_right_x = top_left_x + node_size
        bottom_right_y = top_left_y + node_size

        node_positions[node] = ((top_left_x, top_left_y), (bottom_right_x, bottom_right_y))

    return node_positions


def forceatlas2_layout_with_feedback(
    G: nx.Graph,
    node_size: int,
    image_width: int,
    image_height: int,
    iterations: int = 1000,
    log_every: int = 100
) -> dict:
    """
    Main function to run ForceAtlas2 layout with progress feedback,
    and return positions mapped to an image canvas as node squares.

    Args:
        G: networkx graph.
        node_size: pixel size for square nodes.
        image_width: image width in pixels.
        image_height: image height in pixels.
        iterations: number of ForceAtlas2 iterations.
        log_every: how often to print progress.

    Returns:
        dict: {node: ((top_x, top_y), (bottom_x, bottom_y))}
    """
    print("Starting ForceAtlas2 layout...")
    raw_positions = run_forceatlas2_with_progress(G, iterations, log_every)
    print("Normalizing positions to image dimensions...")
    final_positions = normalize_positions(raw_positions, image_width, image_height, node_size)
    print("Layout complete.")
    return final_positions

def draw_graph_image(
    node_positions: dict,
    image_width: int,
    image_height: int,
    node_color=(0, 255, 0),
    background_color=(0, 0, 0)
) -> Image.Image:
    """
    Generate a PIL Image of the graph given node square positions.

    Args:
        node_positions: dict {node: ((top_x, top_y), (bottom_x, bottom_y))}
        image_width: image width in pixels.
        image_height: image height in pixels.
        node_color: RGB tuple for node color. Default: green.
        background_color: RGB tuple for background. Default: black.

    Returns:
        PIL.Image.Image: the rendered graph image.
    """
    img = Image.new("RGB", (image_width, image_height), color=background_color)
    draw = ImageDraw.Draw(img)

    for node, ((x1, y1), (x2, y2)) in node_positions.items():
        draw.rectangle([x1, y1, x2, y2], fill=node_color)

    return img






if __name__ == "__main__":

    with open("../network_generation/rs_graph.gpickle", "rb") as file:
        G = pickle.load(file)

    for u, v, data in list(G.edges(data=True)):
        if data.get('type') != 'family':
            G.remove_edge(u, v)


    # Parameters
    NODE_SIZE = 20
    IMAGE_WIDTH = 10000
    IMAGE_HEIGHT = 10000
    ITERATIONS = 10
    LOG_EVERY = 1

    positions = forceatlas2_layout_with_feedback(
        G,
        node_size=NODE_SIZE,
        image_width=IMAGE_WIDTH,
        image_height=IMAGE_HEIGHT,
        iterations=ITERATIONS,
        log_every=LOG_EVERY,
    )

    draw_graph_image(positions, IMAGE_WIDTH, IMAGE_HEIGHT).show()
