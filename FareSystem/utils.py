import math

class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y
    def __eq__(self, other):
        return self.x == other.x and self.y == other.y
    def dist(self, other):
        """
        Calculate the distance from this point to another
        :param other: Other point to compare with
        :return: Distance
        """
        return math.dist((self.x, self.y), (other.x, other.y))