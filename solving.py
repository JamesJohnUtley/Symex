from collections import deque
from dis import Instruction
from z3 import *
from typing import Dict, List, Any, Callable, Tuple
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
        print("WARNING: COPY SYMBOLIC INSTRUCTION", file=sys.stderr)
        print(self.instruction, file=sys.stderr)
        copied_given = self.given_items.copy()
        return self.__class__(self.instruction,self.requested_items,copied_given)
    
    def is_tainted(self):
        return False

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

    def add_connections(self, var_connections: dict[str, list[str]], type_seeds: list[tuple[str,type]]):
        symbolic = []
        nonsymbolic = []
        symbolic.append(self.out_v) if type(self.out_v) is SymbolicVariable else nonsymbolic.append(self.out_v)
        symbolic.append(self.in_v0) if type(self.in_v0) is SymbolicVariable else nonsymbolic.append(self.in_v0)
        symbolic.append(self.in_v1) if type(self.in_v1) is SymbolicVariable else nonsymbolic.append(self.in_v1)
        for i in range(len(symbolic)):
            for j in range(len(symbolic)):
                if i != j:
                    var_connections[symbolic[i].name].append(symbolic[j].name)
        # Find Type
        needed_type = None
        for ns in nonsymbolic:
            if ns is not None:
                if needed_type is not None:
                    if type(ns) != needed_type:
                        print(f"ERROR: CONSTRAINT HAS CONFLICTING TYPES", sys.stderr)
                        return
                else:
                    needed_type = type(ns)
        # Set symbolic as seeds if there is a type
        if needed_type is not None:
            for s in symbolic:
                type_seeds.append((s.name, needed_type))


    def gen_solver_constraint(self, solver: Solver, made_vars: dict[str, Any]):
        out_v = self.out_v if type(self.out_v) is not SymbolicVariable else made_vars[self.out_v.name]
        in_v0 = self.in_v0 if type(self.in_v0) is not SymbolicVariable else made_vars[self.in_v0.name]
        if self.in_op is None:
            solver.add(self.comparator(out_v, in_v0))
        else:
            in_v1 = self.in_v1 if type(self.in_v1) is not SymbolicVariable else made_vars[self.in_v1.name]
            solver.add(self.comparator(out_v, self.in_op(in_v0,in_v1)))

def gen_solver_var(name: str, var_type: type) -> Any:
    if var_type is str:
        return String(name)
    if var_type is int:
        return Int(name)
    return Int(name)

class SolvingState:
    def __init__(self,
                 hunting_stack: deque[SymbolicInstruction] = None,
                 avaliability_stack: deque = None,
                 constraints: List[SymbolicConstraint] = None,
                 symbolic_variables: Dict[str,List[Any]] = None,
                 specialized_variables_count: Dict[str,int] = None,
                 unstored_variables: set[str] = None,
                 output = None,
                 prints: List[str] = None,
                 errors: List[str] = None
                 ):
        self.hunting_stack: deque[SymbolicInstruction] = hunting_stack if hunting_stack is not None else deque() # Stack of instructions and requested variables
        self.avaliability_stack: deque = avaliability_stack if avaliability_stack is not None else deque() # Stack of symbols and constants
        self.constraints: List[SymbolicConstraint] = constraints if constraints is not None else []
        self.symbolic_variables: Dict[str,List[Any]] = symbolic_variables if symbolic_variables is not None else {}
        self.unstored_variables: set = unstored_variables if unstored_variables is not None else set()
        self.specialized_variables_count: Dict[str,int] = specialized_variables_count if specialized_variables_count is not None else None
        if self.specialized_variables_count is None:
            self.specialized_variables_count = {}
            self.specialized_variables_count[PRINT_CV] = 0
            self.specialized_variables_count[ERROR_CV] = 0
        self.last_was_jump = False
        # Set out
        if output != None:
            out_var = self.get_new_variable_iteration(OUT_CV)
            self.constraints.append(SymbolicConstraint(int(output),out_var,operator.eq))
        # Set Special Variables
        if prints != None:
            for print_output in prints:
                print_var = self.get_new_variable_iteration(PRINT_CV)
                self.constraints.append(SymbolicConstraint(print_output,print_var,operator.eq))
        if errors != None:
            for error_output in errors:
                error_var = self.get_new_variable_iteration(ERROR_CV)
                self.constraints.append(SymbolicConstraint(error_output,error_var,operator.eq))

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
        copied_specialized_vars_count: Dict[str,int] = {}
        for var in self.specialized_variables_count.keys():
            copied_specialized_vars_count[var] = self.specialized_variables_count[var]
        return SolvingState(copied_hunting_stack,
                            self.avaliability_stack.copy(),
                            copied_constraints,
                            copied_symbolic_variables,
                            copied_specialized_vars_count,
                            self.unstored_variables.copy())
    
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
    
    def get_specialized_variable_iteration(self, name: str):
        sym_var = None
        # Check that actually exists
        if name not in self.symbolic_variables.keys():
            sym_var = self.get_new_variable_iteration(name)
        elif self.specialized_variables_count[name] >= len(self.symbolic_variables[name]):
            sym_var = self.get_new_variable_iteration(name)
        else:
            sym_var = self.symbolic_variables[name][self.specialized_variables_count[name]]
        self.specialized_variables_count[name] += 1
        return sym_var
    
    def make_var_of_type(self, seed_node: str, seed_type: type, graph: dict[str, list[str]], typed_vars: dict[str,type]):
        if seed_node in typed_vars.keys():
            # Hit before check
            if typed_vars[seed_node] == seed_type:
                # Fine
                return
            else:
                print(f"ERROR: TYPE CONFLICT", file=sys.stderr)
                return
        else:
            # Unseen
            typed_vars[seed_node] = seed_type
            for neighbor in graph[seed_node]:
                self.make_var_of_type(neighbor, seed_type, graph, typed_vars)

    def check_solvability(self, var_to_grab: Any = None) -> Tuple[bool, Any]:
        # Construct Type Graph
        type_seeds: list[tuple[str,type]] = []
        type_graph: dict[str, list[str]] = {}
        for var_iterations in self.symbolic_variables.values():
            for v_iter in var_iterations:
                type_graph[v_iter.name] = []
        for c in self.constraints:
            c.add_connections(type_graph, type_seeds)
        # Through Type Graph
        typed_vars: dict[str,type] = {}
        for seed, seed_type in type_seeds:
            self.make_var_of_type(seed,seed_type,type_graph,typed_vars)
        # print(type_graph)
        # print(typed_vars)

        made_vars: dict[str,Any] = {}
        for var_iterations in self.symbolic_variables.values():
            for v_iter in var_iterations:
                made_vars[v_iter.name] = gen_solver_var(v_iter.name,typed_vars.get(v_iter.name, None))

        solver = Solver()
        for c in self.constraints:
            c.gen_solver_constraint(solver, made_vars)
        # if var_to_grab is None:
        #     print(solver.assertions())
        satisfiability = solver.check()
        if satisfiability == sat and var_to_grab is not None:
            model = solver.model()
            # print(model)
            value: int = model[made_vars[var_to_grab.name]].as_long()
            return (satisfiability == sat, value)
        else:
            return (satisfiability == sat, None)