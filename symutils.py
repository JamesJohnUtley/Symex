import math
from typing import Tuple

def get_qu_bounds(bounds: Tuple[int, float, int]) -> Tuple[float, float, float]:
    return tuple(get_qu(x) for x in bounds)

def get_qu(count: float) -> float:
    if count == 0:
        return -1
    return math.log2(count)