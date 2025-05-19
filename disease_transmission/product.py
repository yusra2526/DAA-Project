import pickle
from multiprocessing.connection import Listener

from network_generation_revised.network import Network
from layout.layout import draw_initial_graph
from visualization.NumpyImage import NumpyImage
from threading import Thread
import napari
from visualization.StatusWidget import StatusWidget


metrics = {
    "S": 100_000,
    "I": 0,
    "R": 0,
    "D": 0,
    "h" : 0
}





colors = {
    "S" : (0,255,0),
    "I" : (255,0,0),
    "D" : (0,0,0),
    "R" : (0,0,255)
}

# update image after 100 node color changes
UPDATE_BATCH_SIZE = 10

PANEL_UPDATE_BATCH_SIZE = 100

def handle_updates(update_callback):
    listener = Listener(address=('localhost', 6000), authkey=b'secret')
    while True:
        conn = listener.accept()
        while True:
            try:
                msg = conn.recv()  # Expecting (int, str)
                update_callback(msg)
            except EOFError:
                break
        conn.close()

def run(G:Network, node_positions:dict, family_positions:dict):

    img = NumpyImage(draw_initial_graph(node_positions, family_positions))

    del family_positions

    viewer = napari.view_image(img.get_numpy(), rgb=True)


    pending_updates = 0
    first_infected_received = False

    pending_panel_updates = 0

    def batch_update_image(node_update):

        """
        accumulates updates and delivers them to the actual displayed image in batches
        """

        # focus around the first infected node
        nonlocal first_infected_received
        if not first_infected_received:
            (node_id, status, absolute_hour) = node_update
            assert status == "I"
            first_infected_received = True
            node_update_image(node_update)
            (x,y) = node_positions[node_id][0]
            viewer.layers[0].refresh()
            viewer.camera.center = (y,x)
            viewer.camera.zoom = 4.0


        node_update_image(node_update)
        nonlocal pending_updates
        pending_updates += 1
        nonlocal pending_panel_updates
        pending_panel_updates += 1

        if pending_updates >= UPDATE_BATCH_SIZE:
            viewer.layers[0].refresh()
            pending_updates = 0

        if pending_panel_updates >= PANEL_UPDATE_BATCH_SIZE:
            status_widget.update_panel(metrics)
            pending_panel_updates = 0

    def node_update_image(node_update):

        node_id, status, abs_hour = node_update

        # this will be called first time for basically every node, just initialize statuses first for product man
        if G.nodes[node_id].get("status") is None:
            G.nodes[node_id]["status"] = "S"

        prev_status = G.nodes[node_id]["status"]
        G.nodes[node_id]["status"] = status

        # update metrics and panel
        metrics[prev_status] -= 1
        metrics[status] += 1
        metrics["h"] = abs_hour


        img.draw_rectangle(node_positions[node_id], fill=colors[status])


    Thread(target=handle_updates, args=(batch_update_image,),
                     daemon=True).start()

    status_widget = StatusWidget(metrics)
    viewer.window.add_dock_widget(status_widget, area='right', name='Status Panel')
    napari.run()



if __name__=="__main__":


    G = Network.load_from_bin("../network_generation_revised/network.bin")

    with open("../layout/family_positions.bin","rb") as fam_file, open("../layout/node_positions.bin","rb") as node_file:
        family_positions = pickle.load(fam_file)
        node_positions = pickle.load(node_file)

    run(G,node_positions, family_positions)