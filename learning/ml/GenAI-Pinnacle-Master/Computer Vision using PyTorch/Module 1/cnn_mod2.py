import numpy as np

# Human-like: structured 2D array
image_2d = np.array([[0, 255, 0],
                     [255, 0, 255],
                     [0, 255, 0]])

# ANN-like: flattened array
image_flat = image_2d.flatten()
print("Human perception (2D):", image_2d)
print("ANN perception (1D):", image_flat)

import  cv2
# Load an image in grayscale
image = cv2.imread('cat.png', 0)

# Apply edge detection
edges = cv2.Canny(image, 100, 200)

cv2.imshow('Edges', edges)
cv2.waitKey(0)
cv2.destroyAllWindows()