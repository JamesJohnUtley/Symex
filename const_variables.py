from typing import Tuple
# DEFAULTS
RUN_DEFAULT_VALUE = "run_default_value"
PROBLEMATIC_ID = -1
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
FEASIBILITY_DIVISIONS: int = 16 # Number of times to divide unknown ranges recommend 2^x - 1 for even ranges
DRAWS: int = 100 # Number of times to draw for a given path
MAX_DEPTH: int = 10 # Max blocks to traverse up the control flow graph
MAX_LOOPS: int = 3 # Maximum Number of loops to symbolically execute before falling back on concrete