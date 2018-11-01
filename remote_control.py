import sys
import rx
import msgpack

from rx.concurrency import QtScheduler
from PyQt5 import QtCore
from PyQt5.QtCore import QObject, QUrl, pyqtSignal, pyqtSlot, pyqtProperty
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication
from collections import defaultdict
from roboutils.remote import RemoteControlSocket

manual = False
release = False

#ip = '192.168.43.21' # TODO: Replace IP here!
ip = 'localhost'
scheduler = QtScheduler(QtCore)

# Create a TCP/IP socket
sock = RemoteControlSocket(port = 8004, remote_address = (ip, 8002))

class Backend(QObject):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.keys = defaultdict(lambda:False)
        self.seq_no = 0
        self.robot_state = 0

    @pyqtSlot(str, bool)
    def forward(self, pressed, down):
        self.keys[pressed] = down
        print("Forward {} is {}".format(pressed, 'down' if down else 'up') )
    
    @pyqtSlot(int)
    def releaseManual(self, challenge_id):
        print("Go to challenge %d"%challenge_id)
        self.robot_state = challenge_id

    def get_command(self):
        forward = self.keys['w'] and not self.keys['s']
        backward = self.keys['s'] and not self.keys['w']
        right = self.keys['d'] and not self.keys['a']
        left  = self.keys['a'] and not self.keys['d']
        fwd_speed = 0
        turn_speed = 0

        if forward:
            fwd_speed = 0.14
        if backward:
            fwd_speed = -0.14
        if right:
            turn_speed = -1.24
        if left:
            turn_speed = 1.24
        return {"velocity_command": fwd_speed,
            "turn_command": turn_speed,
            "state": self.robot_state }

    def send_packet(self, _):
        command = self.get_command()
        #print("Sending: %s"%str(command))
        sock.send(command)

app = QApplication(sys.argv)
backend = Backend()

engine = QQmlApplicationEngine()
engine.rootContext().setContextProperty("backend", backend)
engine.load('qml/keys.qml')

win = engine.rootObjects()[0]
win.show()

rx.Observable.interval(1000/30, scheduler=scheduler).subscribe(backend.send_packet)

app.exec_()
