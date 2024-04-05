import math
from typing import Tuple

def get_qu_bounds(bounds: Tuple[int, float, int]) -> Tuple[float, float, float]:
    return tuple(get_qu(x) for x in bounds)

def get_qu(count: int):
    return math.log2(count)