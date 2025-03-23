import numpy as np
from skimage.transform import ProjectiveTransform, warp
from skimage import img_as_ubyte

# Define the source points (selected from the image from all four outside corners)
source_points = np.array([
    [1186.6777991593658, 202.94275079758972],  # Replace with your first point (top-left)
    [3006.8226312857646, 274.89292044361173],  # Replace with your second point (top-right)
    [694.694206714944, 1476.6552134501444],  # Replace with your third point (bottom-left)
    [3310.1801033068314, 1657.5029371550108]   # Replace with your fourth point (bottom-right)
], dtype="float32")

# Define the destination points (desired eagle-eye view)
destination_points = np.array([
    [0, 0],        # Top-left corner of the transformed image
    [3840, 0],      # Top-right corner of the transformed image
    [0, 2160],      # Bottom-left corner of the transformed image
    [3840, 2160]     # Bottom-right corner of the transformed image
], dtype="float32")

# Compute the perspective transformation matrix
transform = ProjectiveTransform()
transform.estimate(destination_points, source_points)

# Warp the image using the perspective transformation
def flattenImage(image):
    return img_as_ubyte(warp(image, transform, output_shape=(2160, 3840)))