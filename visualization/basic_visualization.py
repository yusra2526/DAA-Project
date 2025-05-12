# network_spread_app_focused.py
import tkinter as tk
from PIL import Image, ImageDraw
import threading
import time
import random
import argparse
import math

from PannableImageViewer import PannableImageViewer

DEFAULT_NUM_NODES = 100_000
AVG_EDGES_PER_NODE = 2.5
INITIAL_INFECTED_COUNT = 1

NODE_RADIUS = 4
SUSCEPTIBLE_COLOR = (0, 200, 0, 255)
INFECTED_COLOR = (255, 0, 0, 255)
BACKGROUND_COLOR = (10, 10, 10)

LAYOUT_SIDE_ESTIMATE_FACTOR = 15  # Higher factor for more spread out nodes
IMAGE_PADDING = 50

g_nodes = []
g_first_infected_node_coords = None
g_first_infected_node_id = -1

NUM_NODES = 0
IMAGE_WIDTH = 0
IMAGE_HEIGHT = 0
LAYOUT_WIDTH = 0
LAYOUT_HEIGHT = 0


def initialize_and_create_network(num_nodes_to_generate):
    global NUM_NODES, IMAGE_WIDTH, IMAGE_HEIGHT, LAYOUT_WIDTH, LAYOUT_HEIGHT, g_nodes, g_first_infected_node_coords, g_first_infected_node_id
    NUM_NODES = num_nodes_to_generate

    avg_area_per_node = LAYOUT_SIDE_ESTIMATE_FACTOR ** 2
    total_layout_area = NUM_NODES * avg_area_per_node
    side = int(math.sqrt(total_layout_area))

    LAYOUT_WIDTH = max(side, 200)  # Min layout size
    LAYOUT_HEIGHT = max(side, 200)

    IMAGE_WIDTH = LAYOUT_WIDTH + 2 * IMAGE_PADDING
    IMAGE_HEIGHT = LAYOUT_HEIGHT + 2 * IMAGE_PADDING

    g_nodes = []
    print(f"SIM_THREAD: Creating network with {NUM_NODES:,} nodes...")

    for i in range(NUM_NODES):
        node = {
            'id': i,
            'x': random.randint(IMAGE_PADDING, IMAGE_PADDING + LAYOUT_WIDTH - 1),
            'y': random.randint(IMAGE_PADDING, IMAGE_PADDING + LAYOUT_HEIGHT - 1),
            'state': 'S', 'neighbors': set()
        }
        g_nodes.append(node)

    edges_created_count = 0
    for i in range(NUM_NODES):
        num_edges_to_attempt = 0
        base_edges = int(AVG_EDGES_PER_NODE)
        if random.random() < (AVG_EDGES_PER_NODE - base_edges):
            num_edges_to_attempt = base_edges + 1
        else:
            num_edges_to_attempt = base_edges
        if NUM_NODES < 5: num_edges_to_attempt = random.randint(0, NUM_NODES - 1 if NUM_NODES > 1 else 0)

        current_node_edges = 0;
        attempts = 0
        max_attempts_for_node = NUM_NODES // 10 if NUM_NODES > 20 else NUM_NODES
        while current_node_edges < num_edges_to_attempt and attempts < max_attempts_for_node:
            attempts += 1
            if NUM_NODES <= 1: break
            neighbor_id = random.randint(0, NUM_NODES - 1)
            if neighbor_id == i or neighbor_id in g_nodes[i]['neighbors']: continue
            g_nodes[i]['neighbors'].add(neighbor_id)
            g_nodes[neighbor_id]['neighbors'].add(i)
            edges_created_count += 1
            current_node_edges += 1

    actual_avg_edges = (edges_created_count * 2) / NUM_NODES if NUM_NODES > 0 else 0
    print(
        f"SIM_THREAD: Network logic. Nodes: {len(g_nodes)}, Edges: {edges_created_count}, Avg deg: {actual_avg_edges:.2f}")

    if NUM_NODES > 0:
        infected_idx = random.randint(0, NUM_NODES - 1)
        g_nodes[infected_idx]['state'] = 'I'
        g_first_infected_node_id = infected_idx
        g_first_infected_node_coords = (g_nodes[infected_idx]['x'], g_nodes[infected_idx]['y'])
        print(
            f"SIM_THREAD: Initial infected: ID {infected_idx} at ({g_first_infected_node_coords[0]},{g_first_infected_node_coords[1]})")
    else:
        g_first_infected_node_coords = (IMAGE_WIDTH // 2, IMAGE_HEIGHT // 2)


def render_network_pil_image():
    img = Image.new("RGBA", (IMAGE_WIDTH, IMAGE_HEIGHT), BACKGROUND_COLOR + (255,))
    draw = ImageDraw.Draw(img)
    for node in g_nodes:
        color = INFECTED_COLOR if node['state'] == 'I' else SUSCEPTIBLE_COLOR
        x0 = node['x'] - NODE_RADIUS;
        y0 = node['y'] - NODE_RADIUS
        x1 = node['x'] + NODE_RADIUS;
        y1 = node['y'] + NODE_RADIUS
        draw.ellipse([x0, y0, x1, y1], fill=color, outline=None)
    return img.convert("RGB")


def simulation_step():
    if not g_nodes: return False
    newly_infected = set()
    for node in g_nodes:
        if node['state'] == 'I':
            for neighbor_id in node['neighbors']:
                if g_nodes[neighbor_id]['state'] == 'S': newly_infected.add(neighbor_id)
    if not newly_infected: return False
    for inf_id in newly_infected: g_nodes[inf_id]['state'] = 'I'
    return True


def _apply_focus_to_viewer(viewer_ref, node_x, node_y, target_node_screen_size=80):
    """Internal function to apply pan and zoom. Assumes canvas is ready."""
    if not viewer_ref or not viewer_ref.master.winfo_exists():
        print("FOCUS_APPLY: Viewer or master window gone.")
        return

    # 1. Calculate desired zoom factor
    desired_node_diameter_on_image = NODE_RADIUS * 2
    if desired_node_diameter_on_image == 0:
        new_zoom_factor = viewer_ref.max_zoom  # Default to max zoom if node has no size
    else:
        new_zoom_factor = target_node_screen_size / desired_node_diameter_on_image

    viewer_ref.zoom_factor = max(viewer_ref.min_zoom, min(new_zoom_factor, viewer_ref.max_zoom))

    # 2. Calculate view coordinates to center the node
    # (cx, cy) is the center of the canvas in canvas coordinates
    canvas_width = viewer_ref.canvas.winfo_width()
    canvas_height = viewer_ref.canvas.winfo_height()

    # If canvas isn't ready, we can't reliably get dimensions.
    # The caller (schedule_focus_on_node) should handle retrying.
    if canvas_width <= 1 or canvas_height <= 1:
        print(
            f"FOCUS_APPLY: Canvas not ready for focusing (dims: {canvas_width}x{canvas_height}). Cannot apply focus now.")
        return False  # Indicate failure

    canvas_center_x = canvas_width / 2.0
    canvas_center_y = canvas_height / 2.0

    # We want the point (node_x, node_y) in original image coordinates
    # to appear at (canvas_center_x, canvas_center_y) on the canvas.
    # The top-left of the canvas (0,0) corresponds to (current_view_x, current_view_y) in image coords.
    # So, node_x = current_view_x + (canvas_center_x / zoom_factor)
    # current_view_x = node_x - (canvas_center_x / zoom_factor)
    viewer_ref.current_view_x = node_x - (canvas_center_x / viewer_ref.zoom_factor)
    viewer_ref.current_view_y = node_y - (canvas_center_y / viewer_ref.zoom_factor)

    # 3. Apply changes
    viewer_ref._clamp_view_coordinates()  # Crucial to prevent gray areas if possible
    viewer_ref._update_displayed_image()
    print(
        f"FOCUS_APPLY: Focused on ({node_x},{node_y}). Zoom: {viewer_ref.zoom_factor:.2f}. View: ({viewer_ref.current_view_x:.1f},{viewer_ref.current_view_y:.1f})")
    return True  # Indicate success


def schedule_focus_on_node(viewer_ref, node_x, node_y, target_node_screen_size=80, attempt=1):
    """Schedules the focus operation, retrying if canvas is not ready."""
    MAX_FOCUS_ATTEMPTS = 10
    RETRY_DELAY_MS = 100

    if not viewer_ref or not viewer_ref.master.winfo_exists():
        print("FOCUS_SCHEDULE: Viewer or master window gone, aborting focus.")
        return

    if attempt > MAX_FOCUS_ATTEMPTS:
        print(f"FOCUS_SCHEDULE: Max focus attempts ({MAX_FOCUS_ATTEMPTS}) reached. Giving up.")
        return

    # Check if canvas is ready. This is a proxy for viewer being ready.
    if viewer_ref.canvas.winfo_width() <= 1 or viewer_ref.canvas.winfo_height() <= 1:
        print(f"FOCUS_SCHEDULE: Canvas not ready (attempt {attempt}). Retrying in {RETRY_DELAY_MS}ms.")
        viewer_ref.master.after(
            RETRY_DELAY_MS,
            lambda: schedule_focus_on_node(viewer_ref, node_x, node_y, target_node_screen_size, attempt + 1)
        )
        return

    # If canvas seems ready, try to apply focus immediately (still via 'after' for safety)
    # This internal _apply_focus is what does the real work.
    print(f"FOCUS_SCHEDULE: Canvas seems ready (attempt {attempt}). Scheduling apply_focus.")
    viewer_ref.master.after(
        0,  # Try immediately
        lambda: _apply_focus_to_viewer(viewer_ref, node_x, node_y, target_node_screen_size)
    )


def network_worker_thread_func(viewer_ref, stop_event):
    print(f"SIM_THREAD ({NUM_NODES:,} Nodes - Focused Start): Started.")

    start_create_time = time.perf_counter()
    initialize_and_create_network(NUM_NODES)  # Use the global NUM_NODES set by main
    end_create_time = time.perf_counter()
    print(f"SIM_THREAD: Network creation took {end_create_time - start_create_time:.2f}s.")

    try:
        initial_pil_image = render_network_pil_image()
        if not stop_event.is_set():
            # First, tell the viewer to set the image. This does its own centering/fitting.
            viewer_ref.set_image(initial_pil_image)

            # AFTER set_image is processed, schedule the specific focus.
            # The set_image itself uses root.after(0, ...), so we give it a moment.
            if g_first_infected_node_coords and viewer_ref.master.winfo_exists():
                print("SIM_THREAD: Scheduling initial focus on first infected node...")
                # The schedule_focus_on_node will handle retries if canvas isn't ready
                schedule_focus_on_node(
                    viewer_ref,
                    g_first_infected_node_coords[0],
                    g_first_infected_node_coords[1],
                    target_node_screen_size=80  # Desired screen size of the node
                )
        else:
            print("SIM_THREAD: Stop event set before initial render.");
            return
    except Exception as e:
        print(f"SIM_THREAD: Error during initial render/focus: {e}");
        import traceback;
        traceback.print_exc();
        return

    time_step_count = 0;
    max_time_steps = 2000
    simulation_ended_naturally = False
    stop_event.wait(timeout=1.5)  # Initial pause after focus

    while not stop_event.is_set() and time_step_count < max_time_steps:
        cycle_start_time = time.perf_counter()
        try:
            infection_spread = simulation_step();
            time_step_count += 1
            if not infection_spread and time_step_count > 1:
                print("SIM_THREAD: No new infections.");
                simulation_ended_naturally = True;
                break

            updated_img = render_network_pil_image()
            if not stop_event.is_set():
                viewer_ref.update_image(updated_img)
            else:
                break

            elapsed = time.perf_counter() - cycle_start_time
            print(f"SIM_THREAD: Step {time_step_count}, Cycle took {elapsed:.3f}s.")
            stop_event.wait(timeout=max(0, 2.0 - elapsed))  # Aim for ~5s per step total
            if stop_event.is_set(): break
        except Exception as e:
            print(f"SIM_THREAD_ERROR: {e}");
            import traceback;
            traceback.print_exc();
            break

    if simulation_ended_naturally:
        print(f"SIM_THREAD: Completed naturally after {time_step_count} steps.")
    elif time_step_count >= max_time_steps:
        print(f"SIM_THREAD: Max steps ({max_time_steps}) reached.")
    else:
        print(f"SIM_THREAD: Exited due to stop after {time_step_count} steps.")
    print(f"SIM_THREAD ({NUM_NODES:,} Nodes): Finished.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Simulate infection spread, focused on start.")
    parser.add_argument("--nodes", type=int, default=DEFAULT_NUM_NODES, help=f"Num nodes (def: {DEFAULT_NUM_NODES:,})")
    args = parser.parse_args()

    initialize_and_create_network(args.nodes)  # Calculate global parameters

    print(f"MAIN_APP: Config for {NUM_NODES:,} nodes. Initial infected: 1.")
    print(f"MAIN_APP: Img: {IMAGE_WIDTH}x{IMAGE_HEIGHT}. Node Radius: {NODE_RADIUS}px.")

    root = tk.Tk()
    root.title(f"{NUM_NODES:,} Nodes Spread - Focused ({IMAGE_WIDTH}x{IMAGE_HEIGHT})")

    win_w = min(IMAGE_WIDTH + 50, 1000);
    win_h = min(IMAGE_HEIGHT + 50, 750)
    if IMAGE_WIDTH > 0 and IMAGE_HEIGHT > 0:
        win_w = min(IMAGE_WIDTH // 2 if IMAGE_WIDTH > 800 else IMAGE_WIDTH, win_w)
        win_h = min(IMAGE_HEIGHT // 2 if IMAGE_HEIGHT > 600 else IMAGE_HEIGHT, win_h)
    root.geometry(f"{max(600, win_w)}x{max(500, win_h)}")

    placeholder = Image.new("RGB", (100, 100), (50, 50, 50))
    viewer = PannableImageViewer(root, placeholder, canvas_width=800, canvas_height=600)

    info_lines = [f"Pan/Zoom. {NUM_NODES:,} nodes. Start: 1 infected (focused).",
                  f"Img: {IMAGE_WIDTH}x{IMAGE_HEIGHT}. Nodes: Green(S),Red(I). ~1s/step."]
    info_label = tk.Label(root, text="\n".join(info_lines), pady=5, justify=tk.LEFT)
    info_label.pack(side=tk.BOTTOM, fill=tk.X)

    stop_ev = threading.Event()
    sim_thread = threading.Thread(target=network_worker_thread_func, args=(viewer, stop_ev), daemon=True)
    sim_thread.start()


    def on_close():
        print("MAIN_APP: Closing...");
        stop_ev.set()
        if sim_thread.is_alive():
            print("MAIN_APP: Wait sim thread...");
            sim_thread.join(timeout=3.0)
            if sim_thread.is_alive():
                print("MAIN_APP_WARN: Sim thread timeout.")
            else:
                print("MAIN_APP: Sim thread finished.")
        else:
            print("MAIN_APP: Sim thread already done.")
        root.destroy()


    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

    if sim_thread.is_alive() and not stop_ev.is_set():
        stop_ev.set();
        sim_thread.join(timeout=1.0)
    print("MAIN_APP: Exited.")