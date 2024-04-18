import math
from typing import Tuple, Callable, Any, List
from tests import *

class OutputSummary:
    def __init__(self, function: Callable, prints: List[str], errors: List[str], output: Any):
        self.function: Callable = function
        self.prints: List[str] = prints
        self.errors: List[str] = errors
        self.output: Any = output

    def __eq__(self, other):
        if isinstance(other, OutputSummary):
            if int(other.output) != int(self.output):
                return False
            if other.prints != self.prints:
                return False
            # if other.errors != self.errors: TODO: Fix Stderr Detection
            #     return False
            return True
        return False

def construct_output_summary(function_name: str, prints_filepath: str, errors_filepath: str, output: Any) -> OutputSummary:
    # Set Prints
    prints = []
    if prints_filepath != None:
        with open(prints_filepath) as prints_file:
            for line in prints_file:
                prints.append(line.strip())
        prints.reverse()
    errors = []
    if errors_filepath != None:
        with open(errors_filepath) as errors_file:
            for line in errors_file:
                errors.append(line.strip())
        errors.reverse()
    return OutputSummary(globals()[function_name], prints, errors, output)

def get_qu_bounds(bounds: Tuple[int, float, int]) -> Tuple[float, float, float]:
    return tuple(get_qu(x) for x in bounds)

def get_qu(count: float) -> float:
    if count == 0:
        return -1
    return math.log2(count)