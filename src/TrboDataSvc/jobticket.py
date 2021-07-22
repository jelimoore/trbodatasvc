import socket
from multiprocessing import Process, Value
import TrboDataSvc.util as util
import logging

class JobTicket():
    def __init__(self, port=4013):
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
            ip, port = addr
            rid = util.ip2id(self._cai, ip)
            logging.debug("Received job ticket data from radio {}: {}".format(rid, data))
            # Send the ack if the callback returns true
            #if (self._callback(rid, messageType) == True):
            #    self._sendAck(rid)