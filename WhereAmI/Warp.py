import numpy as np
from skimage.transform import ProjectiveTransform, warp
from skimage import img_as_ubyte
import cv2

# Define the source points (selected from the image from all four outside corners)
source_points = np.array([
    [1024.372, 172.385],  # Replace with your first point (top-left)
    [2790.222, 271.582],  # Replace with your second point (top-right)
    [382.735, 1668.895],  # Replace with your third point (bottom-left)
    [3110.657, 1877.322]   # Replace with your fourth point (bottom-right)
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

def debugImage(image):
    cv2.line(image, pt(source_points[0]), pt(source_points[1]), (255, 0, 0), 5)
    cv2.line(image, pt(source_points[1]), pt(source_points[3]), (255, 0, 0), 5)
    cv2.line(image, pt(source_points[3]), pt(source_points[2]), (255, 0, 0), 5)
    cv2.line(image, pt(source_points[2]), pt(source_points[0]), (255, 0, 0), 5)
    return image

def pt(point):
    val = (
        int(point[0].item()),
        int(point[1].item())
    )
    return val

# Warp the image using the perspective transformation
def flattenImage(image):
    return img_as_ubyte(warp(image, transform, output_shape=(2160, 3840)))