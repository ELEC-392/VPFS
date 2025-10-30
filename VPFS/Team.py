import time

from utils import Point

class Team:
    def __init__(self, number : int):
        self.number = number
        self.money = 0
        self.karma = 20
        self.currentFare : int or None = None
        self.pos = Point(0, 0)
        self.lastPosUpdate = 0
        self.lastStatus = 0

    def update_position(self, pos : Point):
        self.pos = pos
        self.lastPosUpdate = time.time()