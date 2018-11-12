from . import behavior
from . import decorator
from ..utils import kinematics as kine
from ..utils.math_utils import deg2rad, rad2deg, sign, normalizeAngle
from ..utils.Radians import Radians
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

START_ANGLE = deg2rad(10) # radians
RESET_DISTANCE = 0.05
ANGLE_ENOUGH = abs(deg2rad(5)) # must be positive
MAX_TURN_ANGLE = deg2rad(90) # must be positive
FORWARD_AFTER_NOLINE = 0.08 # meters, must be positive; try 0.8%*lineWidth

# Uses radians
# Argument 'record' is a function that
# takes the recorded value as an argument and
# records it somewhere
class RecordAngle:
    def __init__(self, robot:RobotInterface, record:Callable):
        self.robot = robot
        self.angleStart = None
        self.angleDelta = START_ANGLE
        self.record = record
    def start(self):
        self.angleStart = self.robot.heading_rad
        self.angleDelta = angleDiff(self.robot.heading_rad, self.angleStart)
        self.record(self.angleDelta)
    def update(self):
        self.angleDelta = angleDiff(self.robot.heading_rad, self.angleStart)
        self.record(self.angleDelta)
        return behavior.State.Running

# Uses radians
def Wiggle(robot, firstAngle) -> behavior.Task:
    angle = firstAngle
    if firstAngle == 0 or firstAngle >= MAX_TURN_ANGLE or firstAngle <= - MAX_TURN_ANGLE:
        angle = deg2rad(START_ANGLE)
    move = behavior.Sequence(LookBothWays(robot, angle))
    while abs(angle) < MAX_TURN_ANGLE :
        angle *= 2
        move.append(LookBothWays(robot, angle))
    return move


class LineSightingRecorder:
    def __init__(self, robot:RobotInterface):
        self.robot = robot
        self.startedToSeeLine_angle = None
        self.startedToSeeLine_distance = None
    def start(self):
        self.startedToSeeLine_angle = self.robot.heading_rad if self.robot.line_sensor else None
        self.startedToSeeLine_distrance = self.robot.travelled_distance if self.robot.line_sensor else None
    def update(self):
        seesLine = self.robot.line_sensor
        angleNow = self.robot.heading_rad
        positionNow = self.robot.travelled_distance
        if seesLine:
            if self.startedToSeeLine_angle is None:
                self.startedToSeeLine_angle = angleNow
                self.startedToSeeLine_distance = positionNow
        else:
            self.startedToSeeLine_angle = None
            self.startedToSeeLine_distance = None
        return behavior.State.Running


# Assumes robot is turning
# E.g. "see line all the time during a turn of X radians"
@behavior.task
def SeeLineDuringAngle(robot:RobotInterface, angle, lineRecorder:LineSightingRecorder):
    seesLine = robot.line_sensor
    angleNow = robot.heading_rad
    if seesLine:
        if lineRecorder.startedToSeeLine_angle is None:
            return False
        else:
            if abs(angleDiff(angleNow, lineRecorder.startedToSeeLine_angle)) >= angle :
                return True
    else:
        return False



class TurnSetAngle:
    def __init__(self, robot:RobotInterface, direction:int):
        self.robot = robot
        self.behavior = None
        self.angle = None #positive
        self.startDir = None
        if direction == 1 or direction == -1:
            self.direction = direction
        else:
            raise AttributeError("Direction has to be -1 or 1")
    def start(self):
        self.behavior = TurnOnSpot(self.robot, self.direction * math.pi)
        self.startDir = self.robot.heading_rad
        self.behavior.start()
    def update(self):
        if self.angle is None:
            raise RuntimeError("Angle is not set")
        if self.angle <= 0:
            raise AttributeError("Angle can not be negative or 0.")
        else:
            if abs(angleDiff(self.startDir, self.robot.heading_rad)) >= self.angle :
                return behavior.State.Success
            else:
                return behavior.State.Running
    def setAngle(self, angle):
        self.angle = angle
    

