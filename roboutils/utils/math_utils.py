import math

def sign(flt: float) -> float:
    if flt >= 0:
        return 1
    else:
        return -1

def normalizeAngle(angle: float) -> float:
    return angle - math.pi * 2.0 * math.floor((angle + math.pi) / (math.pi * 2.0))

def deg2rad(angle:float) -> float:
    return angle * math.pi / 180.0

def rad2deg(angle:float) -> float:
    return angle * 180 / math.pi

# uses radians
# if starting from angle1, 
# how to turn in order to reach angle2
def angleDiff(angle1:float, angle2:float) -> float:
    angle1 = angle1 % (2*math.pi)
    angle2 = angle2 % (2*math.pi)
    diff = angle1-angle2
    return diff if diff<math.pi else diff-2*math.pi