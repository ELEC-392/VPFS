from typing import Dict
import numpy as np
from numpy.typing import *

class ReferenceTag:
    def __init__(self, id, x, y):
        self.id = id
        self.x = x
        self.y = y
        self.z = 0
        self.mat = self._build_mat()

    def _build_mat(self) -> ArrayLike:
        return np.array([
            [1, 0, 0, self.x],
            [0, -1, 0, self.y],
            [0, 0, -1, self.z],
            [0, 0, 0, 1]
        ])

refTags: Dict[int, ReferenceTag] = { }

def _addTag(tag: ReferenceTag):
    refTags[tag.id] = tag

# Currently just one tag, ID 0, placed at origin
# _addTag(ReferenceTag(0, 0, 0))

# Tags for lab setup
# _addTag(ReferenceTag(584, 0.53, 0.715))
_addTag(ReferenceTag(585, 0.29, 1.35))

# Tag 1:  1.29, 1.35
# Tag 2: 4.52, 1.35
# Tag 3: 2.13	1.35
# Tag 4: 3.05	0.29
# Tag 583: 1.81	4.59
# Tag 584: 5.85	2.33
# Tag 585: 4.52 2.93