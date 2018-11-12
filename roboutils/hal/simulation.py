import time
from ..behavior import State, task
from ..hal.robot_interface import Motor, RangeSensor, RobotInterface
from ..worldsimulator import World
from ..utils.vec2 import Ray

class SimulateMotor:
    def __init__(self, motor:Motor, max_dt:float = 0.2):
        self.motor = motor
        self.max_dt = max_dt
    def start(self):
        self.motor.angular_vel = 0
        self.motor.position = 0
        self.last_time = time.time()
    def update(self):
        new_time = time.time()
        dt = min(new_time - self.last_time, self.max_dt)
        self.last_time = new_time
        self.motor.position += self.motor.angular_vel * 0.5 * dt
        self.motor.angular_vel = self.motor.angular_vel_sp
        self.motor.position += self.motor.angular_vel * 0.5 * dt
        return State.Running

@task
def SimulateRangeSensor(robot:RobotInterface, sensor:RangeSensor, world:World):
    transform = robot.pose.after(sensor.location)
    sensor.value = world.rangeMeasurement(Ray(transform), sensor.max_range)
    return False