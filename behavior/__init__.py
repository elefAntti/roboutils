from .behavior import *

def run(tree):
    tree.start()
    while tree.update() == State.Running:
        pass