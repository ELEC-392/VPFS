"""
Camera intrinsics calibration using a 7x5 chessboard pattern.

Flow:
- Capture frames from /dev/video0 via a GStreamer pipeline (Jetson-friendly).
- Detect chessboard corners and refine them (cornerSubPix) per frame.
- Accumulate 3D object points (ideal chessboard grid in Z=0 plane) and
  corresponding 2D image points.
- Run cv.calibrateCamera to estimate the camera matrix (fx, fy, cx, cy)
  and distortion coefficients.
- Save results to camera_calibration.json for later use.

Notes:
- Ensure the chessboard inner-corner pattern size matches (7,5).
- Move/tilt the chessboard across frames to cover the image area and angles.
- Press 'q' after corners are found in a frame to stop collecting and calibrate.
- Requires OpenCV built with GStreamer; commands use v4l2-ctl (Linux).
"""

import numpy as np
import cv2 as cv
import os
import json

# Termination criteria for corner refinement: stop after 30 iters or epsilon < 1e-3
criteria = (cv.TERM_CRITERIA_EPS + cv.TERM_CRITERIA_MAX_ITER, 30, 0.001)

# Prepare object points for a 7x5 inner-corner chessboard on the Z=0 plane.
# Shape: (N,3) where N = 7*5. Units arbitrary (square size=1).
objp = np.zeros((5 * 7, 3), np.float32)
objp[:, :2] = np.mgrid[0:7, 0:5].T.reshape(-1, 2)  # (x,y) grid, z=0

# Arrays to store all detected corners across frames
objpoints = []  # 3D points in real world (same objp for each successful frame)
imgpoints = []  # 2D points detected in the image

# GStreamer pipeline for Jetson/Linux. Requires OpenCV GStreamer support.
# Tip: 'format' key is commonly used; verify 'fomat' vs 'format' in your env.
pipeline = ' ! '.join([
    "v4l2src device=/dev/video0",
    "video/x-raw, fomat=YUYV, width=1600, height=896, framerate=15/2",
    "videoconvert",
    "video/x-raw, format=(string)BGR",
    "appsink drop=true sync=false"
])

# Optional: configure camera focus for sharper corners (Linux v4l2 controls)
os.system("v4l2-ctl -d /dev/video0 -c focus_auto=0")
os.system("v4l2-ctl -d /dev/video0 -c focus_absolute=0")
# Read back current settings (for logging/verification)
os.system("v4l2-ctl -d /dev/video0 -C focus_auto")
os.system("v4l2-ctl -d /dev/video0 -C focus_absolute")

# Open the camera using the pipeline
cam = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)

while True:
    # Grab a frame
    ret, img = cam.read()
    if not ret or img is None:
        # If capture fails, continue or break as needed
        continue

    # Convert to grayscale for corner detection
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Find the chessboard inner corners (pattern size: 7 columns x 5 rows)
    ret, corners = cv.findChessboardCorners(gray, (7, 5), None)

    # If found, refine corner locations and accumulate points
    if ret is True:
        objpoints.append(objp)

        # Subpixel refinement of detected corners
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        imgpoints.append(corners2)

        # Visualize detected corners on the image
        cv.drawChessboardCorners(img, (7, 5), corners2, ret)
        cv.imshow('img', img)

        # Wait 500 ms; press 'q' to finish collection and calibrate
        key = cv.waitKey(500)
        if key == ord('q'):
            break

# Cleanup windows
cv.destroyAllWindows()

# Calibrate using all collected frames.
# gray.shape[::-1] supplies (width, height). Requires at least one detection.
if not objpoints or not imgpoints:
    raise RuntimeError("No corners collected; cannot calibrate.")
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(
    objpoints,        # list of 3D object points (len = num successful frames)
    imgpoints,        # list of 2D image points
    gray.shape[::-1], # image size (width, height)
    None, None
)

# Save calibration to JSON (NumPy arrays converted to lists for JSON compatibility)
calib = {
    "image_width": int(gray.shape[1]),
    "image_height": int(gray.shape[0]),
    "camera_matrix": mtx.tolist(),                 # 3x3
    "dist_coeffs": dist.ravel().tolist(),          # k1,k2,p1,p2,k3,...
    "rms_reprojection_error": float(ret),
    "rvecs": [rv.ravel().tolist() for rv in rvecs],
    "tvecs": [tv.ravel().tolist() for tv in tvecs],
}
calib_path = os.path.join(os.path.dirname(__file__), "camera_calibration.json")
with open(calib_path, "w", encoding="utf-8") as f:
    json.dump(calib, f, indent=2)
print(f"Saved calibration to: {calib_path}")

# Print camera matrix and derived intrinsics
print(mtx)
print("fx:", mtx[0][0])
print("fy:", mtx[1][1])
print("cx:", mtx[0][2])
print("cy:", mtx[1][2])
