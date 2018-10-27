import socket
import time
import kinematics as kine
import msgpack

class RemoteControlSocket:
    safety_time = 3.0
    def __init__(self, port, state_dict = None, remote_address = None):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ("", port)
        self.sock.bind(server_address)
        self.sock.setblocking(0)
        self.state = state_dict or {}
        self.last_received = time.time()
        self.tx_seq_no = 0
        self.rx_seq_no = 0 
        self.remote_address = remote_address
    def receive(self):
        """Receive message and update the state dictionary with the received fields"""
        try:
            data, client = self.sock.recvfrom(128)
            new_message = msgpack.loads(data, encoding = "UTF-8")
            if new_message[0] < 10:
                self.tx_seq_no = 0
            if new_message[0] < 10 or new_message[0] > self.rx_seq_no:
                self.rx_seq_no = new_message[0]
                self.state.update(new_message[1])
                self.remote_address = client
                self.last_received = time.time()
        except BlockingIOError:
            pass
        return self.state
    def send(self, message):
        if self.remote_address:
            data = msgpack.dumps([self.tx_seq_no, message], encoding = "UTF-8")
            self.sock.sendto(data, self.remote_address)
            self.tx_seq_no += 1
    def send_fields(self, fields):
        """Send selected fields from the state dictionary"""
        message = {k: self.state.get(k, None) for k in fields}
        self.send(message)
    def is_timeout(self):
        return time.time() - self.last_received > self.safety_time