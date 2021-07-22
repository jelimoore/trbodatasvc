import socket
from multiprocessing import Process, Value
import TrboDataSvc.util as util
import logging

class LrrpConsts():
    LRRP_UNDEF = 0

'''
byte 0: const?
byte 1: length
byte 2: const?
byte 3: sequence number
byte 4: request type
    50: point+accuracy
    52: point+time
byte 5: extra
    62: speed


1shot:
point+time  09 04 23 01 52 33
point+acc   09 04 23 01 50 33
pt+acc+spd  09 05 23 01 50 62 33
pt+acc+spd+d09 06 23 01 50 62 57 33
3pt         09 04 23 01 54 33
3pt+acc+spd 09 04 23 01 50 54 62 33
3pt+ac+t+spd09 04 23 01 51 54 62 33

period:
1m point+time: 09 06 23 01 52 34 31 3c
2m point+time: 09 06 23 01 52 34 31 78
3m point+time: 09 06 23 01 52 34 31 81 34   b4
4m point+time: 09 06 23 01 52 34 31 81 70   f0
5m point+time: 09 06 23 01 52 34 31 82 2c   12c
'''
class LRRP():
    LRRP_SP_TIME = 1
    LRRP_SP_ACCURACY = 2
    LRRP_SP_ACCURACY_SPEED = 3
    LRRP_SP_ACCURACY_SPEED_DIRECTION = 4
    LRRP_3DP = 10
    LRRP_3DP_ACCURACY_SPEED = 11
    LRRP_ACCURACY_TIME_SPEED = 12

    def __init__(self, port=4001):
        self._ip = "0.0.0.0"
        self._cai = 12
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._process = Process(target=self._listenForIncoming)
        self._callback = None

    def register_callback(self, callback):
        """ Allow callback to be registered """
        self._callback = callback

    def listen(self):
        #start listening on specified UDP port
        self._sock.bind((self._ip, self._port))
        self._process.start()
        #p.join()

    def close(self):
        logging.info("Closing connection, bye!")
        self._sock.close()
        self._process.terminate()
    
    def _listenForIncoming(self):
        while True:
            data, addr = self._sock.recvfrom(1024)
            ip, port = addr
            rid = util.ip2id(self._cai, ip)
            logging.debug("Got an LRRP message from radio {}: {}".format(rid, data))

    def sendImmediateRequest(self, rid):
        request = b'\x09\x01\x33'
        ip = util.id2ip(self._cai, rid)
        self._sock.sendto(request, (ip, self._port))

    def sendStopRequests(self, rid):
        request = b'\x0f\x02\x23\x01'
        ip = util.id2ip(self._cai, rid)
        self._sock.sendto(request, (ip, self._port))

    def send(self, rid, bytes):
        ip = util.id2ip(self._cai, rid)
        self._sock.sendto(bytes, (ip, self._port))