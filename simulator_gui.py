import sys

import rx
from rx.subjects import BehaviorSubject
from rx.concurrency import QtScheduler
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot, pyqtProperty
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication

from roboutils.utils import Transform, Vec2
import roboutils.utils.kinematics as kine
from roboutils.utils import RemoteControlSocket
from roboutils import hal
from roboutils.hal import simulation
from roboutils.hal import remote
from roboutils import behavior

scheduler = QtScheduler(QtCore)

class GuiRobot(QObject):
    _xChanged = pyqtSignal()
    _yChanged = pyqtSignal()
    _headingChanged = pyqtSignal()
    _leftVelChanged = pyqtSignal()
    _rightVelChanged = pyqtSignal()
    _left_bumper_changed = pyqtSignal()
    _right_bumper_changed = pyqtSignal()
    def __init__(self, parent=None):
        super().__init__(parent)
        self._x = 0
        self._y = 0
        self._heading = 0
        self._left_wheel_vel = 0
        self._right_wheel_vel = 0
        self._left_bumper = False
        self._right_bumper = False

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
        return self._left_bumper

    @left_bumper.setter
    def left_bumper(self, value):
        self._left_bumper = value
        self._left_bumper_changed.emit()

    @pyqtProperty('QVariant', notify=_right_bumper_changed)
    def right_bumper(self):
        return self._right_bumper

    @right_bumper.setter
    def right_bumper(self, value):
        self._right_bumper = value
        self._right_bumper_changed.emit()

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
robot = GuiRobot()

kinematics = kine.KinematicModel(axel_width = 0.2, left_wheel_r = 0.03, right_wheel_r = 0.03)
robot_state = hal.RobotInterface(kinematics)
simulation_tree = behavior.ParallelAll(
    remote.SendSensorsAndReadCommand(robot_state, None, local_port=8000),
    hal.ComputeWheelCommands(robot_state),
    simulation.SimulateMotor(robot_state.left_wheel),
    simulation.SimulateMotor(robot_state.right_wheel),
    hal.ComputeOdometry(robot_state, output=robot)) 

engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("robot", robot)
engine.load('qml/main.qml')

win = engine.rootObjects()[0]
win.show()

simulation_tree.start()
rx.Observable.interval(30, scheduler=scheduler)\
    .subscribe(lambda _:simulation_tree.update())

app.exec_()
