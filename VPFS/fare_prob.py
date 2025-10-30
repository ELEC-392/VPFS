from fare import FareType
from typing import Self, Tuple
import random

class FareProbability:
    def __init__(self,
                 # Default Probabilities, sums to 100%
                 normal=0.75,
                 subsidized=0.15,
                 senior=0.1):

        self._values : dict[FareType, float] = {
                FareType.NORMAL: normal,
                FareType.SUBSIDIZED: subsidized,
                FareType.SENIOR: senior
            }

    @staticmethod
    def merge(p1, p2):
        return FareProbability(
            p1._values[FareType.NORMAL] + p2._values[FareType.NORMAL],
            p1._values[FareType.SUBSIDIZED] + p2._values[FareType.SUBSIDIZED],
            p1._values[FareType.SENIOR] + p2._values[FareType.SENIOR],
        )

    def copy(self) -> Self:
        return FareProbability(
            self._values[FareType.NORMAL],
            self._values[FareType.SUBSIDIZED],
            self._values[FareType.SENIOR],
        )

    def __getitem__(self, key: FareType):
        return self._values[key]

    def __setitem__(self, key: FareType, value: float):
        self._values[key] = value

    def keys(self):
        return self._values.keys()

    def values(self):
        return self._values.values()

    def __iter__(self):
        return self._values.items().__iter__()

    def roll(self) -> FareType:
        """
        Roll the probability, and obtain resulting fare type
        :return: Faretype selected based on probabilities
        """
        types: [FareType] = []
        probs: [float] = []
        sum = 0

        # Create collections of keys/weights, also handle negatives here
        for key, value in self._values.items():
            types.append(key)
            prob = max(0.0, value)
            probs.append(prob)
            sum += prob

        # If the probabilities sum to zero, then don't roll
        if sum == 0:
            return FareType.NORMAL

        # Use weighted random function
        return random.choices(types, probs)[0]



