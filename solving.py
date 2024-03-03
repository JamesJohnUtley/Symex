from collections import deque
from dis import Instruction
from z3 import *
from typing import Dict, List, Any
from const_variables import *


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
    
class SolvingState:
    def __init__(self,
                 hunting_stack: deque[SymbolicInstruction] = None,
                 avaliability_stack: deque = None,
                 solver = None,
                 symbolic_variables: Dict[str,List[Any]] = None,
                 output = None
                 ):
        self.hunting_stack: deque[SymbolicInstruction] = hunting_stack if hunting_stack is not None else deque() # Stack of instructions and requested variables
        self.avaliability_stack: deque = avaliability_stack if avaliability_stack is not None else deque() # Stack of symbols and constants
        self.solver = solver if solver is not None else Solver()
        self.symbolic_variables: Dict[str,List[Any]] = symbolic_variables if symbolic_variables is not None else {}
        self.last_was_jump = False
        # Set out
        if output != None:
            out_var = self.get_new_variable_iteration(OUT_CV)
            self.solver.add(output == out_var)

    def copy(self):
        copied_hunting_stack: deque[SymbolicInstruction] = deque()
        for x in self.hunting_stack:
            copied_hunting_stack.append(x.copy())
        copied_solver = Solver()
        for c in self.solver.assertions():
            copied_solver.add(c)
        copied_symbolic_variables: Dict[str, List[Any]] = {}
        for name in self.symbolic_variables.keys():
            copied_symbolic_variables[name] = self.symbolic_variables[name].copy()
        return SolvingState(copied_hunting_stack,self.avaliability_stack.copy(),copied_solver,copied_symbolic_variables)
    
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
        new_sym = Int(f"{name}@{len(self.symbolic_variables[name])}")
        self.symbolic_variables[name].append(new_sym)
        return new_sym

    def get_current_variable_iteration(self, name: str) -> Any:
        if name not in self.symbolic_variables.keys():
            return self.get_new_variable_iteration(name)
        return self.symbolic_variables[name][len(self.symbolic_variables[name]) - 1]