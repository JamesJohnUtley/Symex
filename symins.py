import sys
import dis
import operator
from collections import deque
from dis import Instruction
from typing import List, Any, Dict
from z3 import *
from solving import SolvingState, SymbolicInstruction, SymbolicConstraint, SymbolicVariable
from const_variables import *
from extern_funcs import *

class ReturnInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = 1
        ss.hunting_stack.append(self)
        self.out_var: SymbolicVariable = ss.get_current_variable_iteration(OUT_CV)
    def execute(self, ss: SolvingState):
        print(f"Return {self.given_items[0]}")
        ss.constraints.append(SymbolicConstraint(self.out_var, self.given_items[0], operator.eq))

class LoadFastInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        ss.avaliability_stack.append(ss.get_current_variable_iteration(self.instruction.argval))

class StoreFastInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = 1
        ss.hunting_stack.append(self)
        self.set_iteration: SymbolicVariable = ss.get_current_variable_iteration(self.instruction.argval)
        ss.get_new_variable_iteration(self.instruction.argval)
    def execute(self, ss: SolvingState):
        ss.constraints.append(SymbolicConstraint(self.set_iteration, self.given_items[0], operator.eq))

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
        self.binop_var: SymbolicVariable = ss.get_new_variable_iteration(BIN_CV)
    def execute(self, ss: SolvingState):
        if self.instruction.argrepr not in BINARY_OPERATORS.keys():
            print(f"ERROR: Binary Operator {self.instruction.argrepr} Undefined")
            return
        ss.constraints.append(SymbolicConstraint(self.binop_var,self.given_items[0],operator.eq,BINARY_OPERATORS[self.instruction.argrepr],self.given_items[1]))
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
        ss.constraints.append(SymbolicConstraint(self.given_items[0], self.given_items[1], comparator))

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
        ss.constraints.append(SymbolicConstraint(self.given_items[0],self.given_items[1],comparator))

class CompareOpInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        ss.avaliability_stack.append(self.instruction.arg)

class PopTopInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = 1
        ss.hunting_stack.append(self)
    def execute(self, ss: SolvingState):
        pass

class CallInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        pass

class PreCallInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        self.requested_items = self.instruction.argval + 1
        ss.hunting_stack.append(self)
    def execute(self, ss: SolvingState):
        if self.given_items[0] in external_functions_execs.keys():
            external_functions_execs[self.given_items[0]](list(self.given_items)[1:], ss)
        else:
            print(f"ERROR: EXEC EXTERNAL FUNCTION {self.given_items[0]} NOT IMPLEMENTED", file=sys.stderr)

class LoadGlobalInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        ss.avaliability_stack.append(self.instruction.argval)

class JumpForwardInstruction(SymbolicInstruction):
    def load(self, ss: SolvingState):
        pass

symbolic_instructions = {
    'RETURN_VALUE': ReturnInstruction,
    'LOAD_FAST': LoadFastInstruction,
    'STORE_FAST': StoreFastInstruction,
    'RESUME': ResumeInstruction,
    'LOAD_CONST': LoadConstInstruction,
    'BINARY_OP': BinaryOpInstruction,
    'POP_JUMP_FORWARD_IF_FALSE': PopJumpForwardIfFalseInstruction,
    'POP_JUMP_FORWARD_IF_TRUE': PopJumpForwardIfTrueInstruction,
    'COMPARE_OP': CompareOpInstruction,
    'POP_TOP': PopTopInstruction,
    'CALL': CallInstruction,
    'PRECALL': PreCallInstruction,
    'LOAD_GLOBAL': LoadGlobalInstruction,
    'JUMP_FORWARD': JumpForwardInstruction
}