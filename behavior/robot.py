from . import behavior
from ..utils import kinematics as kine
import math

def sign(flt):
    if flt >= 0:
        return 1
    else:
        return -1

def normalizeAngle(angle):
    return angle - math.pi * 2.0 * math.floor((angle + math.pi) / (math.pi * 2.0))

def deg2rad(angle):
    return angle * math.pi / 180.0

class DriveForward:
    def __init__(self, robot, distance, speed = 0.14, accuracy = 0.01, slowdown_dist = 0.1):
        self.robot = robot
        self.speed = abs(speed)
        self.accuracy = accuracy
        self.target_distance = distance
        self.slowdown_dist = slowdown_dist
    def start(self):
        self.start_distance = self.robot.travelled_distance
    def update(self):
        travelled_distance = self.robot.travelled_distance - self.start_distance

        error = self.target_distance - travelled_distance
        if abs(error) < self.accuracy:
            self.robot.command = kine.Command(0, 0)
            return behavior.State.Success
        gain = max(abs(error / self.slowdown_dist), 1)
        speed = self.speed * gain * sign(error)
        self.robot.command = kine.Command(
            velocity = speed,
            angularVelocity = 0)
        return behavior.State.Running

def Reverse(robot, distance, *args, **kwargs):
    return DriveForward(robot, -distance, *args, **kwargs)

class TurnOnSpot:
    def __init__(self, robot, angle, angular_vel = 0.12, accuracy = 0.01, slowdown_dist = 0.1):
        self.robot = robot
        self.angular_vel = abs(angular_vel)
        self.accuracy = accuracy
        self.angle_change = angle
        self.slowdown_dist = slowdown_dist
    def start(self):
        self.target_angle = self.robot.heading_rad + self.angle_change
    def update(self):
        error = normalizeAngle(self.target_angle - self.robot.heading_rad) 
        if abs(error) < self.accuracy:
            self.robot.command = kine.Command(0, 0)
            return behavior.State.Success
        gain = max(abs(error / self.slowdown_dist), 1)
        angular_vel = self.angular_vel * gain * sign(error)
        self.robot.command = kine.Command(
            velocity = 0,
            angularVelocity = angular_vel)
        return behavior.State.Running


@behavior.task
def DriveWithVelocity(robot, speed):
    robot.command = kine.Command(
        velocity = speed,
        angularVelocity = 0)
    return True

@behavior.task
def Stop(robot):
    robot.command = kine.Command(
        velocity = 0,
        angularVelocity = 0)
    return True

@behavior.condition
def HasFrontBumper(robot):
    return robot.has_left_bumper or robot.has_right_bumper

@behavior.condition
def IfLeftBumperHit(robot):
    return robot.left_bumper_hit

@behavior.condition
def IfRightBumperHit(robot):
    return robot.right_bumper_hit

@behavior.task
def WaitForBumperHit(robot):
    return (robot.left_bumper_hit or robot.right_bumper_hit)


def DriveToAWall(robot, speed):
    return behavior.Sequence(
            HasFrontBumper(robot),
            DriveWithVelocity(robot, speed),
            WaitForBumperHit(robot),
            Stop(robot))

def TurnAwayFromWall(robot, reverse_distance = 0.1, turn_angle = deg2rad(20)):
    return behavior.Selector(
        behavior.Sequence(
            IfLeftBumperHit(robot),
            Reverse(robot, reverse_distance),
            TurnOnSpot(robot, -turn_angle)),
        behavior.Sequence(
            IfRightBumperHit(robot),
            Reverse(robot, reverse_distance),
            TurnOnSpot(robot, turn_angle)))

def FeelTheWayWithBumpers(robot, speed):
    return behavior.RepeatUntilFail(
        behavior.Sequence(
            DriveToAWall(robot, speed),
            TurnAwayFromWall(robot)))