import tkinter as tk
from PIL import Image, ImageTk, ImageDraw
import random
import threading
import time

# Settings
width, height = 800, 800
total_dots = 100_000
batch_size = 1
dot_size = 5  # Size of the dots

# Setup window and canvas
root = tk.Tk()
root.title("Separate Thread Dots Drawing")
canvas = tk.Canvas(root, width=width, height=height)
canvas.pack()

# Create a blank image using Pillow (white background)
image = Image.new("RGB", (width, height), "white")

# Set up ImageDraw object
draw = ImageDraw.Draw(image)

# Color for black shapes
black = (0, 0, 0)

# This variable will hold the updated Tkinter image object
tk_image = ImageTk.PhotoImage(image)

# Flag to check if the drawing is done
drawing_done = False

# Function to update canvas (called from the main thread)
def update_canvas():
    global tk_image
    tk_image = ImageTk.PhotoImage(image)
    canvas.create_image((0, 0), image=tk_image, anchor=tk.NW)

# Drawing function (in a separate thread)
def draw_dots():
    global drawing_done
    for i in range(0, total_dots, batch_size):
        # Draw random dots
        for _ in range(batch_size):
            x = random.randint(0, width - dot_size)
            y = random.randint(0, height - dot_size)
            draw.rectangle([x, y, x + dot_size, y + dot_size], fill=black)

        # After every batch, notify the main thread to update the canvas
        root.after(0, update_canvas)  # Schedules update_canvas in the main thread


    drawing_done = True
    print("Drawing Done")

# Start the drawing thread
drawing_thread = threading.Thread(target=draw_dots)
drawing_thread.daemon = True  # This makes sure the thread exits when the main program exits
drawing_thread.start()

# Start the main event loop
root.mainloop()
