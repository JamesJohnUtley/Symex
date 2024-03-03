import sys
import dis
import operator
from collections import deque
from dis import Instruction
from typing import List, Any, Dict
from z3 import *
from solving import SolvingState, SymbolicInstruction
from const_variables import *

class ReturnInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = 1
        ss.hunting_stack.append(self)
        self.out_var = ss.get_current_variable_iteration(OUT_CV)
    def execute(self, ss: SolvingState):
        print(f"Return {self.given_items[0]}")
        ss.solver.add(self.out_var == self.given_items[0])

class LoadFastInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        ss.avaliability_stack.append(ss.get_current_variable_iteration(self.instruction.argval))

class StoreFastInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = 1
        ss.hunting_stack.append(self)
        self.set_iteration = ss.get_current_variable_iteration(self.instruction.argval)
        ss.get_new_variable_iteration(self.instruction.argval)
    def execute(self, ss: SolvingState):
        ss.solver.add(self.set_iteration == self.given_items[0])

class ResumeInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        pass

class LoadConstInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        ss.avaliability_stack.append(self.instruction.argval)
        
BINARY_OPERATORS = {
        # 'POWER':    pow,
        '*': operator.mul,
        # '//': operator.floordiv,
        '/':  operator.truediv,
        # '%':   operator.mod,
        '+':      operator.add,
        '-': operator.sub,
        # 'SUBSCR':   operator.getitem,
        # 'LSHIFT':   operator.lshift,
        # 'RSHIFT':   operator.rshift,
        # 'AND':      operator.and_,
        # 'XOR':      operator.xor,
        # 'OR':       operator.or_,
    }

class BinaryOpInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = 2
        ss.hunting_stack.append(self)
        self.binop_var = ss.get_new_variable_iteration(BIN_CV)
    def execute(self, ss: SolvingState):
        if self.instruction.argrepr not in BINARY_OPERATORS.keys():
            print(f"ERROR: Binary Operator {self.instruction.argrepr} Undefined")
            return
        ss.solver.add(self.binop_var == BINARY_OPERATORS[self.instruction.argrepr](self.given_items[0], self.given_items[1]))
        ss.avaliability_stack.append(self.binop_var)


COMPARE_OPERATORS = [
    operator.lt,
    operator.le,
    operator.eq,
    operator.ne,
    operator.gt,
    operator.ge,
    lambda x, y: x in y,
    lambda x, y: x not in y,
    lambda x, y: x is y,
    lambda x, y: x is not y,
    lambda x, y: issubclass(x, Exception) and issubclass(x, y),
]

FLIP_OPERATORS = {
    0:5,1:4,2:3,3:2,4:1,5:0,6:7,7:6,8:9,9:8,10:10
}

class PopJumpForwardIfFalseInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = 3
        ss.hunting_stack.append(self)
    def execute(self, ss: SolvingState):
        comparator: function = None
        if ss.last_was_jump:
            comparator = COMPARE_OPERATORS[FLIP_OPERATORS[self.given_items[2]]]
        else:
            comparator = COMPARE_OPERATORS[self.given_items[2]]
        ss.solver.add(comparator(self.given_items[0], self.given_items[1]))

class PopJumpForwardIfTrueInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = 3
        ss.hunting_stack.append(self)
    def execute(self, ss: SolvingState):
        comparator: function = None
        if ss.last_was_jump:
            comparator = COMPARE_OPERATORS[self.given_items[2]]
        else:
            comparator = COMPARE_OPERATORS[FLIP_OPERATORS[self.given_items[2]]]
        ss.solver.add(comparator(self.given_items[0], self.given_items[1]))

class CompareOpInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        ss.avaliability_stack.append(self.instruction.arg)


symbolic_instructions = {
    'RETURN_VALUE': ReturnInstruction,
    'LOAD_FAST': LoadFastInstruction,
    'STORE_FAST': StoreFastInstruction,
    'RESUME': ResumeInstruction,
    'LOAD_CONST': LoadConstInstruction,
    'BINARY_OP': BinaryOpInstruction,
    'POP_JUMP_FORWARD_IF_FALSE': PopJumpForwardIfFalseInstruction,
    'POP_JUMP_FORWARD_IF_TRUE': PopJumpForwardIfTrueInstruction,
    'COMPARE_OP': CompareOpInstruction
}