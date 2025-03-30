
import  cv2
width = 356
height = 356

# Calculate total features
total_features = width * height
print(f"Total number of features: {total_features}")


# Load an image
image = cv2.imread('cat.png')

# Get dimensions
height, width, channels = image.shape
print(height, width, channels)
total_pixels = height * width

print(f"Image Dimensions: {width}x{height}")
print(f"Total Pixels: {total_pixels}")