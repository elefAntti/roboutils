import sys

from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot, pyqtProperty, QTimer
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication

from roboutils.utils import Transform, Vec2
import roboutils.utils.kinematics as kine
from roboutils import hal
from roboutils.hal import simulation
from roboutils import remote
from roboutils import behavior

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

app = QApplication(sys.argv)
sock = remote.RemoteControlSocket(port = 8000)

kinematics = kine.KinematicModel(axel_width = 0.2, left_wheel_r = 0.03, right_wheel_r = 0.03)
robot_state = hal.RobotInterface(kinematics)
robot = GuiRobot(robot_state)

@behavior.task
def SetPosToGui(state):
    robot.pose = state.pose

simulation_tree = behavior.ParallelAll(
    remote.UDPReceive(robot_state, sock),
    hal.ComputeWheelCommands(robot_state),
    simulation.SimulateMotor(robot_state.left_wheel),
    simulation.SimulateMotor(robot_state.right_wheel),
    hal.ComputeOdometry(robot_state),
    SetPosToGui(robot_state),
    remote.SendSensors(robot_state, sock)) 

engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("robot", robot)
engine.load('qml/main.qml')

win = engine.rootObjects()[0]
win.show()

timer = QTimer()
timer.timeout.connect(lambda: simulation_tree.update())
timer.setSingleShot(False)
simulation_tree.start()
timer.start(30)

app.exec_()
