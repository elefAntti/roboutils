from . import behavior

@behavior.task
def DoNothing():
    return True

@behavior.guard
def Fail():
    return False

@behavior.task
def WaitForever():
    return False