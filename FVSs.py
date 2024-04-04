
from solving import SolvingState, SymbolicInstruction, SymbolicConstraint
from typing import List, Tuple, Set, Any
from const_variables import INT_MIN_MAX, EXCLUDE_FOUND, FEASIBILITY_DIVISIONS
from queue import Queue
from symutils import *
import sys
import operator

# (Min, Max), Feasible Values Inside
FeasibilityRange = Tuple[Tuple[int, int], Set[int]]

class FeasibleValueSet:
    def __init__(self, base_solver: SolvingState, possibility_range: Tuple[int,int] = INT_MIN_MAX): # Make this multiple
        self.possibility_range = possibility_range
        self.base_solver = base_solver
        self.solver_exluded = base_solver.copy()
        self.feasible_values: Set[int] = set()
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
        minmax = self._find_min_max()
        print(minmax)
        print(self.feasible_values)
        feasible_ranges: Queue[FeasibilityRange] = Queue()
        feasible_ranges.put((minmax, self.feasible_values))
        for _ in range(FEASIBILITY_DIVISIONS):
            for x in self._divide_range(feasible_ranges.get()):
                feasible_ranges.put(x)
        # Count
        print(get_qu(len(self.feasible_values)))
        unknown_count: int = 0
        while not feasible_ranges.empty():
            fr: FeasibilityRange = feasible_ranges.get()
            value_range = fr[0]
            unknown_count += (value_range[1] - value_range[0] + 1) - len(fr[1])
        print(get_qu(unknown_count))


    def _divide_range(self, FR: FeasibilityRange) -> List[FeasibilityRange]:
        value_range: Tuple[int,int] = FR[0]
        feasible_values: Set[int] = FR[1]
        # Divide
        mid = ((value_range[1] - value_range[0]) // 2) + value_range[0]
        low_range: Tuple[int,int] = (value_range[0],mid)
        high_range: Tuple[int,int] = (mid+1,value_range[1])
        # Divide Feasible Values
        low_set: Set[int] = set()
        high_set: Set[int] = set()
        for x in feasible_values:
            if x <= mid:
                low_set.add(x)
            else:
                high_set.add(x)
        # Check Feasibility
        new_ranges: List[FeasibilityRange] = []
        feasible, found = self._query_range(low_range, True)
        if feasible:
            low_set.add(found)
            self._record_feasible(found)
            new_ranges.append(((low_range),low_set))
        feasible, found = self._query_range(high_range, True)
        if feasible:
            high_set.add(found)
            self._record_feasible(found)
            new_ranges.append(((high_range),high_set))
        return new_ranges


    def _find_min_max(self) -> Tuple[int,int]:
        return (self._find_min(),self._find_max())
    
    # Returns 1 before the max feasible
    def _find_max(self) -> int:
        range = self.possibility_range
        max = range[1]
        # Check point
        if(self._query_value(max)):
            return max
        # Other check
        while range[1] - range[0] > 0: # While there is more than 1 value
            mid = ((range[1] - range[0]) // 2) + range[0]
            feasible, found_feasible = self._query_range((mid+1,max)) # TODO: Save Feasible. (Maybe Add constraints to exclude?)
            if feasible:
                range = (mid+1,range[1])
                self._record_feasible(found_feasible)
            else:
                range = (range[0],mid)
        if range[1] != range[0]:
            print("ERROR: Find Max Failure!", file=sys.stderr)
        self._record_feasible(range[0])
        return range[0]
    
    # Returns 1 after the min feasible
    def _find_min(self) -> int:
        range = self.possibility_range
        min = range[0]
        # Check point
        if(self._query_value(min)):
            return min
        while range[1] - range[0] > 0: # While there is more than 1 value
            mid = ((range[1] - range[0]) // 2) + range[0]
            feasible, found_feasible = self._query_range((min,mid)) # TODO: Save Feasible?
            if feasible:
                range = (range[0],mid)
                self._record_feasible(found_feasible)
            else:
                range = (mid+1,range[1])
        if range[1] != range[0]:
            print("ERROR: Find Min Failure!", file=sys.stderr)
        self._record_feasible(range[0])
        return range[0]
    
    # Returns True if feasible/unknown and False if not feasible. Also returns a easible value if feasible/unknown
    def _query_range(self, range: Tuple[int,int], use_excluded: bool = False) -> Tuple[bool, Any]:
        solver: SolvingState = self.base_solver.copy() if not use_excluded else self.solver_exluded.copy()
        solver.constraints.append(SymbolicConstraint(self.unknown_sym_var, range[0], operator.ge))
        solver.constraints.append(SymbolicConstraint(self.unknown_sym_var, range[1], operator.le))
        return solver.check_solvability(self.unknown_sym_var)
    
    # Returns True feasible False infeasible
    def _query_value(self, value: int, use_excluded: bool = False) -> bool:
        solver: SolvingState = self.base_solver.copy() if not use_excluded else self.solver_exluded.copy()
        solver.constraints.append(SymbolicConstraint(self.unknown_sym_var, value, operator.eq))
        feasible, _ = solver.check_solvability(self.unknown_sym_var)
        return feasible
    
    # Record a feasible value as found
    def _record_feasible(self, value: int):
        if value in self.feasible_values:
            return
        self.feasible_values.add(value)
        if EXCLUDE_FOUND:
            self.solver_exluded.constraints.append(SymbolicConstraint(self.unknown_sym_var, value, operator.ne))

    def __str__(self):
        return "ERROR: To String for FVSs not Implemented yet"