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
    def __init__(self, start:vec2.Vec2, end:vec2.Vec2, width:float):
        self.start = start
        self.end = end
        self.width = width

    def isOnLineSegment(self, point:vec2.Vec2) -> bool:
        seg = self.end - self.start
        segNormal = seg.normal()
        
        point = point - self.start
        xProjection = point.projectionOn(seg)
        yProjection = point.projectionOn(segNormal)
        halfWidth = self.width / 2

        return 0 - halfWidth < xProjection \
            and xProjection <= seg.length + halfWidth \
            and - halfWidth < yProjection \
            and yProjection < halfWidth


class Wall(vec2.LineSeg):
    __slots__=()
    pass


class World:
    def __init__(self, lines:List[Line], walls:List[Wall] = None):
        self.lines = lines
        self.walls = walls or []

    def isOnLine(self, point:vec2.Vec2) -> bool:
        for line in self.lines:
            if line.isOnLine(point):
                return True
        return False
    
    def rangeMeasurement(self, ray: vec2.Ray, max_distance: float) -> float:
        hit_distances = (ray.lineSeqIntersection(wall) for wall in self.walls)
        return min((x for x in hit_distances if x), default = max_distance)