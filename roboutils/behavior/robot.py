from . import behavior
from . import decorator
from ..utils import kinematics as kine
import math
import time
from ..hal import RobotInterface

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



class WaitForRotation:
    def __init__(self, robot, angle_diff):
        self.target_angle = 0
        self.robot = robot
        self.angle_diff_or_fcn = angle_diff
    def start(self):
        if callable(self.angle_diff_or_fcn):
            self.angle_diff = self.angle_diff_or_fcn()
        else:
            self.angle_diff = self.angle_diff_or_fcn
        self.target_angle = self.robot.heading_rad + self.angle_diff
    def update(self):
        if self.angle_diff == 0:
            return True 
        if self.angle_diff > 0 and self.robot.heading_rad > self.target_angle:
            return behavior.State.Success
        if self.angle_diff < 0 and self.robot.heading_rad < self.target_angle:
            return behavior.State.Success
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

@behavior.task
def ReverseCurrentCommand(robot):
    robot.command = robot.command.reverse()
    return True
    
class _FollowLine:
    """Follow eg. a line on the ground"""
    def __init__(self, robot, on_the_line, curvature = 1.9, speed = 0.033, min_duration = 1.5, max_dir_change = deg2rad(15)):
        self.robot = robot
        self.on_the_line = on_the_line
        self.curvature = curvature
        self.speed = speed
        self.line_dir = None
        self.min_duration = min_duration
        self.max_dir_change = max_dir_change
    def start(self):
        self.previous_measurement = self.on_the_line()
        self.line_dir = self.robot.heading_rad
        self.start_time = time.time()
    def update(self):
        on_the_line = self.on_the_line()
        if on_the_line:
            self.robot.command = kine.Command.arc(self.speed, self.curvature)
        else:
            self.robot.command = kine.Command.arc(self.speed, -self.curvature)
        if on_the_line != self.previous_measurement:
            self.previous_measurement = on_the_line
            self.line_dir = self.robot.heading_rad
        if abs(self.line_dir - self.robot.heading_rad) > self.max_dir_change \
        and time.time() - self.start_time > self.min_duration:
            return behavior.State.Success
        return behavior.State.Running

def FollowLine(
        robot,
        on_the_line,
        curvature = 1.9,
        speed = 0.033,
        min_duration = 1.5,
        max_dir_change = deg2rad(15)):
    follow = _FollowLine(robot, on_the_line, curvature, speed, min_duration, max_dir_change)
    return behavior.Sequence(
        follow,
        ReverseCurrentCommand(robot),
        WaitForRotation(robot, lambda: follow.line_dir - robot.heading_rad),
        Stop(robot))

@behavior.task
def WaitUntilSeesLine(robot:RobotInterface):
    return robot.line_sensor

@behavior.task
def WaitUntilSeesNoLine(robot:RobotInterface):
    return not robot.line_sensor

def Wiggle(robot):
    return behavior.Sequence(
        TurnOnSpot(robot, deg2rad(5)), #5 left
        TurnOnSpot(robot, deg2rad(-10)), #5 right
        TurnOnSpot(robot, deg2rad(20)), #15 left
        TurnOnSpot(robot, deg2rad(-35)), #15 right
        TurnOnSpot(robot, deg2rad(45)), #30 left
        TurnOnSpot(robot, deg2rad(-60)), #30 right
        TurnOnSpot(robot, deg2rad(90)), #60 left
        TurnOnSpot(robot, deg2rad(-120)), #60 right
        TurnOnSpot(robot, deg2rad(170)), #110 left
        TurnOnSpot(robot, deg2rad(-220)), #110 right
    )

def ValheFollowLine(robot):
    return decorator.Repeat(behavior.Sequence(

        DriveWithVelocity(robot, 0.3),
        WaitUntilSeesNoLine(robot),
        behavior.ParallelAny(
            WaitUntilSeesLine(robot),
            Wiggle(robot)
        )
    ))

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
    return decorator.RepeatUntilFail(
        behavior.Sequence(
            DriveToAWall(robot, speed),
            TurnAwayFromWall(robot)))