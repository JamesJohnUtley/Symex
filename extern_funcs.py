from typing import Any, List
from solving import SolvingState, SymbolicConstraint, SymbolicVariable
from const_variables import *
import operator

def printExtern(items: List[Any], ss: SolvingState):
    print_var: SymbolicVariable = ss.get_new_variable_iteration(PRINT_CV)
    ss.constraints.append(SymbolicConstraint(print_var,items[0],operator.eq))
    ss.avaliability_stack.append(None)

def valueErrorExtern(items: List[Any], ss: SolvingState):
    error_var: SymbolicVariable = ss.get_new_variable_iteration(ERROR_CV)
    ss.constraints.append(SymbolicConstraint(error_var,items[0],operator.eq))
    ss.avaliability_stack.append(None)

external_functions_execs = {
    'print': printExtern,
    'ValueError': valueErrorExtern
}
