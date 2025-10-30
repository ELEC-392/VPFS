import re
from time import sleep

import socketio
from socketio import SimpleClient

sock = socketio.Client()

@sock.event
def connect():
    print("I'm connected!")

@sock.event
def connect_error(data):
    print("The connection failed!")

@sock.event
def disconnect():
    print("I'm disconnected!")


sock.connect("http://vpfs.lan:5000/")

team = int(input("Enter team number: "))
lastX = 0
lastY = 0
while True:
    text = input("Enter position in format x,y: ")
    x = None
    y = None
    if text == "":
        x = lastX
        y = lastY
    else:
        try:
            match = re.match(r"\s*([\d.\-+]+)\s*,\s*([\d.\-+]+)", text)
            x = float(match.group(1))
            y = float(match.group(2))
        except Exception as e:
            print("Invalid input format")

    if x is None or y is None:
        continue

    print(f"Setting team {team} to ({x}, {y})")

    sock.emit("whereami_update", [{'team': team, 'x': x, 'y': y}])

    lastX = x
    lastY = y

sock.disconnect()