import socket
from multiprocessing import Process, Value
import util
import logging

class LrrpConsts():
    LRRP_UNDEF = 0

class LrrpOpByte():
    ARS_HELLO = b'\xf0'


class LRRP():
    def __init__(self, port=4001):
        self._ip = "0.0.0.0"
        self._cai = 12
        self._port = port
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._callback = None

    def register_callback(self, callback):
        """ Allow callback to be registered """
        self._callback = callback

    def listen(self):
        #start listening on specified UDP port
        self._sock.bind((self._ip, self._port))
        #create subprocess for listening so we don't tie up the main thread of whoever called us
        p = Process(target=self._listenForIncoming)
        p.start()
        #p.join()
    
    def _listenForIncoming(self):
        while True:
            data, addr = self._sock.recvfrom(1024)

            logging.debug("Got an LRRP message from radio {}: {}".format(rid, messageType))
            print(data)