
from solving import SolvingState, SymbolicInstruction, SymbolicConstraint
from typing import List, Tuple, Set, Any
from const_variables import INT_MIN_MAX, EXCLUDE_FOUND, FEASIBILITY_DIVISIONS, DRAWS
from queue import Queue
from symutils import *
import sys
import operator
import random

# (Min, Max), Feasible Values Inside
class FeasibilityRange:
    def __init__(self, value_range: Tuple[int,int], feasibility_set: Set[int]):
        self.value_range = value_range
        self.feasibility_set = feasibility_set
        self.mid = ((value_range[1] - value_range[0]) // 2) + value_range[0]
        self.size = (value_range[1] - value_range[0] + 1)
        self.unknown_count = self.size - len(feasibility_set)

class FeasibleValueSet:
    def __init__(self, base_solver: SolvingState, possibility_range: Tuple[int,int] = INT_MIN_MAX): # Make this multiple
        self.possibility_range = possibility_range
        self.base_solver = base_solver
        self.solver_exluded = base_solver.copy()
        self.feasible_values: Set[int] = set()
        if len(base_solver.unstored_variables) > 1:
            print("ERROR: Multiple Unknown Variables",file=sys.stdout)


    # Upper Bound, PE, Lower bound
    def get_bounds(self) -> Tuple[int, float, int]:
        if len(self.base_solver.unstored_variables) == 0:
            print("ERROR: NO UNKNOWN",file=sys.stdout)
            return (self.possibility_range[1] - self.possibility_range[0] + 1,) * 3
        self.unknown_sym_var = self.base_solver.get_current_variable_iteration(next(iter(self.base_solver.unstored_variables)))
        self._build_set()
        # Count
        feasible_count, unknown_count, total_count = self._count()
        # Construct Weights
        frs_weights: List[float] = self._construct_weights(total_count)
        # Estimate
        if unknown_count > 0:
            feasiblity_estimate: float = self._estimate_feasibility(frs_weights)
        else:
            feasiblity_estimate: float = 0
        ub = feasible_count + unknown_count
        pe = feasible_count + unknown_count * feasiblity_estimate
        lb = feasible_count
        return (ub, pe, lb)
    
    def _build_set(self):
        minmax = self._find_min_max()
        print(minmax)
        frs_to_divide: Queue[FeasibilityRange] = Queue()
        frs_to_divide.put(FeasibilityRange(minmax, self.feasible_values))
        for _ in range(FEASIBILITY_DIVISIONS):
            if not frs_to_divide.empty():
                for x in self._divide_range(frs_to_divide.get()):
                    frs_to_divide.put(x)
        self.frs: List[FeasibilityRange] = []
        while not frs_to_divide.empty():
            fr: FeasibilityRange = frs_to_divide.get()
            if fr.unknown_count > 0:
                self.frs.append(fr)

    def _construct_weights(self, total_count: int) -> List[float]:
        frs_weights: List[float] = []
        for x in self.frs:
            frs_weights.append(x.size / total_count)
        return frs_weights

    def _estimate_feasibility(self, frs_weights: List[float]) -> float:
        found_unknown: int = 0
        feasible_unknowns: int = 0
        for x in random.choices(self.frs,frs_weights,k=DRAWS):
            draw = random.randint(x.value_range[0], x.value_range[1])
            if draw not in x.feasibility_set:
                # Unknown Found
                found_unknown += 1
                if(self._query_value(draw)):
                    feasible_unknowns += 1
        return feasible_unknowns / found_unknown
        # hit_ratio = found_unknown / DRAWS

    def _count(self) -> Tuple[int,int,int]:
        feasible_count = len(self.feasible_values)
        unknown_count: int = 0
        total_count: int = 0
        for fr in self.frs:
            unknown_count += fr.unknown_count
            total_count += fr.size
        return (feasible_count, unknown_count, total_count)

    def _divide_range(self, fr: FeasibilityRange) -> List[FeasibilityRange]:
        # Divide
        low_range: Tuple[int,int] = (fr.value_range[0],fr.mid)
        high_range: Tuple[int,int] = (fr.mid+1,fr.value_range[1])
        # Divide Feasible Values
        low_set: Set[int] = set()
        high_set: Set[int] = set()
        for x in fr.feasibility_set:
            if x <= fr.mid:
                low_set.add(x)
            else:
                high_set.add(x)
        # Check Feasibility
        new_ranges: List[FeasibilityRange] = []
        feasible, found = self._query_range(low_range, True)
        if feasible:
            low_set.add(found)
            self._record_feasible(found)
            new_ranges.append(FeasibilityRange((low_range),low_set)) # TODO: Only append if there are unknowns?
        feasible, found = self._query_range(high_range, True)
        if feasible:
            high_set.add(found)
            self._record_feasible(found)
            new_ranges.append(FeasibilityRange((high_range),high_set))
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
            feasible, found_feasible = self._query_range((mid+1,max))
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
            feasible, found_feasible = self._query_range((min,mid))
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
    def _query_value(self, value: int) -> bool:
        solver: SolvingState = self.base_solver.copy()
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