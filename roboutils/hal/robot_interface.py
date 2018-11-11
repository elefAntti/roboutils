from .. import utils
from ..utils import math_utils

class Motor:
    def __init__(self):
        self.angular_vel_sp = 0
        self.angular_vel = 0
        self.max_angular_vel = math_utils.deg2rad(700)
        self.position = 0

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
        self.left_wheel = Motor()
        self.right_wheel = Motor()
        self.line_sensor = False #TODO: Replace this with proper light sensor

    @property
    def command(self):
        return utils.Command(self.velocity_command, self.turn_command)
    @command.setter
    def command(self, value):
        self.turn_command = value.angularVelocity
        self.velocity_command = value.velocity
