from . import behavior
from . import decorator
from ..utils import kinematics as kine
from ..utils import vec2
from ..utils.math_utils import deg2rad, sign, normalizeAngle
import math
import time
from ..hal import RobotInterface, RangeSensor

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

@behavior.task
def DriveNextToWall(robot: RobotInterface,
                    sensor: RangeSensor,
                    distance:float, 
                    speed:float = 0.14,
                    slowdown_dist:float = 0.1,
                    accuracy:float = 0.01):
    error = sensor.value - distance
    if abs(error) < accuracy:
        robot.command = kine.Command(0, 0)
        return True
    gain = max(abs(error / slowdown_dist), 1)
    speed = speed * gain * sign(error)
    robot.command = kine.Command(
        velocity = speed,
        angularVelocity = 0)
    return False

@behavior.from_generator
def AlignToWall(robot: RobotInterface, sensor:RangeSensor, angle_offset:float = 0.0):
    start_angle = robot.heading_rad
    yield behavior.State.Running
    robot.command = kine.Command(0.0, -0.5)

    while robot.heading_rad - start_angle > deg2rad(-15):
        yield behavior.State.Running

    tf = vec2.Transform.rotation(robot.heading_rad).after(sensor.location)
    hit_point1 = tf.applyTo(vec2.Vec2(sensor.value, 0.0))
    robot.command = kine.Command(0, 0.5)

    while robot.heading_rad - start_angle < deg2rad(15):
        yield behavior.State.Running

    tf = vec2.Transform.rotation(robot.heading_rad).after(sensor.location)
    hit_point2 = tf.applyTo(vec2.Vec2(sensor.value, 0.0))
    face_to = (hit_point1 - hit_point2).normal()
    angle = normalizeAngle(face_to.heading - robot.heading_rad + angle_offset)
    print(str(face_to.heading))
    turn = TurnOnSpot(robot, angle, accuracy = 0.005, slowdown_dist = 0.02)
    for state in behavior.as_generator(turn):
        yield state

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