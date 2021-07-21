import socket
from multiprocessing import Process, Value
import util
import logging

class TMS():
    def __init__(self, port=4007):
        self._ip = "0.0.0.0"
        self._cai = 12
        self._gcai = 225
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

            if (opByte == b'\xbf' or opByte == b'\x9f'):
                self._handleTmsAck(data, addr)
            else:
                self._handleMessage(data, addr)

    def _handleTmsAck(self, dataIn, addrIn):
        #TODO - queue messages and repeat sending them until ACK is received. for now, drop it on the floor
        ip, port = addrIn
        logging.info("Ack received from {}".format(util.ip2id(ip)))

    def _handleMessage(self, dataIn, addrIn):
        ip, port = addrIn
        rid = util.ip2id(ip)
        messageText = self._decodeMessage(dataIn)
        if (self._callback(rid, messageText) == True):
            self._sendAck(rid, dataIn)

    def sendMessage(self, rid, message):
        ip = util.id2ip(self._cai, int(rid))
        messageBytes = self._generateMessage(message)
        self._sock.sendto(messageBytes, (ip, self._port))

    def sendGroupMessage(self, gid, message):
        ip = util.ip2id(self._gcai, int(gid))
        messageBytes = self._generateMessage(message)
        self._sock.sendto(messageBytes, (ip, self._port))

    def _generateMessage(self, input):
        #TODO: make the r and n actually bytes not just the character representation
        respHeader = b'\xc0\x00\x88\x04\r\x00\n'
        #start off the body with a null
        respBody = b'\x00'
        for c in input:
            #encode the byte, add a null to the end, then add it to the message
            cByte = c.encode()
            respBody += cByte + b'\x00'
        headerAndBody = respHeader + respBody
        length = len(headerAndBody)
        length = length.to_bytes(1, "big")
        message = b'\x00' + length + headerAndBody
        return message

    def _decodeMessage(self, dataIn):
        message = dataIn[9:]
        #replace the nulls with nothing so string compare works
        message = message.replace(b'\x00', b'').decode()
        return message

    def _sendAck(self, rid, dataIn):
        ip = util.id2ip(self._cai, rid)
        length = dataIn[1:2]
        opByte = dataIn[2:3]
        seqId = dataIn[4:5]
        ackOpByte = None
        #TODO: a0 means no ack needed, save the precious air time and don't send an ack if we don't have to
        #I also don't think the exact op byte sent matters as long as it's bf or 9f, will need to check to be sure though
        '''
        if (opByte == b'\xc0'):
            ackOpByte = b'\xbf'
        else:
            ackOpByte = b'\x9f'
        '''
        ackOpByte = b'\x9f'

        intSeqId = int.from_bytes(seqId, "big")
        ackSeqId = intSeqId - 128
        ackSeqId = ackSeqId.to_bytes(1, "big")
        ackMessage = b'\x00\x03' + ackOpByte + b'\x00' + ackSeqId
        self._sock.sendto(ackMessage, (ip, self._port))