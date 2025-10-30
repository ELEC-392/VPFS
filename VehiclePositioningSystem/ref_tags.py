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

ref_tags: Dict[int, ReferenceTag] = { }

def _addTag(tag: ReferenceTag):
    ref_tags[tag.id] = tag

# Currently just one tag, ID 0, placed at origin
# _addTag(ReferenceTag(0, 0, 0))

# Tags for lab setup
# _addTag(ReferenceTag(584, 0.53, 0.715))
_addTag(ReferenceTag(0, 0, 0))