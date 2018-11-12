from roboutils.behavior.robot import FeelTheWayWithBumpers, PavelFollowLine, ValheFollowLine, DriveNextToWall
from roboutils.remote import RemoteControlSocket, SendCommand, UDPReceive, ReceiveSensors
from roboutils import hal
from roboutils.utils import kinematics as kine
from roboutils.behavior import task, guard, run, Selector, ParallelAll
from roboutils.behavior.decorator import Repeat
from roboutils.behavior.time import RateLimit

simulator_sock = RemoteControlSocket(port = 8001, remote_address = ('localhost', 8000))
control_sock = RemoteControlSocket(port = 8002)

remote_command = {
    "velocity_command": 0,
    "turn_command": 0,
    "state": 0
}

@task
def RemoteControl(robot, command):
    robot.velocity_command = command["velocity_command"]
    robot.turn_command = command["turn_command"]
    return False

@guard
def SelectedMode(robot, mode):
    return robot["state"] == mode

@task
def Print(message):
    print(message)
    return True


kinematics = kine.KinematicModel(axel_width = 0.2, left_wheel_r = 0.03, right_wheel_r = 0.03)
robot_state = hal.RobotInterface(kinematics)
robot_state.has_left_bumper = True
robot_state.has_right_bumper = True
robot_behavior = \
    Repeat(
        Selector(
            ParallelAll(
                SelectedMode(remote_command, 0),
                Print("Entering remote control"),
                RemoteControl(robot_state, remote_command)),
            ParallelAll(
                SelectedMode(remote_command, 2),
                Print("Entering mode 2"),
                ValheFollowLine(robot_state)),
            ParallelAll(
                SelectedMode(remote_command, 3),
                Print("Entering mode 3"),
                FeelTheWayWithBumpers(robot_state, 0.14)),
            ParallelAll(
                SelectedMode(remote_command, 4),
                Print("Entering Drive Next to wall"),
                DriveNextToWall(robot_state, robot_state.front_range, 0.3))))
tree = \
    ParallelAll(
        ReceiveSensors(robot_state, simulator_sock),
        UDPReceive(remote_command, control_sock),
        robot_behavior,
        RateLimit(0.03, SendCommand(robot_state, simulator_sock)))

run(tree)
