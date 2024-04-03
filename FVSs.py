
from solving import SolvingState, SymbolicInstruction, SymbolicConstraint
from typing import List, Tuple, Set, Any
import sys
import operator

class FeasibleValueSet:
    def __init__(self, base_solver: SolvingState):
        self.base_solver = base_solver
        if len(base_solver.unstored_variables) > 1:
            print("ERROR: Multiple Unknown Variables",file=sys.stdout)
        elif len(base_solver.unstored_variables) == 0:
            # TODO: FIX THIS SHOULD NOT ERROR
            print("ERROR: ALL FEASIBLE",file=sys.stdout)
        else:
            print(f"Unknown: {base_solver.unstored_variables}")
            self.unknown_sym_var = self.base_solver.get_current_variable_iteration(next(iter(base_solver.unstored_variables)))
            self._build_set()
    
    def _build_set(self):
        min_max: int = pow(2,31)
        feasible_ranges: List[Tuple[int, int]] = [(-min_max,min_max-1)]
        print(self._query_range((0,2000)))
        print(self._query_value(40))
    
    # Returns True if feasible/unknown and False if not feasible. Also returns a easible value if feasible/unknown
    def _query_range(self, range: Tuple[int,int]) -> Tuple[bool, Any]:
        solver: SolvingState = self.base_solver.copy()
        solver.constraints.append(SymbolicConstraint(self.unknown_sym_var, range[0], operator.ge))
        solver.constraints.append(SymbolicConstraint(self.unknown_sym_var, range[1], operator.le))
        return solver.check_solvability(self.unknown_sym_var)
    
    # Returns True feasible False infeasible
    def _query_value(self, value: int) -> bool:
        solver: SolvingState = self.base_solver.copy()
        solver.constraints.append(SymbolicConstraint(self.unknown_sym_var, value, operator.eq))
        feasible, _ = solver.check_solvability(self.unknown_sym_var)
        return feasible

    def __str__(self):
        return "ERROR: To String for FVSs not Implemented yet"