import time

from .. import utils
from ..behavior import State
from ..utils import kinematics as kine


# tasks

class ComputeWheelCommands:
    def __init__(self, robot):
        self.robot = robot
    def start(self):
        pass
    def update(self):
        wheel_command = self.robot.kinematics.computeWheelCommand(self.robot.command)
        limiting_speed = max(
            abs(wheel_command.left_angular_vel),
            abs(wheel_command.right_angular_vel))
        speed_limit = min(
            self.robot.left_wheel.max_angular_vel,
            self.robot.right_wheel.max_angular_vel)
        scale = speed_limit / limiting_speed if limiting_speed > speed_limit else 1.0
        self.robot.left_wheel.angular_vel_sp = wheel_command.left_angular_vel * scale
        self.robot.right_wheel.angular_vel_sp = wheel_command.right_angular_vel * scale
        return State.Running

class ComputeOdometry:
    def __init__(self, robot, output = None, max_dt = 2.0):
        self.robot = robot
        self.output = output or robot
        self.max_dt = max_dt
    def start(self):
        self.old_left_pos = self.robot.left_wheel.position
        self.old_right_pos = self.robot.right_wheel.position
        self.output.travelled_distance = 0
        self.output.heading_rad = 0
        self.output.pose = utils.Transform.identity()
        self.output.movement = kine.Command(0,0)
        self.last_time = time.time()
    def update(self):
        new_time = time.time()
        dt = min(new_time - self.last_time, self.max_dt)
        self.last_time = new_time
        wheel_command = kine.WheelCommand(
            (self.robot.left_wheel.position - self.old_left_pos) / dt,
            (self.robot.right_wheel.position - self.old_right_pos) / dt)
        self.old_left_pos = self.robot.left_wheel.position
        self.old_right_pos = self.robot.right_wheel.position
        estimated_movement = self.robot.kinematics.computeCommand(wheel_command)
        self.output.travelled_distance += estimated_movement.velocity * dt
        self.output.heading_rad += estimated_movement.angularVelocity * dt
        self.output.pose = kine.predictPose(self.output.pose, estimated_movement, dt)
        self.output.movement = estimated_movement
        return State.Running