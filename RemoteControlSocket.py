import socket
import time
import kinematics as kine
import msgpack

class RemoteControlSocket:
    safety_time = 3.0
    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        server_address = ("", 8000)
        self.sock.bind(server_address)
        self.sock.setblocking(0)
        self.message = [-1,0,0,0,0]
        self.last_received = time.time()
        self.tx_seq_no = 0
        self.rx_seq_no = 0 
        self.client_address = None
    def receive(self):
        try:
            data, client = self.sock.recvfrom(128)
            new_message = msgpack.loads(data, encoding = "UTF-8")
            if new_message[0] < 10:
                self.tx_seq_no = 0
            if new_message[0] < 10 or new_message[0] > self.rx_seq_no:
                self.rx_seq_no = new_message[0]
                self.message = new_message
                self.client_address = client
                self.last_received = time.time()
                print(str(client))
        except BlockingIOError:
            pass
        return kine.Command(self.message[1], self.message[2]), int(self.message[4])
    def reply(self, message):
        if self.client_address:
            data = msgpack.dumps([self.tx_seq_no, message], encoding = "UTF-8")
            self.sock.sendto(data, self.client_address)
            self.tx_seq_no += 1
    def is_timeout(self):
        return time.time() - self.last_received > self.safety_time