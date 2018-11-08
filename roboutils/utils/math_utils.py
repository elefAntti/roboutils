import math

def sign(flt: float) -> float:
    if flt >= 0:
        return 1
    else:
        return -1

def normalizeAngle(angle: float) -> float:
    return angle - math.pi * 2.0 * math.floor((angle + math.pi) / (math.pi * 2.0))

def deg2rad(angle: float) -> float:
    return angle * math.pi / 180.0