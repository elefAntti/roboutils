from enum import Enum

class State(Enum):
    Running = 0
    Success = 1
    Failure = 2

#Executes the child tasks in parallel
#Completes when al the children are complete or
#When first one is complete (if to_first_success = True is passed)
class Parallel:
    def __init__(self, *children, **kwargs):
        self.children = children
        self.completed = [False for child in self.children]
        if "to_first_success" in kwargs:
            self.to_first_success = kwargs["to_first_success"]
        else:
            self.to_first_success = False
    def start(self):
        for child in self.children:
            child.start()
        self.completed = [False for child in self.children]
    def update(self):
        failed = False
        succeeded = False
        running = False
        for idx in range(len(self.children)):
            child = self.children[idx]
            if not self.completed[idx]:
                status = child.update()
                if status == State.Success:
                    succeeded = True
                    self.completed[idx] = True
                if status == State.Failure:
                    failed = True
                    self.completed[idx] = True
                if status == State.Running:
                    running = True
        if failed:
            return State.Failure
        if succeeded and self.to_first_success:
            return State.Success
        if running:
            return State.Running
        else:
            return State.Success

#Executes children in order until all of them complete or first one fails
class Sequence:
    def __init__(self, *children):
        self.children = children
    def start(self):
        self.currentChild = 0
        self.children[self.currentChild].start()
    def update(self):
        if self.currentChild >= len(self.children):
            return State.Success
        state = self.children[self.currentChild].update()
        if state == State.Success:
            self.currentChild += 1
            if self.currentChild >= len(self.children):
                return State.Success
            self.children[self.currentChild].start()
        elif state == State.Failure:
            return State.Failure
        return State.Running

#Executes children in order until all of them fail or first one succeeds
class Selector:
    def __init__(self, *children):
        self.children = children
    def start(self):
        self.currentChild = 0
        self.children[self.currentChild].start()
    def update(self):
        if self.currentChild >= len(self.children):
            return State.Failure
        state = self.children[self.currentChild].update()
        if state == State.Failure:
            self.currentChild += 1
            if self.currentChild >= len(self.children):
                return State.Failure
            self.children[self.currentChild].start()
        elif state == State.Success:
            return State.Success
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


class Task:
    def __init__(self, fcn, *args):
        self.args = args
        self.fcn = fcn
    def start(self):
        pass
    def update(self):
        try:
            status = self.fcn(*self.args)
            if status == True:
                return State.Success
            return State.Running
        except:
            return State.Failure

#A decorator to construct a task from any function
# - If function throws, task fails
# - If function returns true, it succeeds
def task(fcn):
    def factory(*args):
        return Task(fcn, *args)
    return factory

class Condition:
    def __init__(self, fcn, *args):
        self.args = args
        self.fcn = fcn
    def start(self):
        pass
    def update(self):
        status = self.fcn(*self.args)
        if status == True:
            return State.Success
        if status == False:
            return State.Failure
        return State.Running


#A decorator to construct a condition from any function
# - If function returns false, condition fails
# - If function returns true, it succeeds
def task(fcn):
    def factory(*args):
        return Condition(fcn, *args)
    return factory
