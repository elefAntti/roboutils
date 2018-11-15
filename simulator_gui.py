import sys


import ezdxf

from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot, pyqtProperty, QTimer, QPointF
from PyQt5.QtQml import QQmlApplicationEngine, QQmlListProperty
from PyQt5.QtWidgets import QApplication

from roboutils.utils import Transform, Vec2
import roboutils.utils.kinematics as kine
from roboutils import hal
from roboutils.hal import simulation
from roboutils.hal.differential_drive import ComputeWheelCommands, ComputeOdometry
from roboutils import remote
from roboutils import behavior

from roboutils.worldsimulator import World, Line, Wall


class GuiRobot(QObject):
    _xChanged = pyqtSignal()
    _yChanged = pyqtSignal()
    _headingChanged = pyqtSignal()
    _leftVelChanged = pyqtSignal()
    _rightVelChanged = pyqtSignal()
    _left_bumper_changed = pyqtSignal()
    _right_bumper_changed = pyqtSignal()
    _line_sensor_changed = pyqtSignal()
    def __init__(self, robot_state, parent=None):
        super().__init__(parent)
        self._x = 0
        self._y = 0
        self._heading = 0
        self._left_wheel_vel = 0
        self._right_wheel_vel = 0
        self._left_bumper = False
        self._right_bumper = False
        self.robot_state = robot_state
    @pyqtProperty('QVariant', notify=_xChanged)
    def x(self):
        return self._x

    @x.setter
    def x(self, value):
        self._x = value
        self._xChanged.emit()

    @pyqtProperty('QVariant', notify=_yChanged)
    def y(self):
        return self._y

    @y.setter
    def y(self, value):
        self._y = value
        self._yChanged.emit()

    @pyqtProperty('QVariant', notify=_headingChanged)
    def heading(self):
        return self._heading

    @heading.setter
    def heading(self, value):
        self._heading = value
        self._headingChanged.emit()

    @pyqtProperty('QVariant', notify=_leftVelChanged)
    def leftWheelVel(self):
        return self._left_wheel_vel

    @pyqtProperty('QVariant', notify=_rightVelChanged)
    def rightWheelVel(self):
        return self._right_wheel_vel

    @pyqtProperty('QVariant', notify=_left_bumper_changed)
    def left_bumper(self):
        return self.robot_state.left_bumper_hit

    @left_bumper.setter
    def left_bumper(self, value):
        self.robot_state.left_bumper_hit = value
        self._left_bumper_changed.emit()

    @pyqtProperty('QVariant', notify=_right_bumper_changed)
    def right_bumper(self):
        return self.robot_state.right_bumper_hit

    @right_bumper.setter
    def right_bumper(self, value):
        self.robot_state.right_bumper_hit = value
        self._right_bumper_changed.emit()

    @pyqtProperty('QVariant', notify=_line_sensor_changed)
    def line_sensor(self):
        return self.robot_state.line_sensor

    @line_sensor.setter
    def line_sensor(self, value):
        self.robot_state.line_sensor = value
        self._line_sensor_changed.emit()

    @property
    def pose(self):
        return Transform(self.heading, Vec2(self.x, self.y))
    
    @pose.setter
    def pose(self, pose):
        self.x = pose.x
        self.y = pose.y
        self.heading = pose.heading
        self._headingChanged.emit()
    

    def setWheelCommand(self, command):
        self._left_wheel_vel = command.left_angular_vel
        self._right_wheel_vel = command.right_angular_vel
        self._leftVelChanged.emit()
        self._rightVelChanged.emit()

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

app = QApplication(sys.argv)
sock = remote.RemoteControlSocket(port = 8000)

kinematics = kine.KinematicModel(axel_width = 0.2, left_wheel_r = 0.03, right_wheel_r = 0.03)
robot_state = hal.RobotInterface(kinematics)
robot = GuiRobot(robot_state)

walls = []
drawing = ezdxf.readfile("map.dxf")
model = drawing.modelspace()
for entity in model.query('LINE'):
    if entity.dxf.layer == "Walls":
        walls.append(Wall(Vec2(*entity.dxf.start), Vec2(*entity.dxf.end)))

world = World(
    lines = [ 
        Line([
            Vec2(-0.7, 0),
            Vec2(0,0),
            Vec2(0.0, 0.7),
            Vec2(0.7, 0.7),
            Vec2(0.6, -0.7),
            Vec2(-0.8, -0.9)],
        width=0.10)],
    walls=walls)
gui_world = GuiWorld(world)

@behavior.task
def UpdateGui(state):
    robot.pose = state.pose
    robot._line_sensor_changed.emit()

@behavior.task
def SimulateLineSensor(state, world:World):
    state.line_sensor = world.isOnLine(robot.pose.applyTo(Vec2(0.05, 0)))

simulation_tree = behavior.ParallelAll(
    remote.UDPReceive(robot_state, sock),
    ComputeWheelCommands(robot_state),
    simulation.SimulateMotor(robot_state.left_wheel),
    simulation.SimulateMotor(robot_state.right_wheel),
    simulation.SimulateRangeSensor(robot_state, robot_state.front_range, world),
    SimulateLineSensor(robot_state, world),
    ComputeOdometry(robot_state),
    UpdateGui(robot_state),
    remote.SendSensors(robot_state, sock)) 

engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("robot", robot)
engine.rootContext().setContextProperty("world", gui_world)
engine.load('qml/SimulatorWindow.qml')

win = engine.rootObjects()[0]
win.show()

timer = QTimer()
timer.timeout.connect(lambda: simulation_tree.update())
timer.setSingleShot(False)
simulation_tree.start()
timer.start(30)

app.exec_()
