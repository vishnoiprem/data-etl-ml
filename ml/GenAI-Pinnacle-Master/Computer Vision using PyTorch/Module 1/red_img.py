import numpy as np
from PIL import Image
import  cv2

# Create a 5x5 grayscale image (0 = black, 255 = white)
pixels = np.array([[0, 50, 100, 150, 255],
                   [50, 75, 125, 175, 200],
                   [100, 125, 150, 175, 200],
                   [150, 175, 200, 225, 255],
                   [255, 200, 175, 150, 125]], dtype=np.uint8)

# Convert to image and display
image = Image.fromarray(pixels)
image.show()

# Create a 100x100 red image
red_image = np.zeros((100, 100, 3), dtype=np.uint8)
red_image[:] = [0, 0, 255]  # Full intensity red

cv2.imwrite('red_image.png', red_image)
cv2.imshow('Red Image', red_image)
cv2.waitKey(0)
cv2.destroyAllWindows()