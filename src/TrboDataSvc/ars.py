import socket
from multiprocessing import Process, Value
import TrboDataSvc.util as util
import logging

class ArsConsts():
    ARS_ID_MISMATCH = -1
    ARS_UNDEF = 0
    ARS_HELLO = 1
    ARS_BYE = 2
    ARS_PING = 3
    ARS_PONG = 4

class ArsOpByte():
    ARS_HELLO = b'\xf0'
    ARS_BYE = b'\x31'
    ARS_PING = b'\x74'
    ARS_PONG = b'\x3f'

class ARS():
    def __init__(self, port=4005):
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
            
            opByte = data[2:3]
            ip, port = addr
            rid = util.ip2id(ip)
            ack_needed = False                  # do we need to send an ack for the message? let's save air time if we don't need to
            messageType = ArsConsts.ARS_UNDEF   # initialize the messageType var with an undefined value, use as fallback
            if (opByte == ArsOpByte.ARS_BYE):   # bye message
                #no need for an ack on bye, the radio is going away!
                ack_needed = False
                messageType = ArsConsts.ARS_BYE
            if (opByte == ArsOpByte.ARS_HELLO): # hello message
                # let's check that the ID being hello'ed and the sending radio are the same!
                #content = dataIn[5:] # strip the header
                #arsId = content.replace(b'\x00', b'').decode() # remove trailing nulls
                #print("IP ID: {} ARS ID: {}".format(id, arsId))
                #if (arsId == id):
                #    messageType = ArsConsts.ARS_HELLO
                #else:
                #    messageType = ArsConsts.ARS_ID_MISMATCH
                messageType = ArsConsts.ARS_HELLO
                ack_needed = True
            if (opByte == ArsOpByte.ARS_PONG):  # pong message
                #no ack needed, since this is a response
                ack_needed = False
                messageType = ArsConsts.ARS_PONG

            logging.debug("Got an ARS message from radio {}: {}".format(rid, messageType))
            # Send the ack if the callback returns true
            if (self._callback(rid, messageType) == True and ack_needed == True):
                self._sendAck(rid)

    def _sendAck(self, rid):
        ackMessage = b'\x00\x02\xbf\x01'
        ip = util.id2ip(self._cai, rid)
        logging.debug("Sending ARS Ack to {}".format(rid))
        self._sock.sendto(ackMessage, (ip, 4005))

    def queryRadio(self, rid):
        ip = util.id2ip(self._cai, int(rid))
        queryMessage = b'\x00\x01\x74'
        self._sock.sendto(queryMessage, (ip, 4005))