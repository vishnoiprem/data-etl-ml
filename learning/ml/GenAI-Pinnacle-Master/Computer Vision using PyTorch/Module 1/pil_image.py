from PIL import Image

# Load an image
image = Image.open("cat.png")

# Display the image
image.show()

# Get image size (width x height in pixels)
width, height = image.size
print(f"Image size: {width} x {height} pixels")