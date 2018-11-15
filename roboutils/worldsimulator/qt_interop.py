from PyQt5.QtCore import QObject, pyqtSignal, pyqtSlot, pyqtProperty, QPointF
from PyQt5.QtQml import QQmlListProperty
from ..utils.vec2 import Vec2
from .world import World

class GuiLineSegment(QObject):
    def __init__(self, beg:QPointF, end:QPointF, width:float, style:int = 0, parent:QObject = None):
        super().__init__(parent)
        self._beg = beg
        self._end = end
        self._width = width
        self._style = style
    @pyqtProperty(QPointF)
    def beg(self):
        return self._beg
    @pyqtProperty(QPointF)
    def end(self):
        return self._end
    @pyqtProperty(float)
    def width(self):
        return self._width
    @pyqtProperty(int)
    def style(self):
        return self._style

def Vec2ToQPointF(vec:Vec2) -> QPointF:
    return QPointF(vec.x, vec.y)

class GuiWorld(QObject):
    def __init__(self, world:World, parent=None):
        super().__init__(parent)
        self._lines = []
        for line in world.lines:
            for lineSegment in line.segmentList:
                self._lines.append(
                    GuiLineSegment(
                        Vec2ToQPointF(lineSegment.start),
                        Vec2ToQPointF(lineSegment.end),
                        lineSegment.width))
        for wall in world.walls:
                self._lines.append(
                    GuiLineSegment(
                        Vec2ToQPointF(wall.start),
                        Vec2ToQPointF(wall.end),
                        width = 0.01,
                        style = 1))
    
    @pyqtProperty(QQmlListProperty)
    def lines(self):
        return QQmlListProperty(GuiLineSegment, self, self._lines)
