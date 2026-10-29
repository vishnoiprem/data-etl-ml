import numpy as np
from PIL import Image

# Create a 3x3 RGB image
pixels = np.array([[[255, 0, 0], [0, 255, 0], [0, 0, 255]],
                   [[255, 255, 0], [0, 255, 255], [255, 0, 255]],
                   [[128, 128, 128], [255, 255, 255], [0, 0, 0]]], dtype=np.uint8)

# Convert to image and display
image = Image.fromarray(pixels)
image.show()
image.close()