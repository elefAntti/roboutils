import socket
import time
import msgpack
from .behavior import task

def getFieldsFromDict(dictionary, fields):
    return {k: dictionary.get(k, None) for k in fields}

class RemoteControlSocket:
    safety_time = 3.0
    def __init__(self, port, remote_address = None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ("", port)
        self.sock.bind(server_address)
        self.sock.setblocking(0)
        self.last_received = time.time()
        self.tx_seq_no = 0
        self.rx_seq_no = 0 
        self.remote_address = remote_address
    def receive(self):
        message = {}
        try:
            while True:
                data, client = self.sock.recvfrom(1024)
                new_message = msgpack.loads(data, encoding = "UTF-8")
                if new_message[0] < 10:
                    self.tx_seq_no = 0
                if new_message[0] < 10 or new_message[0] > self.rx_seq_no:
                    self.rx_seq_no = new_message[0]
                    self.remote_address = client
                    self.last_received = time.time()
                    message = new_message[1]
        except BlockingIOError:
            pass
        return message
    def send(self, message):
        if self.remote_address:
            data = msgpack.dumps([self.tx_seq_no, message], encoding = "UTF-8")
            self.sock.sendto(data, self.remote_address)
            self.tx_seq_no += 1

    def send_fields(self, state, fields):
        """Send selected fields from the state dictionary"""
        message = {k: state.get(k, None) for k in fields}
        self.send(message)
    def is_timeout(self):
        return time.time() - self.last_received > self.safety_time

@task
def UDPSend(message, socket):
    socket.send(message)
    return False #Never complete

@task
def UDPSendFields(message, socket, fields):
    socket.send_fields(message, fields)

    return False #Never complete

@task
def UDPReceive(state, socket):
    message = socket.receive()
    if isinstance(state, dict):
        state.update(message)
    else:
        state.__dict__.update(message)
    return False #Never complete

def SendCommand(robot, socket):
    fields_to_send = ("velocity_command", "turn_command")
    return UDPSendFields(robot.__dict__, socket, fields_to_send)

@task
def SendSensors(robot, socket:RemoteControlSocket):
    fields_to_send = (
            "left_bumper_hit",
            "right_bumper_hit",
            "travelled_distance",
            "heading_rad",
            "line_sensor")
    message = getFieldsFromDict(robot.__dict__, fields_to_send)
    message["front_range_m"] = robot.front_range.value
    socket.send(message)
    return False

@task
def ReceiveSensors(robot, socket:RemoteControlSocket):
    message = socket.receive()
    if message:
        robot.left_bumper_hit = message.get("left_bumper_hit", False)
        robot.right_bumper_hit = message.get("right_bumper_hit", False)
        robot.travelled_distance = message.get("travelled_distance", 0)
        robot.heading_rad = message.get("heading_rad", 0)
        robot.line_sensor = message.get("line_sensor", False)
        robot.front_range.value = message.get("front_range_m", robot.front_range.max_range)
    return False
