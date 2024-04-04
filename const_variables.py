from typing import Tuple
# NAMES
OUT_CV: str = "@out"
BIN_CV: str = "@binop"
PRINT_CV: str = "@print"
ERROR_CV: str = "@error"
# VALUES
_min_max: int = pow(2,31)
INT_MIN_MAX: Tuple[int,int] = (-_min_max,_min_max-1)
# OPTIONS
EXCLUDE_FOUND: bool = True # Excludes found feasible values from searches, adds overhead but results in more feasible values
FEASIBILITY_DIVISIONS: int = 16 # Number of times to divide unknown ranges