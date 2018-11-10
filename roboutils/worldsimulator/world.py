from ..utils import vec2
from typing import List



class Line:
    def __init__(self, points:List[vec2.Vec2], width):
        self.segmentList = []
        for i in range(0, len(points)-1):
            beg = points[i]
            end = points[i+1]
            segment = LineSegment(beg, end, width)
            self.segmentList.append(segment)

    def isOnLine(self, point:vec2.Vec2) -> bool:
        for segment in self.segmentList:
            if segment.isOnLineSegment(point):
                return True
        return False


class LineSegment:
    def __init__(self, beg:vec2.Vec2, end:vec2.Vec2, width:float):
        self.beg = beg
        self.end = end
        self.width = width

    def isOnLineSegment(self, point:vec2.Vec2) -> bool:
        seg = self.end - self.beg
        segNormal = seg.normal()
        
        point = point - self.beg
        xProjection = point.projectionOn(seg)
        yProjection = point.projectionOn(segNormal)

        return 0 < xProjection \
            and xProjection <= seg.length \
            and -self.width / 2 < yProjection \
            and yProjection < self.width / 2

class World:
    def __init__(self, lines:List[Line]):
        self.lines = lines

    def isOnLine(self, point:vec2.Vec2) -> bool:
        for line in self.lines:
            if line.isOnLine(point):
                return True
        return False