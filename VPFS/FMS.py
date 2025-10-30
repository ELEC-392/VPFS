import time

from fare_gen import generate_fare
from utils import Point
from fare import Fare
from team import Team
from threading import Lock

from fare import FareType

matchRunning = False
matchNum = 0
matchDuration = 0
matchEndTime = 0

fares : list[Fare] = [ ]
mutex = Lock()

# Lazy way to quickly generate some dummy fares
points = [
    # Point(0,2),
    # Point(3,0),
    # Point(0,-4),
    # Point(-5,0)
]
for point in points:
    fares.append(Fare(Point(0,0), point, FareType.NORMAL))

teams : {int : Team} = {
    3 : Team(3),
    5 : Team(5),
    7 : Team(7),
    10 : Team(10)
}

TARGET_FARES = 5

genCooldown = 0

def do_generation() -> bool:
    global fares, genCooldown

    # Get number of active fares
    count = 0
    for fare in fares:
        if fare.isActive:
            count += 1

    # Don't over-generate
    if count >= TARGET_FARES:
        return False

    # Wait a bit between generating new fares
    if time.time() < genCooldown:
        return False

    # Wait a full 3s to generate the last fare, and scale others linearly
    genCooldown = time.time() + (count / TARGET_FARES) * 3
    return True

def periodic():
    global fares
    while True:
        with mutex:
            # Update fare statuses
            for idx, fare in enumerate(fares):
                fare.periodic(idx, teams)

            # Generate a new fare if needed
            if do_generation():
                fare = generate_fare(fares)
                if fare is not None:
                    fares.append(fare)
                    print("New Fare")
                else:
                    print("Failed faregen")
        time.sleep(0.02)

def config_match(num: int, duration: int):
    global matchNum, matchDuration, matchRunning, matchEndTime
    with mutex:
        # Only apply when match is finished
        if matchEndTime < time.time():
            matchNum = num
            matchDuration = duration
            matchEndTime = 0
            matchRunning = False

def start_match():
    global matchEndTime, matchRunning
    with mutex:
        if not matchRunning:
            matchEndTime = time.time() + matchDuration
            matchRunning = True

def cancel_match():
    global matchEndTime
    with mutex:
        if matchRunning:
            matchEndTime = 0