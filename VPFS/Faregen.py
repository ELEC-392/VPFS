from attr import dataclass

from Utils import Point
from Fare import Fare, FareType
import random

from FareProbability import FareProbability

@dataclass
class SpawnPoint:
    point: Point
    biases: FareProbability

points : [SpawnPoint] = [
    # Aquatic Ave
    SpawnPoint(Point(0.42, 0.42), FareProbability()), #A
    SpawnPoint(Point(1.77, 0.29), FareProbability()), #B
    # SpawnPoint(Point(2.60, 0.29), FareProbability()), #C
    SpawnPoint(Point(3.80, 0.29), FareProbability()), #D
    SpawnPoint(Point(5.20, 0.29), FareProbability()), #E
    # Migration Ave
    SpawnPoint(Point(1.74, 1.35), FareProbability()), #F
    SpawnPoint(Point(3.80, 1.35), FareProbability()), #G
    SpawnPoint(Point(5.25, 1.35), FareProbability()), #H
    # Pondside Ave
    SpawnPoint(Point(1.00, 2.96), FareProbability()), #I
    SpawnPoint(Point(5.25, 2.33), FareProbability()), #J
    # Dabbler
    SpawnPoint(Point(5.25, 2.93), FareProbability()), #K
    # Breadcrumb Ave
    SpawnPoint(Point(1.13, 4.59), FareProbability()), #L
    SpawnPoint(Point(2.46, 4.49), FareProbability()), #M
    # Tail Ave
    SpawnPoint(Point(3.76, 4.34), FareProbability()), #N
    # Duckling Drive
    SpawnPoint(Point(5.25, 4.75), FareProbability()), #O

    # Mallard
    SpawnPoint(Point(5.85, 1.90), FareProbability()), #P
    SpawnPoint(Point(5.93, 4.20), FareProbability()), #Q
    # Waddle
    SpawnPoint(Point(1.35, 2.10), FareProbability()), #R
    # Beak
    SpawnPoint(Point(4.52, 3.53), FareProbability()), #S
    # Quack
    SpawnPoint(Point(0.29, 2.00), FareProbability()), #T
    SpawnPoint(Point(0.29, 2.80), FareProbability()), #U
    SpawnPoint(Point(0.29, 4.10), FareProbability()), #V
]

DIST_MIN = 2.5
DIST_MAX = 999

# TODO: Find a way to link this to the one in FMS.py without a circular import
TARGET_FARES = 8
# Aim to have 1-2 of the special fare types at a time, Normal is the remainder
targetProbabilities = {
    FareType.SUBSIDIZED: 1.5 / TARGET_FARES,
    FareType.SENIOR: 1.5 / TARGET_FARES
}
targetProbabilities[FareType.NORMAL] = 1 - sum(targetProbabilities.values())

def generate_fare(existingFares : [Fare]) -> Fare or None:

    # May be bound later to guarantee a range of distances
    min_dist = DIST_MIN
    max_dist = DIST_MAX

    existing = []
    # Track number of each type
    quantities: dict[FareType, float] = {
        FareType.NORMAL: 0,
        FareType.SUBSIDIZED: 0,
        FareType.SENIOR: 0,
    }
    active_fares : int = 0
    for fare in existingFares:
        if fare.isActive:
            active_fares += 1
            existing.append(fare.src)
            existing.append(fare.dest)
            quantities[fare.type] += 1

    # Cap at 10 tries to avoid getting stuck
    ovf = 0
    success = False
    while ovf < 10 and not success:
        ovf += 1
        # Pick two random points, and make sure they are a valid pairing
        p1: SpawnPoint = random.choice(points)
        p2: SpawnPoint = random.choice(points)
        dist = Point.dist(p1.point, p2.point)
        # Need two unique points, within distance bounds, and not already in use
        if (p1.point == p2.point
                or dist > max_dist
                or dist < min_dist
                or p1.point in existing
                or p2.point in existing):
            continue
        success = True

    # Additional probability weightings to try to balance options
    prob_mul: dict[FareType, float] = { }
    for key, value in quantities.items():
        # Determine the current ratio for the fare type, relative to target qty not actual qty
        curr_ratio = value / max(active_fares, 1)
        if curr_ratio == 0:
            curr_ratio = 0.01
        # Calculate the probability multiplier based on target and current. Bound between 1/10x and 10x
        prob_mul[key] = min(max(targetProbabilities[key] / curr_ratio, 1/4), 10)

    if success:
        prob = FareProbability.merge(p1.biases, p2.biases)
        # Multiply base probabilities by the
        for key, value in prob:
            prob[key] *= prob_mul.get(key, 1)

        return Fare(p1.point, p2.point, prob.roll())
    return None