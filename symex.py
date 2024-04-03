import dis
from dis import Instruction
import sys
from typing import List, Tuple, Set
from z3 import *
from collections import deque
import argparse

from tests import *
from symins import *
from solving import SolvingState, SymbolicInstruction
from FVSs import FeasibleValueSet


follow_lead_opnames = ['POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE', 'JUMP_FORWARD']
conditional_jump_opnames = ['POP_JUMP_FORWARD_IF_FALSE', 'POP_JUMP_FORWARD_IF_TRUE']

MAX_DEPTH: int = 10

class InstructionBlock:
    def __init__(self, offset: int, offset_instructions: int, id: int):
        self.instructions: List[Instruction] = []
        self.offset: int = offset
        self.offset_instructions: int = offset_instructions
        self.id: int = id
        self.successors: List[InstructionBlock] = []
        self.predecessors: List[InstructionBlock] = []
        self.following_block = None
        self.end_block = False

    def __str__(self):
        return f"{self.id}"

    def add_successor(self, successor):
        self.successors.append(successor)
        successor.predecessors.append(self)

    def set_end_block(self):
        self.end_block = True
        

def main(args):
    print(f"BREAKING: {args.function_name}")
    # Breakdown Arguments
    if args.bre:
        for x in dis.get_instructions(globals()[args.function_name]):
            print(x)
        return 0
    if args.dis:
        dis.dis(globals()[args.function_name])
        return 0
    if args.run:
        print(f"Out: {globals()[args.function_name]()}")
        return 0
    
    # Set Prints
    prints = None
    if args.prints != None:
        prints = []
        with open(args.prints) as prints_file:
            for line in prints_file:
                prints.append(line.strip())
        prints.reverse()
    errors = None
    if args.errors != None:
        errors = []
        with open(args.errors) as errors_file:
            for line in errors_file:
                errors.append(line.strip())
        errors.reverse()

    instructions: List[Instruction] = []
    for x in dis.get_instructions(globals()[args.function_name]):
        instructions.append(x)

    blocks, end_blocks, jump_edges = construct_cfg(instructions)
    if args.cf:
        for x in blocks.values():
            print(f"{x.id} -> {[y.id for y in x.successors]}")
        for x in blocks.values():
            print(f"{[y.id for y in x.predecessors]} -> {x.id}")
        print(f"{[x.id for x in end_blocks]}")
        return 0

    for end_block in end_blocks:
        build_paths(end_block, jump_edges, base_solve_state=SolvingState(output=args.output, prints=prints, errors=errors))
        
def build_paths(last_block: InstructionBlock, jump_edges: Set[Tuple[int,int]], depth: int = 0, prefix_path: List[InstructionBlock] = [], base_solve_state: SolvingState = None):
    base_solve_state = base_solve_state if base_solve_state is not None else SolvingState()
    if depth >= MAX_DEPTH:
        return
    # Construct full path
    path = prefix_path + [last_block]
    print(f"{[x.id for x in path]}")

    # Attempt to solve
    if(traverse_block(last_block, base_solve_state)):
        if len(last_block.predecessors) != 0: 
            for neighbor in last_block.predecessors:
                new_ss: SolvingState = base_solve_state.copy()
                new_ss.last_was_jump = (neighbor.id, last_block.id) in jump_edges
                build_paths(neighbor, jump_edges, depth +  1, path, new_ss)
        else:
            print("Find Feasible Value Set")
            fvs = FeasibleValueSet(base_solve_state)

def construct_cfg(instructions: List[Instruction]) -> Tuple[Dict[int,InstructionBlock], List[InstructionBlock], Set[Tuple[int,int]]]:
    # Construct Nodes
    follows_jump = True
    blocks: Dict[int, InstructionBlock] = {}
    current_block: InstructionBlock = None
    block_id = 0
    for i in range(len(instructions)):
        #  Create New Leaders
        if follows_jump or instructions[i].is_jump_target:
            prev_block = current_block
            current_block = InstructionBlock(instructions[i].offset, i, block_id)
            if prev_block is not None:
                prev_block.following_block = current_block
            block_id += 1
            blocks[current_block.id] = current_block
        # Add instructions to block
        current_block.instructions.append(instructions[i])
        #  Following is Leader
        if instructions[i].opname in follow_lead_opnames:
            follows_jump = True
        else:
            follows_jump = False

    end_blocks: List[InstructionBlock] = []
    jump_edges: Set[Tuple[int, int]] = set() # Forward edges that are jumps
    # Construct Edges
    for x in blocks.values():
        last_instruction = x.instructions[len(x.instructions) - 1]
        if last_instruction.opname in conditional_jump_opnames:
            # Two Successors
            x.add_successor(x.following_block)
            jumped_block = find_block_offset(last_instruction.argval, blocks)
            x.add_successor(jumped_block)
            jump_edges.add((x.id,jumped_block.id))
        elif last_instruction.opname == 'RETURN_VALUE':
            # End Block
            x.set_end_block()
            end_blocks.append(x)
        elif last_instruction.opname == 'JUMP_FORWARD':
            # Unconditional Jump
            jumped_block = find_block_offset(last_instruction.argval, blocks)
            x.add_successor(jumped_block)
        else:
            # One Successor
            x.add_successor(x.following_block)

    return (blocks, end_blocks, jump_edges)

# Returns satisfiability
def traverse_block(block: InstructionBlock, ss: SolvingState = SolvingState()) -> bool:
    instructions = block.instructions
    for i in range(len(instructions) - 1, -1, -1):
        # print(instructions[i].opname)
        if instructions[i].opname not in symbolic_instructions.keys():
            print(f"{instructions[i].opname} not implemented", file=sys.stderr)
            return
        symins: SymbolicInstruction = symbolic_instructions[instructions[i].opname](instructions[i])
        symins.load(ss)
        ss.resolve_instructions()
    solution, _ = ss.check_solvability()
    if solution:
        # Get the model
        # model = ss.solver.model()
        # Print the values of the variables
        # print(model)
        print("Satisfiable")
    else:
        print("Unsatisfiable")
    return solution
    
def find_block_offset(offset: int, blocks: Dict[int,InstructionBlock]) -> InstructionBlock:
    for x in blocks.values():
        if offset == x.offset:
            return x
    print(f"No Block With Offset Found! Offset: {offset}", sys.stderr)
    return None

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('function_name', type=str,
                        help='Function to run on')
    parser.add_argument('-d', '--dis', action='store_true', help='Print out the dissassembled form of the function')
    parser.add_argument('-b', '--bre', action='store_true', help='Print out the dissassembled instruction objects of the function')
    parser.add_argument('-r', '--run', action='store_true', help='Run the function')
    parser.add_argument('-f', '--cf', action='store_true', help='Print out the control flow of the function')
    parser.add_argument('-o', '--output', help='Add a requirement for output to be a certain value', required=False)
    parser.add_argument('-p', '--prints', help='Add a requirement for prints to be equivalent to a certain file', required=False)
    parser.add_argument('-e', '--errors', help='Add a requirement for errors to be equivalent to a certain file', required=False)
    args = parser.parse_args()
    main(args)
    sys.exit(0)

