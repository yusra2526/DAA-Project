import napari
import numpy as np
import threading

# Image size and strip configuration
height = 10000
width = 10000
num_strips = 10
strip_width = width // num_strips

# Create 10 colorful vertical strips
colors = [
    [255, 0, 0],    # Red
    [255, 165, 0],  # Orange
    [255, 255, 0],  # Yellow
    [0, 128, 0],    # Green
    [0, 255, 255],  # Cyan
    [0, 0, 255],    # Blue
    [75, 0, 130],   # Indigo
    [238, 130, 238],# Violet
    [255, 192, 203],# Pink
    [128, 0, 128]   # Purple
]

# Initialize blank RGB image
image = np.zeros((height, width, 3), dtype=np.uint8)

# Fill strips
for i in range(num_strips):
    image[:, i*strip_width:(i+1)*strip_width, :] = colors[i]

# Start napari viewer
viewer = napari.view_image(image, rgb=True, name='Sliding Strips')

# Function to animate the image
def animate():
    while True:

        viewer.layers[0].refresh()  # Force redraw

# Run animation in a background thread to keep GUI responsive
threading.Thread(target=animate, daemon=True).start()

# Launch napari GUI
napari.run()
