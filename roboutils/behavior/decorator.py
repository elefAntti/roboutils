from .behavior import State

class Repeat:
    def __init__(self, child):
        self.child = child
    def start(self):
        self.child.start()
    def update(self):
        status = self.child.update()
        if status != State.Running:
            self.child.start()
        return State.Running

class RepeatUntilFail:
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

class RepeatUntilSuccess:
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


class Invert:
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

class Succeed:
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

class Fail:
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
