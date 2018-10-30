import time
from .behavior import State

class Delay:
    def __init__(self, duration):
        self.duration = duration
    def start(self):
        self.start_time = time.time()
    def update(self):
        if (time.time() - self.start_time) >= self.duration:
            return State.Success
        return State.Running

class RateLimit:
    def __init__(self, child, duration):
        self.duration = duration
        self.child = child
    def start(self):
        self.start_time = time.time()
        self.child.start()
    def update(self):
        if (time.time() - self.start_time) >= self.duration:
            self.start_time = time.time()
            return self.child.update()
        return State.Running