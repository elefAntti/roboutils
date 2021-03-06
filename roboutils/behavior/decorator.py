from .behavior import State, Behavior

class Repeat(Behavior):
    """Repeat child task forever"""
    __slots__ = ("child", "completed")
    def __init__(self, child):
        self.child = child
    def start(self):
        self.child.start()
    def update(self):
        status = self.child.update()
        if status != State.Running:
            self.child.start()
        return State.Running

class RepeatUntilFail(Behavior):
    """Repeat child task until it fails"""
    __slots__ = ("child", "completed")
    def __init__(self, child):
        self.child = child
    def start(self):
        self.child.start()
    def update(self):
        status = self.child.update()
        if status == State.Failure:
            return State.Failure
        if status == State.Success:
            self.child.start()
        return State.Running

class RepeatUntilSuccess(Behavior):
    """Repeat child task until it succeeds"""
    __slots__ = ("child", "completed")
    def __init__(self, child):
        self.child = child
    def start(self):
        self.child.start()
    def update(self):
        status = self.child.update()
        if status == State.Success:
            return State.Success
        if status == State.Failure:
            self.child.start()
        return State.Running


class Invert(Behavior):
    """Execute child task, but revert it's success when it completes"""
    __slots__ = ("child", "completed")
    def __init__(self, child):
        self.child = child
    def start(self):
        self.child.start()
    def update(self):
        status = self.child.update()
        if status == State.Failure:
            return State.Success
        if status == State.Success:
            return State.Failure
        return State.Running

class Succeed(Behavior):
    """Execute child task, but always return success when it's complete"""
    __slots__ = ("child", "completed")
    def __init__(self, child):
        self.child = child
    def start(self):
        self.child.start()
    def update(self):
        status = self.child.update()
        if status == State.Failure:
            return State.Success
        if status == State.Success:
            return State.Success
        return State.Running

class Fail(Behavior):
    """Execute child task, but always return failure when it's complete"""
    __slots__ = ("child", "completed")
    def __init__(self, child):
        self.child = child
    def start(self):
        self.child.start()
    def update(self):
        status = self.child.update()
        if status == State.Failure:
            return State.Failure
        if status == State.Success:
            return State.Failure
        return State.Running
