
from solving import SolvingState, SymbolicInstruction, SymbolicConstraint
from typing import List, Tuple, Set, Any
from const_variables import INT_MIN_MAX, EXCLUDE_FOUND, FEASIBILITY_DIVISIONS, DRAWS
from queue import Queue
from symutils import *
from tests import *
import sys
import operator
import random
from io import StringIO
# (Min, Max), Feasible Values Inside
class FeasibilityRange:
    def __init__(self, value_range: Tuple[int,int], feasibility_set: Set[int]):
        self.value_range = value_range
        self.feasibility_set = feasibility_set
        self.mid = ((value_range[1] - value_range[0]) // 2) + value_range[0]
        self.size = (value_range[1] - value_range[0] + 1)
        self.unknown_count = self.size - len(feasibility_set)

class FeasibleValueSet:
    def __init__(self, base_solvers: List[SolvingState], output_summary: OutputSummary, possibility_range: Tuple[int,int] = INT_MIN_MAX):
        self.output_summary: OutputSummary = output_summary
        self.possibility_range: Tuple[int,int] = possibility_range
        self.base_solvers: List[SolvingState] = base_solvers
        self.excluded_solvers: List[SolvingState] = []
        for base_solver in base_solvers:
            self.excluded_solvers.append(base_solver.copy())
        self.feasible_values: Set[int] = set()
        for base_solver in base_solvers:
            if len(base_solver.unstored_variables) > 1:
                print("ERROR: Multiple Unknown Variables",file=sys.stdout)
        for base_solver in self.base_solvers:
            if len(base_solver.unstored_variables) == 0:
                print("ERROR: NO UNKNOWN",file=sys.stdout)
                return (self.possibility_range[1] - self.possibility_range[0] + 1,) * 3
        self.unknown_sym_vars: Any = []
        for base_solver in self.base_solvers:
            self.unknown_sym_vars.append(base_solver.get_current_variable_iteration(next(iter(base_solver.unstored_variables))))
        print([x.name for x in self.unknown_sym_vars])


    # Upper Bound, PE, Lower bound
    def get_bounds(self) -> Tuple[int, float, int]:
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
        # Create List with only ranges with unknowns
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
                if(self._query_value(draw)): # Allow for concrete evaluation?
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
        for base_solver, excluded_solver, unknown_sym_var in zip(self.base_solvers, self.excluded_solvers, self.unknown_sym_vars):
            solver: SolvingState = base_solver.copy() if not use_excluded else excluded_solver.copy()
            solver.constraints.append(SymbolicConstraint(unknown_sym_var, range[0], operator.ge))
            solver.constraints.append(SymbolicConstraint(unknown_sym_var, range[1], operator.le))
            solvability_results = solver.check_solvability(unknown_sym_var)
            if solvability_results[0]: # If solvable
                return solvability_results
        return (False, None) # Not solvable in any solver
    
    # Returns True feasible False infeasible
    def _query_value(self, value: int) -> bool:
        for base_solver, unknown_sym_var in zip(self.base_solvers, self.unknown_sym_vars):
            solver: SolvingState = base_solver.copy()
            solver.constraints.append(SymbolicConstraint(unknown_sym_var, value, operator.eq))
            solvable, _ = solver.check_solvability(unknown_sym_var)
            if solvable:
                return True
        return False
    
    # Record a feasible value as found
    def _record_feasible(self, value: int):
        if value in self.feasible_values:
            return
        self.feasible_values.add(value)
        if EXCLUDE_FOUND:
            for excluded_solver, unknown_sym_var in zip(self.excluded_solvers, self.unknown_sym_vars):
                excluded_solver.constraints.append(SymbolicConstraint(unknown_sym_var, value, operator.ne))

    def __str__(self):
        return "ERROR: To String for FVSs not Implemented yet"
    
class FeasibleValueSetProblematic(FeasibleValueSet):
    def __init__(self, base_solvers: List[SolvingState], output_summary: OutputSummary, possibility_range: Tuple[int,int] = INT_MIN_MAX):
        super().__init__(base_solvers, output_summary, possibility_range)

    def get_bounds(self) -> Tuple[int, float, int]:
        self._build_set()
        # Count
        feasible_count, unknown_count, total_count = self._count()
        homeless_feasible: List[int] = self._homeless_feasible()
        # Construct Weights
        frs_weights: List[float] = self._construct_weights(total_count, homeless_feasible)
        # Estimate
        feasiblity_estimate, valid_estimate = self._estimate_feasibility_validity(frs_weights, homeless_feasible)
        print(valid_estimate)
        ub = feasible_count + unknown_count
        pe = (feasible_count + unknown_count * feasiblity_estimate) * valid_estimate # TODO: Allow for pure concrete?
        lb = 0
        return (ub, pe, lb)
    
    def _estimate_feasibility_validity(self, frs_weights: List[float], homeless_feasible: List[int]) -> Tuple[float, float]:
        found_unknown: int = 0
        feasible_unknowns: int = 0
        feasibles_found: int = 0
        valid_feasibles: int = 0
        frs_plus = self.frs.copy()
        frs_plus.append(None)
        for fr in random.choices(frs_plus,frs_weights,k=DRAWS):
            if fr is not None: # Draw from Feasible Value Range
                draw = random.randint(fr.value_range[0], fr.value_range[1])
            else: # Draw from homeless feasible
                draw = random.choice(homeless_feasible)
            # Evaluate Draw
            feasible = draw in self.feasible_values
            if not feasible: # Unknown
                found_unknown += 1
                if(self._query_value(draw)): # Check if feasible
                    feasible_unknowns += 1
                    feasible = True
            if feasible: # Feasible
                feasibles_found += 1
                if(self._concrete_eval(draw)):
                    valid_feasibles += 1
        feasibility_estimate = 0 if found_unknown == 0 else feasible_unknowns / found_unknown
        return (feasibility_estimate, valid_feasibles / feasibles_found)
    
    def _concrete_eval(self, draw: int) -> bool:
        # Prep Capture
        # Stdout
        original_stdout = sys.stdout
        new_stdout = StringIO()
        sys.stdout = new_stdout
        # Stderr
        original_stderr = sys.stderr
        new_stderr = StringIO()
        sys.stderr = new_stderr
        # Capture
        return_value = self.output_summary.function(draw)
        # Get Capture
        captured_stdout = new_stdout.getvalue() # TODO: Check prints and errors
        new_stdout.close()
        captured_stderr = new_stderr.getvalue()
        new_stderr.close()
        # Restore
        sys.stdout = original_stdout
        sys.stderr = original_stderr

        return self._concrete_output_summary(return_value, captured_stdout, captured_stderr) == self.output_summary
    
    def _concrete_output_summary(self, return_value: Any, captured_stdout: str, captured_stderr: str) -> OutputSummary:
        prints: List[str] = captured_stdout.split('\n')[:-1]
        prints.reverse()
        errors: List[str] = captured_stderr.split('\n')[:-1]
        errors.reverse()
        return OutputSummary(self.output_summary.function, prints, errors,return_value)
    
    def _construct_weights(self, total_count: int, homeless_feasible: List[int]) -> List[float]:
        weights = super()._construct_weights(total_count)
        if total_count > 0:
            homeless_weight = len(homeless_feasible) / total_count
        else:
            homeless_weight = 1
        weights.append(homeless_weight)
        return weights

    def _homeless_feasible(self) -> List[int]:
        homeless = list(self.feasible_values.copy())
        for fr in self.frs:
            for x in fr.feasibility_set:
                homeless.remove(x)
        return homeless
    