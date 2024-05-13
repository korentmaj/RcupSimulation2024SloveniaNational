"""
    SERS TEAM
    sequencer.py
"""

from debug.settings import SHOW_DEBUG


class Sequencer:
    def __init__(self, reset_function=None):
        self.line_identifier = 0
        self.line_pointer = 1
        self.done = False
        self.reset_function = reset_function

    def reset_sequence(self):
        if self.reset_function is not None:
            self.reset_function()
        self.line_pointer = 1
        if SHOW_DEBUG:
            print("[SEQUENCER] Resetting sequence!")

    def seq_reset_sequence(self):
        if self.check():
            self.reset_sequence()
            
            return True
        return False

    def start_sequence(self):
        self.line_identifier = 0
        self.done = False

    def check(self):
        self.done = False
        self.line_identifier += 1
        return self.line_identifier == self.line_pointer

    def next_seq(self):
        self.line_pointer += 1
        self.done = True

    def seq_done(self):
        return self.done

    def simple_event(self, function=None, *args, **kwargs):
        if self.check():
            if function is not None:
                function(*args, **kwargs)
            self.next_seq()
            return True
        return False

    def complex_event(self, function, *args, **kwargs):
        if self.check():
            if function(*args, **kwargs):
                self.next_seq()
                return True
        return False
    
    def make_simple_event(self, function):
        def event(*args, **kwargs):
            if self.check():
                function(*args, **kwargs)
                self.next_seq()
                return True
            return False
        return event

    def make_complex_event(self, function):
        def event(*args, **kwargs):
            if self.check():
                if function(*args, **kwargs):
                    self.next_seq()
                    return True
            return False
        return event
