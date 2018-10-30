from enum import Enum

class State(Enum):
    Running = 0
    Success = 1
    Failure = 2

class ParallelAny:
    """
Behavior tree node that executes the child tasks in parallel
Fails when all of the children fail,
Succeeds as soon as one succeeds: does not evaluate the rest
of the children for that update.
    """
    def __init__(self, *children):
        self.children = children
    def start(self):
        for child in self.children:
            child.completed = False
            child.start()
    def update(self):
        running = False
        for child in self.children:
            if not child.completed:
                running = True
                status = child.update()
                if status == State.Success:
                    return State.Success
                if status == State.Failure:
                    child.completed = True
        return State.Running if running else State.Failure

class ParallelAll:
    """
Behavior tree node that executes the child tasks in parallel
Completes when all of the children are complete,
Fails as soon as one fails: does not evaluate the rest of the children
for that update.
    """
    def __init__(self, *children):
        self.children = children
    def start(self):
        for child in self.children:
            child.completed = False
            child.start()
    def update(self):
        running = False
        for child in self.children:
            if not child.completed:
                running = True
                status = child.update()
                if status == State.Failure:
                    return State.Failure
                if status == State.Success:
                    child.completed = True
        return State.Running if running else State.Success

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
def condition(fcn):
    def factory(*args):
        return Condition(fcn, *args)
    return factory
