from ..utils import RemoteControlSocket

class SendCommandAndReadSensors:
    def __init__(self, robot, remote_address, local_port = 8001 ):
        self.robot = robot
        self.socket = RemoteControlSocket(
            local_port,
            state_dict = robot.__dict__,
            remote_address = remote_address)
    def start(self):
        pass
    def update(self):
        self.socket.send_fields(("velocity_command", "turn_command"))
        self.socket.receive()

class SendSensorsAndReadCommand:
    def __init__(self, robot, remote_address, local_port = 8000 ):
        self.robot = robot
        self.socket = RemoteControlSocket(
            local_port,
            state_dict = robot.__dict__,
            remote_address = remote_address)
    def start(self):
        pass
    def update(self):
        self.socket.send_fields(("left_bumper_hit", "right_bumper_hit"))
        self.socket.receive()