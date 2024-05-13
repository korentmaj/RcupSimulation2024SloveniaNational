"""
    SERS TEAM
    state_machine.py
"""

from typing import Callable


class StateMachine:
    def __init__(self, initial_state, function_on_change_state=lambda:None):
        self.state = initial_state
        self.current_function = lambda:None

        self.change_state_function = function_on_change_state

        self.state_functions = {}
        self.allowed_state_changes = {}
        self.possible_states = set()

    def create_state(self, name: str, function: Callable, possible_changes=None):
        if possible_changes is None:
            possible_changes = set()
        if name in self.possible_states:
            raise ValueError("Failed to create new state. State already exists.")
        self.possible_states.add(name)
        self.state_functions[name] = function
        self.allowed_state_changes[name] = possible_changes
        if name == self.state:
            self.current_function = self.state_functions[self.state]

    def change_state(self, new_state):
        if new_state not in self.possible_states:
            raise ValueError("Can't change state. New state doesn't exist.")
        
        if new_state in self.allowed_state_changes[self.state]:
            self.change_state_function()
            self.state = new_state
            self.current_function = self.state_functions[self.state]
            print("[STATE-MACHINE] Changed to:", new_state)

        else:
            print(f"WARNING: Can't change to state {new_state}. New state is not in the possible changes for {self.state}.")
        return True

    def check_state(self, state):
        return self.state == state
    
    def run(self):
        return self.current_function(self.change_state)