# Keeps turning if sees the line,
# until does not see it any more.
# Then turn back all the way.
def TurnAwayAndBack(robot:RobotInterface, angle:float) -> behavior.Task:
    if angle == 0:
        raise AttributeError("Angle can not be 0")
    sign = lambda x: (1, -1)[x < 0]
    turnAngle = TurnSetAngle(robot, - sign(angle))
    task = behavior.Sequence(
        behavior.ParallelAny(
            RecordAngle(robot, lambda angle: turnAngle.setAngle(abs(angle))),
            behavior.Sequence(
                    TurnOnSpot(robot, angle),
                    behavior.ParallelAny(
                        TurnOnSpot(robot, sign(angle)*math.pi),
                        WaitUntilSeesNoLine(robot)
                    )
                )
        ),
        turnAngle
    )
    return task
        

# Uses radians
def LookBothWaysKeepingLineInSight(robot, angle) -> behavior.Task:
    if angle == 0:
        raise AttributeError("Angle can not be 0.")
    return behavior.Sequence(
        TurnAwayAndBack(robot, angle),
        TurnAwayAndBack(robot, -angle),
        DriveForward(robot, 0.10),
        DriveForward(robot, -0.10)
    )
        

def WiggleKeepingLineInSight(robot, firstAngle) -> behavior.Task:
    angle = firstAngle
    if abs(angle) >= deg2rad(180):
        raise AttributeError("fistAngle can not be >= 180 deg.")
    move = behavior.Sequence(LookBothWaysKeepingLineInSight(robot, angle))
    while angle < deg2rad(180) and angle > deg2rad(-180):
        angle *= 2
        move.append(LookBothWaysKeepingLineInSight(robot, angle))
    return move

#radians
def LookBothWays(robot, angle:float) -> behavior.Task:
    return behavior.Sequence(
        TurnOnSpot(robot, angle),
        TurnOnSpot(robot, -2*angle),
        TurnOnSpot(robot, angle)
    )

#radians
class ResetRecordedAngleWhenGoingStraight:
    def __init__(self, robot:RobotInterface, angleRecorder:RecordAngle):
        self.robot = robot
        self.angleRecorder = angleRecorder
        self.distance_at_start = None
    def start(self):
        self.distance_at_start = self.robot.travelled_distance
    def update(self):
        travDistNow = self.robot.travelled_distance
        if (travDistNow - self.distance_at_start > RESET_DISTANCE):
            self.distance_at_start = travDistNow
            self.angleRecorder.resetAngle
        return behavior.State.Running


class TurnTowardsLine:
    def __init__(self, robot:RobotInterface, lineSeer:LineSightingRecorder):
        self.robot = robot
        self.lineSeer = lineSeer
        self.behavior = None
    def start(self):
        if self.lineSeer.startedToSeeLine_angle is None:
            raise TypeError("Ei pitäis olla None wtf")
        angle = angleDiff(self.robot.heading_rad, self.lineSeer.startedToSeeLine_angle)
        self.behavior = behavior.Sequence(
            DriveForward(self.robot, 0.20),
            DriveForward(self.robot, -0.20),
            TurnOnSpot(self.robot, angle)
        )
        self.behavior.start()
    def update(self):
        return self.behavior.update()


def ValheFollowLine(robot) -> behavior.Task:
    lineSeer = LineSightingRecorder(robot)
    seeLineDuringAngle2 = SeeLineDuringAngle(robot, ANGLE_ENOUGH, lineSeer)
    turnTowardsLine2 = TurnTowardsLine(robot, lineSeer)

    return decorator.Repeat(behavior.Sequence(
        DriveWithVelocity(robot, 0.3),
        WaitUntilSeesNoLine(robot),
        DriveForward(robot, FORWARD_AFTER_NOLINE),
        behavior.ParallelAny(
            lineSeer,
            seeLineDuringAngle2,
            WiggleKeepingLineInSight(robot, START_ANGLE)
        ),
        turnTowardsLine2
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