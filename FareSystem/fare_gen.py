"""
Spawn-point–biased fare generator.

Purpose:
- Pick two distinct spawn points and create a Fare between them.
- Enforce distance bounds and avoid reusing endpoints already used by active fares.
- Bias the fare type (NORMAL/SUBSIDIZED/SENIOR) using per-point probabilities.
- Nudge probabilities toward a target distribution so the active list stays balanced.

Returns:
- A new Fare when a valid pair is found within 10 tries.
- None if no valid pairing can be found in those attempts.
"""

from attr import dataclass  # Uses the 'attrs' library's dataclass. stdlib alternative: from dataclasses import dataclass

from utils import Point
from fare import Fare, FareType
import random

from fare_prob import FareProbability

@dataclass
class SpawnPoint:
    """
    A predefined location on the map and its fare-type bias.
    - point: the (x, y) spawn coordinate.
    - biases: a FareProbability describing likelihoods for each FareType.
    """
    point: Point
    biases: FareProbability


# Candidate spawn points and their type biases.
# Example biases:
# - (0,0) always SENIOR, (1,1) and (2,2) heavily SUBSIDIZED, others default mix.
points: [SpawnPoint] = [
    # This one always spawns seniors for reasons I guess
    SpawnPoint(Point(0, 0), FareProbability(0, 0, 1)),
    # These two are always subsidized
    SpawnPoint(Point(1, 1), FareProbability(0, 1, 1)),
    SpawnPoint(Point(2, 2), FareProbability(0, 1, 1)),
    SpawnPoint(Point(3, 3), FareProbability()),
    SpawnPoint(Point(4, 4), FareProbability()),
    SpawnPoint(Point(5, 5), FareProbability()),
    SpawnPoint(Point(6, 6), FareProbability()),
    SpawnPoint(Point(7, 7), FareProbability()),
    SpawnPoint(Point(8, 8), FareProbability()),
    SpawnPoint(Point(9, 9), FareProbability()),
    SpawnPoint(Point(10, 10), FareProbability()),
    SpawnPoint(Point(11, 11), FareProbability()),
]

# Minimum and maximum allowed distance between spawn points
DIST_MIN = 0.5
DIST_MAX = 999

# TODO: Find a way to link this to the one in FMS.py without a circular import
TARGET_FARES = 5

# Target composition of active fares (ratios across NORMAL/SUBSIDIZED/SENIOR).
# We aim for roughly 1–2 special fares out of TARGET_FARES, remainder NORMAL.
targetProbabilities = {
    FareType.SUBSIDIZED: 1.5 / TARGET_FARES,
    FareType.SENIOR: 1.5 / TARGET_FARES,
}
targetProbabilities[FareType.NORMAL] = 1 - sum(targetProbabilities.values())


def generate_fare(existingFares: [Fare]) -> Fare or None:
    """
    Try to generate a new fare that:
    - Uses two distinct spawn points not currently occupied by active fares.
    - Falls within distance bounds [DIST_MIN, DIST_MAX].
    - Selects a FareType by merging endpoint biases and reweighting toward targets.

    :param existingFares: Current fare list (active and inactive).
    :return: A new Fare or None if generation failed after several attempts.
    """

    # May be bound later to guarantee a range of distances
    min_dist = DIST_MIN
    max_dist = DIST_MAX

    # Collect endpoints from currently active fares to avoid reuse, and
    # track live counts of each fare type to compute balancing multipliers.
    existing = []
    quantities: dict[FareType, float] = {
        FareType.NORMAL: 0,
        FareType.SUBSIDIZED: 0,
        FareType.SENIOR: 0,
    }
    active_fares: int = 0
    for fare in existingFares:
        if fare.isActive:
            active_fares += 1
            existing.append(fare.src)
            existing.append(fare.dest)
            quantities[fare.type] += 1

    # Try up to 10 random pairings to find a legal (distinct + in-range + unused) route.
    ovf = 0
    success = False
    while ovf < 10 and not success:
        ovf += 1
        # Pick two random points and validate the pairing
        p1: SpawnPoint = random.choice(points)
        p2: SpawnPoint = random.choice(points)

        # Distance between endpoints (instance-method call style)
        dist = Point.dist(p1.point, p2.point)

        # Need two unique points, within distance bounds, and not already in use
        if (
            p1.point == p2.point
            or dist > max_dist
            or dist < min_dist
            or p1.point in existing
            or p2.point in existing
        ):
            continue
        success = True

    # Compute per-type probability multipliers to pull the mix toward targets.
    # If a type is underrepresented, it gets >1x multiplier; overrepresented gets <1x.
    prob_mul: dict[FareType, float] = {}
    for key, value in quantities.items():
        # Current share of active fares for this type (avoid div-by-zero)
        curr_ratio = value / max(active_fares, 1)
        if curr_ratio == 0:
            curr_ratio = 0.01  # small epsilon to avoid singularity
        # Bound multiplier between 0.25x and 10x
        prob_mul[key] = min(max(targetProbabilities[key] / curr_ratio, 1 / 4), 10)

    if success:
        # Merge endpoint biases into a base probability distribution
        prob = FareProbability.merge(p1.biases, p2.biases)

        # Reweight by multipliers to approach the target composition.
        # NOTE: If 'prob' is a dict-like, this should be prob.items():
        # for key, value in prob.items():
        for key, value in prob:
            prob[key] *= prob_mul.get(key, 1)

        # Sample a FareType from the reweighted distribution
        fare_type = prob.roll()

        # Build the new Fare
        return Fare(p1.point, p2.point, fare_type)

    # No valid pairing found in allotted attempts
    return None