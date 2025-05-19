import numpy as np
from PIL import Image


class NumpyImage:
    def __init__(self, pil_image: Image.Image):
        # Convert PIL image to NumPy array in RGB format
        self.array = np.array(pil_image.convert("RGB"), dtype=np.uint8)

    def get_numpy(self) -> np.ndarray:
        """Return the internal NumPy array (RGB)."""
        return self.array

    def draw_rectangle(self, xy, fill=(0, 0, 0)):
        """
        Fill a rectangle in the image with a color.

        Args:
            xy (tuple): (x0, y0, x1, y1) coordinates of the rectangle.
            fill (tuple): (R, G, B) color tuple.
        """
        ((x0, y0), (x1, y1)) = xy
        # Clip bounds to array dimensions
        x0, x1 = np.clip([x0, x1], 0, self.array.shape[1])
        y0, y1 = np.clip([y0, y1], 0, self.array.shape[0])

        # added 1 to make ranges inclusive
        self.array[y0:y1+1, x0:x1+1] = fill


if __name__=="__main__":

    # Create blank white PIL image
    pil_img = Image.new("RGB", (512, 512), "white")

    # Wrap it in our class
    img = NumpyImage(pil_img)

    # Draw red rectangle
    img.draw_rectangle((100, 100, 200, 200), fill=(255, 0, 0))

    # Use in Napari
    import napari

    viewer = napari.view_image(img.get_numpy(), rgb=True)
    napari.run()