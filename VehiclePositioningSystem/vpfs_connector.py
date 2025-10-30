from typing import Dict, Tuple
import socketio
import sys

sock = socketio.Client()

connected = False

@sock.event
def connect():
    global connected
    connected = True
    print("Connected to VFPS")

@sock.event
def connect_error(data):
    global connected
    connected = False
    print("The connection failed!")

@sock.event
def disconnect():
    global connected
    connected = False
    print("Disconnected from VPFS")

# Localhost server works this is the same computer as VPFS
if 'vpfs' in sys.argv:
    sock.connect("http://192.168.1.100:5000/")

def send_update(tagPoses: Dict[int, Tuple[int, int, int]]):
    if not connected:
        return

    data = []
    for tag, pose in tagPoses.items():
        data.append({
            'team': tag,
            'x': pose[0],
            'y': pose[1]
        })
    sock.emit("whereami_update", data)