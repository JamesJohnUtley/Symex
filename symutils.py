import math
from typing import Tuple, Callable, Any, List

class OutputSummary:
    def __init__(self, function: Callable, prints: List[str], errors: List[str], output: Any):
        self.function: Callable = function
        self.prints: List[str] = prints
        self.errors: List[str] = errors
        self.output: Any = output

def get_qu_bounds(bounds: Tuple[int, float, int]) -> Tuple[float, float, float]:
    return tuple(get_qu(x) for x in bounds)

def get_qu(count: float) -> float:
    if count == 0:
        return -1
    return math.log2(count)