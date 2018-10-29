from .. import utils

class RobotInterface:
    def __init__(self):
        self.travelled_distance = 0
        self.heading_rad = 0
        self.has_left_bumper = False
        self.has_right_bumper = False
        self.left_bumper_hit = False
        self.right_bumper_hit = False
        self.turn_command = 0
        self.velocity_command = 0

    @property
    def command(self):
        return utils.Command(self.velocity_command, self.turn_command)
    @command.setter
    def command(self, value):
        self.turn_command = value.angularVelocity
        self.velocity_command = value.velocity