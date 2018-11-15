import time
from .behavior import State, Behavior

class Delay(Behavior):
    """Delay for 'duration' seconds then return success"""
    __slots__ = ("duration", "start_time", "completed")
    def __init__(self, duration):
        self.duration = duration
    def start(self):
        self.start_time = time.time()
    def update(self):
        if (time.time() - self.start_time) >= self.duration:
            return State.Success
        return State.Running

class RateLimit(Behavior):
    """Call child task at most every 'duration' seconds,
return 'Running' otherwise"""
    __slots__ = ("duration", "start_time", "child", "completed")
    def __init__(self, duration, child):
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