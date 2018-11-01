from roboutils.behavior.robot import FeelTheWayWithBumpers
from roboutils.remote import RemoteControlSocket, SendCommand, UDPReceive
from roboutils import hal
from roboutils.utils import kinematics as kine
from roboutils.behavior import ParallelAll, run, Task
from roboutils.behavior.time import RateLimit

sock = RemoteControlSocket(port = 8001, remote_address = ('localhost', 8000))

kinematics = kine.KinematicModel(axel_width = 0.2, left_wheel_r = 0.03, right_wheel_r = 0.03)
robot_state = hal.RobotInterface(kinematics)
robot_state.has_left_bumper = True
robot_state.has_right_bumper = True
tree = \
    RateLimit(
        0.03,
        ParallelAll(
            UDPReceive(robot_state, sock),
            FeelTheWayWithBumpers(robot_state, 0.14),
            SendCommand(robot_state, sock)
            ))

run(tree)
