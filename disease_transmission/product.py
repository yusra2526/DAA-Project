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

# update image after this number of node color changes
"""
NOTE: this directly affects the simulation process running independently? Why?
because napari.refresh() is an intensive operation, and if the rate of running the update < rate of sending message, the simulation process starts blocking
as it sends messages, so if this variable is set to 1, the between-hour times can reach upto 120 seconds, at peak infection spread time.
alternative is to use a queue with more buffer capacity, but that would require starting simulation as a Process and sharing the queue
with it set to 10, it gives peak delay of 6 seconds, which is good.
for now, to keep a balance between responsiveness of program and performance, im tuning the update time according to infection rate
"""


def IMAGE_UPDATE_BATCH_SIZE():

    infection_size = metrics["I"]

    if 0 <= infection_size <= 100:
        return 10

    return 10


def handle_updates(node_update_callback, metric_update_callback):
    listener = Listener(address=('localhost', 6000), authkey=b'secret')
    while True:
        conn = listener.accept()
        while True:
            try:
                msg = conn.recv()

                # metric update for widget, will happen at minimum delay of MIN_DELAY defined in simulation, happens hourly/
                if msg[0]==-1:
                    metric_update_callback(msg[1])

                # node update, is handled in batches
                else:
                    node_update_callback(msg)
            except EOFError:
                break
        conn.close()

def run(node_positions:dict, family_positions:dict):

    img = NumpyImage(draw_initial_graph(node_positions, family_positions))

    del family_positions

    viewer = napari.view_image(img.get_numpy(), rgb=True)


    pending_updates = 0
    first_infected_received = False

    def update_image_in_batches(node_update):

        """
        accumulates updates and delivers them to the actual displayed image in batches
        """

        # focus around the first infected node
        nonlocal first_infected_received
        if not first_infected_received:
            (node_id, status) = node_update
            assert status == "I"
            first_infected_received = True
            node_update_image(node_update)
            (x,y) = node_positions[node_id][0]
            viewer.camera.zoom = 4.0
            viewer.camera.center = (y, x)
            viewer.layers[0].refresh()



        node_update_image(node_update)
        nonlocal pending_updates
        pending_updates += 1

        if pending_updates >= IMAGE_UPDATE_BATCH_SIZE():
            viewer.layers[0].refresh()
            pending_updates = 0


    def node_update_image(node_update):

        node_id, status = node_update
        img.draw_rectangle(node_positions[node_id], fill=colors[status])

    def metric_update(metrics):
        metrics = metrics
        status_widget.update_panel(metrics)

    Thread(target=handle_updates, args=(update_image_in_batches,metric_update),
                     daemon=True).start()

    status_widget = StatusWidget(metrics)
    viewer.window.add_dock_widget(status_widget, area='right', name='Status Panel')
    napari.run()



if __name__=="__main__":

    with open("../layout/family_positions.bin","rb") as fam_file, open("../layout/node_positions.bin","rb") as node_file:
        family_positions = pickle.load(fam_file)
        node_positions = pickle.load(node_file)

    run(node_positions, family_positions)