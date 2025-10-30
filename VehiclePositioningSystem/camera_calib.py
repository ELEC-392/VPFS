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
import sys
import shutil

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
pipeline = ' ! '.join([
    "v4l2src device=/dev/video0",
    "video/x-raw, format=YUYV, width=1600, height=896, framerate=15/2",  # fix 'format'
    "videoconvert",
    "video/x-raw, format=(string)BGR",
    "appsink drop=true sync=false"
])

is_windows = sys.platform.startswith("win")
has_v4l2ctl = shutil.which("v4l2-ctl") is not None

# Optional: configure camera focus (Linux/Jetson only)
if not is_windows and has_v4l2ctl:
    os.system("v4l2-ctl -d /dev/video0 -c focus_auto=0")
    os.system("v4l2-ctl -d /dev/video0 -c focus_absolute=0")
    os.system("v4l2-ctl -d /dev/video0 -C focus_auto")
    os.system("v4l2-ctl -d /dev/video0 -C focus_absolute")

# Open the camera using the appropriate backend
if is_windows:
    # Use DirectShow on Windows
    cam = cv.VideoCapture(0, cv.CAP_DSHOW)
    cam.set(cv.CAP_PROP_FRAME_WIDTH, 1920)
    cam.set(cv.CAP_PROP_FRAME_HEIGHT, 1080)
    # Disable autofocus if supported
    cam.set(cv.CAP_PROP_AUTOFOCUS, 0)
    cam.set(cv.CAP_PROP_FOCUS, 0)  # may be ignored by some drivers
else:
    # Use GStreamer pipeline on Jetson/Linux
    cam = cv.VideoCapture(pipeline, cv.CAP_GSTREAMER)

# Create a preview window and UI state
cv.namedWindow("Calibration", cv.WINDOW_NORMAL)
cv.resizeWindow("Calibration", 1280, 720)
samples = 0

while True:
    # Grab a frame
    ret, img = cam.read()
    if not ret or img is None:
        # If capture fails, continue or break as needed
        continue

    # Convert to grayscale for corner detection
    gray = cv.cvtColor(img, cv.COLOR_BGR2GRAY)

    # Find the chessboard inner corners (pattern size: 7 columns x 5 rows)
    found, corners = cv.findChessboardCorners(gray, (7, 5), None)

    corners2 = None
    if found:
        # Subpixel refinement of detected corners
        corners2 = cv.cornerSubPix(gray, corners, (11, 11), (-1, -1), criteria)
        # Visualize detected corners on the image
        cv.drawChessboardCorners(img, (7, 5), corners2, found)
        status_msg = "Pattern FOUND - press C to capture"
        status_color = (0, 200, 0)
    else:
        status_msg = "Pattern not found"
        status_color = (0, 0, 255)

    # HUD overlay
    cv.putText(img, f"Samples: {samples}", (10, 30), cv.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2, cv.LINE_AA)
    cv.putText(img, status_msg, (10, 60), cv.FONT_HERSHEY_SIMPLEX, 0.7, status_color, 2, cv.LINE_AA)
    cv.putText(img, "C=Capture  Q=Calibrate+Save  ESC=Quit", (10, 90), cv.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 1, cv.LINE_AA)

    # Show preview
    cv.imshow("Calibration", img)
    key = cv.waitKey(1) & 0xFF

    # Capture a sample when pattern is found
    if key == ord('c') and found and corners2 is not None:
        objpoints.append(objp.copy())
        imgpoints.append(corners2)
        samples += 1

    # Calibrate and save
    elif key == ord('q'):
        break

    # Quit without saving
    elif key == 27:  # ESC
        objpoints.clear()
        imgpoints.clear()
        break

# Cleanup window
cv.destroyAllWindows()

# Calibrate using all collected frames.
# gray.shape[::-1] supplies (width, height). Requires at least one detection.
if not objpoints or not imgpoints:
    raise RuntimeError("No samples captured; press 'c' when the pattern is found.")
ret, mtx, dist, rvecs, tvecs = cv.calibrateCamera(
    objpoints, imgpoints, gray.shape[::-1], None, None
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
