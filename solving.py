from collections import deque
from dis import Instruction
from z3 import *
from typing import Dict, List, Any, Callable
from const_variables import *
import operator


class SymbolicInstruction:
    def __init__(self, instruction: Instruction, requested_items: int = 0, given_items: deque = None) -> None:
        self.instruction: Instruction = instruction
        self.requested_items: int = requested_items
        if given_items is None:
            self.given_items: deque = deque()
        else:
            self.given_items: deque = given_items

    def load(self, ss):
        print("Error: SymbolicInstruction Not Implemented",file=sys.stderr)
    def execute(self, ss):
        print(self.instruction,file=sys.stderr)
        print(self.given_items,file=sys.stderr)
        print("Error: SymbolicInstruction Not Implemented",file=sys.stderr)
    def copy(self):
        print("COPY")
        copied_given = self.given_items.copy()
        return self.__class__(self.instruction,self.requested_items,copied_given)
    
class SymbolicVariable:
    def __init__(self, name):
        self.name = name

class SymbolicConstraint:
    def __init__(self, out_v, in_v0, comparator: Callable[[Any, Any], None], in_op: Callable[[Any, Any], Any] = None, in_v1 = None):
        self.out_v = out_v
        self.in_v0 = in_v0
        self.comparator: Callable[[Any, Any], None] = comparator
        self.in_op = in_op
        self.in_v1 = in_v1

    def gen_solver_constraint(self, solver: Solver, made_vars: dict[str, Any]):
        out_v = self.out_v if type(self.out_v) is not SymbolicVariable else made_vars[self.out_v.name]
        in_v0 = self.in_v0 if type(self.in_v0) is not SymbolicVariable else made_vars[self.in_v0.name]
        if self.in_op is None:
            solver.add(self.comparator(out_v, in_v0))
        else:
            in_v1 = self.in_v1 if type(self.in_v1) is not SymbolicVariable else made_vars[self.in_v1.name]
            solver.add(self.comparator(out_v, self.in_op(in_v0,in_v1)))

class SolvingState:
    def __init__(self,
                 hunting_stack: deque[SymbolicInstruction] = None,
                 avaliability_stack: deque = None,
                 constraints: List[SymbolicConstraint] = None,
                 symbolic_variables: Dict[str,List[Any]] = None,
                 output = None
                 ):
        self.hunting_stack: deque[SymbolicInstruction] = hunting_stack if hunting_stack is not None else deque() # Stack of instructions and requested variables
        self.avaliability_stack: deque = avaliability_stack if avaliability_stack is not None else deque() # Stack of symbols and constants
        self.constraints: List[SymbolicConstraint] = constraints if constraints is not None else []
        self.symbolic_variables: Dict[str,List[Any]] = symbolic_variables if symbolic_variables is not None else {}
        self.last_was_jump = False
        # Set out
        if output != None:
            out_var = self.get_new_variable_iteration(OUT_CV)
            self.constraints.append(SymbolicConstraint(output,out_var,operator.eq))

    def copy(self):
        copied_hunting_stack: deque[SymbolicInstruction] = deque()
        for x in self.hunting_stack:
            copied_hunting_stack.append(x.copy())
        copied_constraints = []
        for c in self.constraints:
            copied_constraints.append(c)
        copied_symbolic_variables: Dict[str, List[Any]] = {}
        for name in self.symbolic_variables.keys():
            copied_symbolic_variables[name] = self.symbolic_variables[name].copy()
        return SolvingState(copied_hunting_stack,self.avaliability_stack.copy(),copied_constraints,copied_symbolic_variables)
    
    def resolve_instructions(self):
        # Check if instructions are avaliable for execution
        while len(self.avaliability_stack) > 0 and len(self.hunting_stack) > 0:
            # Consume
            self.hunting_stack[-1].given_items.appendleft(self.avaliability_stack.pop())
            self.hunting_stack[-1].requested_items -= 1
            if self.hunting_stack[-1].requested_items == 0:
                filled_hunter: SymbolicInstruction = self.hunting_stack.pop()
                filled_hunter.execute(self)

    def get_new_variable_iteration(self, name: str) -> Any:
        if name not in self.symbolic_variables.keys():
            self.symbolic_variables[name] = []
        # print(f"NEW VAR: {name}@{len(symbolic_variables[name])}", file=sys.stderr)
        new_sym = SymbolicVariable(f"{name}@{len(self.symbolic_variables[name])}")
        self.symbolic_variables[name].append(new_sym)
        return new_sym

    def get_current_variable_iteration(self, name: str) -> Any:
        if name not in self.symbolic_variables.keys():
            return self.get_new_variable_iteration(name)
        return self.symbolic_variables[name][len(self.symbolic_variables[name]) - 1]
    
    def check_solvability(self) -> bool:
        made_vars: dict[str,Any] = {}
        for var_iterations in self.symbolic_variables.values():
            for v_iter in var_iterations:
                made_vars[v_iter.name] = Int(v_iter.name)
        solver = Solver()
        for c in self.constraints:
            c.gen_solver_constraint(solver, made_vars)
        print(solver.assertions())
        satisfiability = solver.check()
        # if satisfiability == sat:
        #     print(solver.model())
        return satisfiability == sat