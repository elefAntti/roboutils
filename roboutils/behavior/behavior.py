from enum import Enum
from functools import wraps
from typing import List

class State(Enum):
    Running = 0
    Success = 1
    Failure = 2

class Behavior:
    __slots__ = ("completed")
    def start(self) -> None:
        pass
    def update(self) -> State:
        return State.Success

class ParallelAny(Behavior):
    """
Behavior tree node that executes the child tasks in parallel
Fails when all of the children fail,
Succeeds as soon as one succeeds: does not evaluate the rest
of the children for that update.
    """
    __slots__ = ("children", "completed")
    def __init__(self, *children: List[Behavior]):
        self.children = children
    def start(self) -> None:
        for child in self.children:
            child.completed = False
            child.start()
    def update(self) -> State:
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


class ParallelAll(Behavior):
    """
Behavior tree node that executes the child tasks in parallel
Completes when all of the children are complete,
Fails as soon as one fails: does not evaluate the rest of the children
for that update.
    """
    __slots__ = ("children", "completed")
    def __init__(self, *children: List[Behavior]):
        self.children = children
    def start(self) -> None:
        for child in self.children:
            child.completed = False
            child.start()
    def update(self) -> State:
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

class Sequence(Behavior):
    """Executes children in order until all of them complete or first one fails"""
    __slots__ = ("children", "currentChild", "completed")
    def __init__(self, *children: List[Behavior]):
        self.children = children
    def start(self) -> None:
        self.currentChild = 0
        self.children[self.currentChild].start()
    def update(self) -> State:
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
    def append(self, task: Behavior):
        self.children = (*self.children, task)



class Selector(Behavior):
    """Executes children in order until all of them fail or first one succeeds"""
    __slots__ = ("children", "currentChild", "completed")
    def __init__(self, *children: List[Behavior]):
        self.children = children
    def start(self) -> None:
        self.currentChild = 0
        self.children[self.currentChild].start()
    def update(self) -> State:
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


class Condition(Behavior):
    __slots__ = ("fcn", "args", "completed")
    def __init__(self, fcn, *args):
        self.args = args
        self.fcn = fcn
    def start(self) -> None:
        pass
    def update(self) -> State:
        status = self.fcn(*self.args)
        if status == True:
            return State.Success
        if status == False:
            return State.Failure
        return State.Running


def condition(fcn):
    """A decorator to construct a condition from any function
    - If function returns false, condition fails
    - If function returns true, it succeeds"""
    @wraps(fcn)
    def factory(*args) -> Behavior:
        return Condition(fcn, *args)
    return factory


class Guard(Behavior):
    __slots__ = ("fcn", "args", "completed")
    def __init__(self, fcn, *args):
        self.args = args
        self.fcn = fcn
    def start(self) -> None:
        pass
    def update(self) -> State:
        status = self.fcn(*self.args)
        if status == False:
            return State.Failure
        return State.Running


def guard(fcn):
    """A decorator to construct a guard from any function
    - If function returns false, guard fails
    - If function returns true, it continues execution"""
    @wraps(fcn)
    def factory(*args) -> Behavior:
        return Guard(fcn, *args)
    return factory

class FromGenerator(Behavior):
    def __init__(self, generator, *args):
        self.generator = generator
        self.args = args
    def start(self) -> None:
        self.iteration = self.generator(*self.args)
        self.iteration.__next__()
    def update(self) -> State:
        try:
            return self.iteration.__next__()
        except StopIteration:
            return State.Success

def from_generator(fcn):
    """A decorator that turns a generator into a task
    It will be advanced once to start it, then advanced once per update.
    The value yielded by the generator should be one of the State values.
    If generator terminates, it is interpreted as a success
    """
    @wraps(fcn)
    def factory(*args) -> Behavior:
        return FromGenerator(fcn, *args)
    return factory


def as_generator(tree: Behavior):
    """Run the tree as a generator yielding State"""
    tree.start()
    state = State.Running
    yield state
    while state == state.Running:
        state = tree.update()
        yield state

class Task(Behavior):
    __slots__ = ("fcn", "args", "completed")
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
        except Exception as e:
            print(str(e))
            return State.Failure

def task(fcn):
    """A decorator to construct a task from any function
    - If function throws, task fails
    - If function returns true, it succeeds"""
    @wraps(fcn)
    def factory(*args) -> Behavior:
        return Task(fcn, *args)
    return factory
