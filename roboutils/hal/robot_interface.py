from .. import utils
from ..utils import math_utils
from ..utils import vec2, kinematics as kine

class Motor:
    def __init__(self):
        self.angular_vel_sp = 0
        self.angular_vel = 0
        self.max_angular_vel = math_utils.deg2rad(700)
        self.position = 0

class RangeSensor:
    def __init__(self, location: vec2.Transform):
        self.max_range = 1.0
        self.value = 0.0
        self.location = location

class ColorSensor:
    def __init__(self, location: vec2.Transform):
        self.hue = 0.0
        self.saturation = 0.0
        self.value = 0.0
        self.location = location

class RobotInterface:
    def __init__(self, kinematics):
        self.kinematics = kinematics
        self.travelled_distance = 0
        self.heading_rad = 0
        self.has_left_bumper = False
        self.has_right_bumper = False
        self.left_bumper_hit = False
        self.right_bumper_hit = False
        self.turn_command = 0
        self.velocity_command = 0
        self.heading_rad = 0
        self.pose = vec2.Transform.identity()
        self.movement = kine.Command(0,0)
        self.left_wheel = Motor()
        self.right_wheel = Motor()
        self.front_range = RangeSensor(
            vec2.Transform(heading=0.0, offset=vec2.Vec2(0.05, 0.0)))
        self.line_sensor = False #TODO: Replace this with proper light sensor

    @property
    def command(self):
        return utils.Command(self.velocity_command, self.turn_command)
    @command.setter
    def command(self, value):
        self.turn_command = value.angularVelocity
        self.velocity_command = value.velocity
