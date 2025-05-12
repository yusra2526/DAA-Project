# pannable_image_viewer.py
import tkinter as tk
from PIL import Image, ImageTk, ImageDraw


class PannableImageViewer:
    """
    A Tkinter widget for displaying a PIL Image, allowing panning and zooming.
    It supports updating the displayed image dynamically.
    This viewer is not aware of how or by what mechanism its image update
    methods (set_image, update_image) are called.
    """

    def __init__(self, master, pil_image, canvas_width=600, canvas_height=400):
        self.master = master
        self.pil_image_original = None
        self.image_mode = None  # Will be 'RGB' or 'RGBA' generally
        self.img_width = 0
        self.img_height = 0

        self.canvas_width_init = canvas_width
        self.canvas_height_init = canvas_height
        self.canvas = tk.Canvas(master, width=self.canvas_width_init, height=self.canvas_height_init,
                                bg="gray", highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Panning state
        self._drag_start_x_canvas = 0
        self._drag_start_y_canvas = 0
        self._view_start_x_pan = 0.0
        self._view_start_y_pan = 0.0

        # Zooming state
        self.zoom_factor = 1.0
        self.zoom_step = 1.15
        self.min_zoom = 0.01  # Min zoom factor
        self.max_zoom = 50.0  # Max zoom factor
        self.resample_filter = Image.Resampling.NEAREST  # Good for pixel art, can be BILINEAR too

        # Viewport state
        self.current_view_x = 0.0  # Top-left x of viewport in original image coords
        self.current_view_y = 0.0  # Top-left y of viewport in original image coords

        self.tk_image = None  # Holds the PhotoImage to prevent garbage collection
        self.image_on_canvas = None  # ID of the image item on canvas

        self.z_key_pressed = False  # For 'z' + 'i'/'o' zoom

        # Bindings
        self.canvas.bind("<ButtonPress-1>", self.on_mouse_press)
        self.canvas.bind("<B1-Motion>", self.on_mouse_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_mouse_release)
        self.canvas.bind("<Configure>", self.on_canvas_resize)

        # Global key bindings on the master window for zoom
        self.master.bind_all("<KeyPress-z>", self.on_z_press, add="+")
        self.master.bind_all("<KeyRelease-z>", self.on_z_release, add="+")
        self.master.bind_all("<KeyPress-i>", self.on_i_press, add="+")
        self.master.bind_all("<KeyPress-o>", self.on_o_press, add="+")

        self.canvas.focus_set()  # Allow canvas to receive focus for potential direct key events

        # Initial image setup - called directly as __init__ is on the main thread
        if pil_image:  # Allow initializing with a None image if desired by caller
            self._execute_set_image(pil_image.copy())
        else:  # Handle None case: create a tiny placeholder
            placeholder = Image.new("RGB", (1, 1), "gray")
            self._execute_set_image(placeholder)

    def _preprocess_and_set_original_image(self, pil_img):
        """Internal: Converts image to RGB/RGBA and updates instance attributes."""
        if pil_img.mode == "RGBA":
            self.pil_image_original = pil_img
            self.image_mode = "RGBA"
        elif pil_img.mode == "P" and 'transparency' in pil_img.info:
            self.pil_image_original = pil_img.convert("RGBA")
            self.image_mode = "RGBA"
        else:  # Convert other modes (L, P without transparency, CMYK etc.) to RGB
            self.pil_image_original = pil_img.convert("RGB")
            self.image_mode = "RGB"

        self.img_width, self.img_height = self.pil_image_original.size

    def set_image(self, new_pil_image):
        """
        Sets a new image to be displayed, resetting the view (pan/zoom)
        and centering the new image. Thread-safe.
        Args:
            new_pil_image (PIL.Image.Image): The new image to display.
        """
        if not isinstance(new_pil_image, Image.Image):
            raise TypeError("new_pil_image must be a PIL.Image.Image instance.")
        # Schedule GUI operations on the main thread
        self.master.after(0, self._execute_set_image, new_pil_image.copy())

    def _execute_set_image(self, image_to_set):
        """Internal: Sets image and resets view. Must be called from main Tkinter thread."""
        self._preprocess_and_set_original_image(image_to_set)
        # update_idletasks ensures canvas dimensions are (more likely) known before centering
        self.master.update_idletasks()
        self._center_image_view()  # Resets zoom/pan and calls _update_displayed_image

    def update_image(self, new_pil_image):
        """
        Updates the displayed image with new content, retaining current pan/zoom.
        The new image MUST have the exact same dimensions as the current one. Thread-safe.
        Args:
            new_pil_image (PIL.Image.Image): The new image content.
        Raises:
            ValueError: If new image dimensions do not match the current image.
            TypeError: If new_pil_image is not a PIL Image.
        """
        if not isinstance(new_pil_image, Image.Image):
            raise TypeError("new_pil_image must be a PIL.Image.Image instance.")
        if self.pil_image_original is None:  # If not initialized, treat as set_image
            self.set_image(new_pil_image)
            return
        if new_pil_image.size != (self.img_width, self.img_height):
            raise ValueError(
                f"New image size {new_pil_image.size} must match current image size "
                f"{self.img_width}x{self.img_height} for 'update_image'."
            )

        self.master.after(0, self._execute_update_image, new_pil_image.copy())

    def _execute_update_image(self, image_to_update):
        """Internal: Updates image content, retains view. Main Tkinter thread only."""
        self._preprocess_and_set_original_image(image_to_update)
        self._clamp_view_coordinates()
        self._update_displayed_image()

    def _get_canvas_bg_color(self):
        """Internal: Gets canvas background color for image composition."""
        bg_color_str = self.canvas['bg']
        try:
            rgb_high_range = self.master.winfo_rgb(bg_color_str)
            rgb_255_range = tuple(c // 256 for c in rgb_high_range)
        except tk.TclError:  # Fallback if canvas is being destroyed
            rgb_255_range = (128, 128, 128)  # Gray

        if self.image_mode == "RGBA":  # Should match self.pil_image_original.mode
            return rgb_255_range + (255,)  # Add full opacity for RGBA background
        return rgb_255_range  # For "RGB" mode

    def _center_image_view(self):
        """Internal: Resets zoom, calculates view to center image, and updates display."""
        # Estimate initial zoom to fit roughly if image is very large
        c_w_est = self.canvas.winfo_width() if self.canvas.winfo_width() > 1 else self.canvas_width_init
        c_h_est = self.canvas.winfo_height() if self.canvas.winfo_height() > 1 else self.canvas_height_init

        if self.img_width > 0 and self.img_height > 0 and c_w_est > 1 and c_h_est > 1:
            self.zoom_factor = min(c_w_est / self.img_width, c_h_est / self.img_height, 1.0)
            self.zoom_factor = max(self.zoom_factor, self.min_zoom)
        else:
            self.zoom_factor = 1.0

        c_w = self.canvas.winfo_width()
        c_h = self.canvas.winfo_height()

        if c_w <= 1 or c_h <= 1:  # Canvas not sized yet
            c_w = max(c_w, self.canvas_width_init)
            c_h = max(c_h, self.canvas_height_init)
            if c_w <= 1 or c_h <= 1:  # Still not sized (e.g. window not mapped)
                self.master.after(50, self._center_image_view);
                return

        self.current_view_x = (self.img_width - (c_w / self.zoom_factor)) / 2.0
        self.current_view_y = (self.img_height - (c_h / self.zoom_factor)) / 2.0

        self._clamp_view_coordinates();
        self._update_displayed_image()

    def _clamp_view_coordinates(self):
        """Internal: Ensures current_view_x/y are valid for current zoom and image/canvas."""
        c_w = self.canvas.winfo_width();
        c_h = self.canvas.winfo_height()
        if c_w <= 1 or c_h <= 1 or self.zoom_factor == 0: return

        view_w_orig = c_w / self.zoom_factor;
        view_h_orig = c_h / self.zoom_factor

        if self.img_width <= view_w_orig:
            self.current_view_x = (self.img_width - view_w_orig) / 2.0
        else:
            self.current_view_x = max(0.0, min(self.current_view_x, self.img_width - view_w_orig))

        if self.img_height <= view_h_orig:
            self.current_view_y = (self.img_height - view_h_orig) / 2.0
        else:
            self.current_view_y = max(0.0, min(self.current_view_y, self.img_height - view_h_orig))

    def _update_displayed_image(self):
        """Internal: Crops, resizes, and draws the current view."""
        c_w = self.canvas.winfo_width();
        c_h = self.canvas.winfo_height()
        if c_w <= 1 or c_h <= 1 or self.pil_image_original is None or self.zoom_factor == 0: return

        view_w_orig = c_w / self.zoom_factor;
        view_h_orig = c_h / self.zoom_factor
        crop_L_orig = self.current_view_x;
        crop_U_orig = self.current_view_y

        bg_color = self._get_canvas_bg_color()
        base_img_w = max(1, int(round(view_w_orig)));
        base_img_h = max(1, int(round(view_h_orig)))

        # Create base_image with the mode of the original image
        base_image = Image.new(self.pil_image_original.mode, (base_img_w, base_img_h), bg_color)

        src_crop_L = max(0, int(round(crop_L_orig)))
        src_crop_U = max(0, int(round(crop_U_orig)))
        src_crop_R = min(self.img_width, int(round(crop_L_orig + view_w_orig)))
        src_crop_D = min(self.img_height, int(round(crop_U_orig + view_h_orig)))

        if src_crop_L < src_crop_R and src_crop_U < src_crop_D:
            actual_cropped_content = self.pil_image_original.crop(
                (src_crop_L, src_crop_U, src_crop_R, src_crop_D)
            )
            paste_x_on_base = int(round(max(0, src_crop_L - crop_L_orig)))
            paste_y_on_base = int(round(max(0, src_crop_U - crop_U_orig)))

            if actual_cropped_content.mode == "RGBA" and base_image.mode == "RGBA":
                base_image.paste(actual_cropped_content, (paste_x_on_base, paste_y_on_base), actual_cropped_content)
            else:  # Handles RGB pasting or RGBA onto RGB (alpha is ignored)
                base_image.paste(actual_cropped_content, (paste_x_on_base, paste_y_on_base))

        target_resize_w = max(1, c_w);
        target_resize_h = max(1, c_h)
        final_pil_image_for_display = base_image.resize(
            (target_resize_w, target_resize_h), self.resample_filter
        )

        self.tk_image = ImageTk.PhotoImage(final_pil_image_for_display)

        if self.image_on_canvas:
            self.canvas.itemconfig(self.image_on_canvas, image=self.tk_image)
            self.canvas.coords(self.image_on_canvas, 0, 0)
        else:
            self.image_on_canvas = self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
        self.canvas.tag_raise(self.image_on_canvas)

    # --- Event Handlers ---
    def on_mouse_press(self, event):
        self.canvas.focus_set()
        self._drag_start_x_canvas = event.x;
        self._drag_start_y_canvas = event.y
        self._view_start_x_pan = self.current_view_x;
        self._view_start_y_pan = self.current_view_y
        self.canvas.config(cursor="fleur")

    def on_mouse_drag(self, event):
        if self.zoom_factor == 0: return
        dx_canvas = event.x - self._drag_start_x_canvas;
        dy_canvas = event.y - self._drag_start_y_canvas
        self.current_view_x = self._view_start_x_pan - (dx_canvas / self.zoom_factor)
        self.current_view_y = self._view_start_y_pan - (dy_canvas / self.zoom_factor)
        self._clamp_view_coordinates();
        self._update_displayed_image()

    def on_mouse_release(self, event):
        self.canvas.config(cursor="")

    def on_canvas_resize(self, event):
        self._clamp_view_coordinates(); self._update_displayed_image()

    def on_z_press(self, event):
        if event.keysym == 'z': self.z_key_pressed = True

    def on_z_release(self, event):
        if event.keysym == 'z': self.z_key_pressed = False

    def on_i_press(self, event):
        if event.keysym == 'i' and self.z_key_pressed:
            # Use event.x/y if bound to canvas, event.x_root/y_root if bound to master
            # Assuming canvas has focus or mouse is over it for master binding
            canvas_x = event.x_root - self.canvas.winfo_rootx()
            canvas_y = event.y_root - self.canvas.winfo_rooty()
            self._zoom('in', canvas_x, canvas_y)

    def on_o_press(self, event):
        if event.keysym == 'o' and self.z_key_pressed:
            canvas_x = event.x_root - self.canvas.winfo_rootx()
            canvas_y = event.y_root - self.canvas.winfo_rooty()
            self._zoom('out', canvas_x, canvas_y)

    def _zoom(self, direction, canvas_mouse_x, canvas_mouse_y):
        """Internal: Handles zoom logic centered on mouse position."""
        c_w = self.canvas.winfo_width();
        c_h = self.canvas.winfo_height()
        if c_w <= 1 or c_h <= 1 or self.zoom_factor == 0: return

        clamped_mx = max(0, min(canvas_mouse_x, c_w - 1))
        clamped_my = max(0, min(canvas_mouse_y, c_h - 1))

        img_x_at_cursor = self.current_view_x + (clamped_mx / self.zoom_factor)
        img_y_at_cursor = self.current_view_y + (clamped_my / self.zoom_factor)

        old_zoom = self.zoom_factor
        if direction == 'in':
            self.zoom_factor *= self.zoom_step
        else:
            self.zoom_factor /= self.zoom_step
        self.zoom_factor = max(self.min_zoom, min(self.zoom_factor, self.max_zoom))

        if abs(old_zoom - self.zoom_factor) < 1e-9: return  # No change

        self.current_view_x = img_x_at_cursor - (clamped_mx / self.zoom_factor)
        self.current_view_y = img_y_at_cursor - (clamped_my / self.zoom_factor)

        self._clamp_view_coordinates();
        self._update_displayed_image()


if __name__ == '__main__':
    # Example usage for testing the PannableImageViewer directly
    root = tk.Tk()
    root.title("Pannable Image Viewer - Test")
    root.geometry("700x500")

    # Create a simple test image
    try:
        # Try to load a test image if available
        test_img = Image.open("test_image.png")  # Replace with a path to your test image
        print("Loaded test_image.png")
    except FileNotFoundError:
        print("test_image.png not found, creating a default pattern.")
        test_img = Image.new("RGB", (1200, 900), "lightgreen")
        draw = ImageDraw.Draw(test_img)
        for i in range(0, max(test_img.width, test_img.height), 50):
            draw.line([(i, 0), (0, i)], fill="blue", width=2)
            draw.text((i + 5, i + 5), f"({i},{i})", fill="black")
        draw.text((test_img.width // 2 - 50, test_img.height // 2 - 10), "CENTER", fill="red")

    viewer = PannableImageViewer(root, test_img)


    # Add a button to test set_image
    def change_image():
        new_img = Image.new("RGB", (800, 600), "orange")
        d = ImageDraw.Draw(new_img)
        d.text((100, 100), "New Image!", fill="black")
        viewer.set_image(new_img)


    button = tk.Button(root, text="Set New Image (800x600 Orange)", command=change_image)
    button.pack(side=tk.BOTTOM)

    root.mainloop()