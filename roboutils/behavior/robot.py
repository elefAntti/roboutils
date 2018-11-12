from . import behavior
from . import decorator
from ..utils import kinematics as kine
from ..utils.math_utils import deg2rad, rad2deg, sign, normalizeAngle
import math
import time
from ..hal import RobotInterface
from typing import Callable

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
def DriveWithAngleVelocity(robot, speed, angle):
    robot.command = kine.Command(
        velocity = speed,
        angularVelocity = angle
    )

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

@behavior.from_generator   
def PavelFollowLine(robot, on_the_line, curvature = 1.9, speed = 0.033, min_duration = 1.5, max_dir_change = deg2rad(15)):
        previous_measurement = on_the_line()
        line_dir = robot.heading_rad
        start_time = time.time()
        yield 
        while abs(line_dir - robot.heading_rad) < max_dir_change \
            or time.time() - start_time < min_duration:
            on_the_line_now = on_the_line()
            if on_the_line_now:
                robot.command = kine.Command.arc(speed, curvature)
            else:
                robot.command = kine.Command.arc(speed, -curvature)
            if on_the_line_now != previous_measurement:
                previous_measurement = on_the_line_now
                line_dir = robot.heading_rad
            yield behavior.State.Running
        end_part = behavior.Sequence(
            ReverseCurrentCommand(robot),
            WaitForRotation(robot, line_dir - robot.heading_rad),
            Stop(robot))
        for state in behavior.as_generator(end_part):
            yield state

# uses radians
# if starting from angle1, 
# how to turn in order to reach angle2
def angleDiff(angle1:float, angle2:float) -> float:
    angle1 = angle1 % (2*math.pi)
    angle2 = angle2 % (2*math.pi)
    diff = angle1-angle2
    return diff if diff<math.pi else diff-2*math.pi


@behavior.task
def WaitUntilSeesLine(robot:RobotInterface):
    return robot.line_sensor

@behavior.task
def WaitUntilSeesNoLine(robot:RobotInterface):
    return not robot.line_sensor



def ValheFollowLine(robot) -> behavior.Task:

    return decorator.Repeat(behavior.Sequence(
        behavior.ParallelAny(
           DriveWithAngleVelocity(robot, 0.2, -deg2rad(90)),
           WaitForRotation(robot, -deg2rad(90)),
           WaitUntilSeesNoLine(robot)
        ),
        behavior.ParallelAny(
           DriveWithAngleVelocity(robot, 0.2, deg2rad(90)),
           WaitForRotation(robot, deg2rad(90)),
           WaitUntilSeesLine(robot)
        ),
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