#INCOMPLETE
#this is mostly a proto with a bit of parsing
import socket
from multiprocessing import Process, Value
import TrboDataSvc.util as util
import logging
class BatteryMgmtOpCodes():
    RADIO_HELLO = b'\x02'
    HELLO_ACK = b'\x03'
    BATT_REQUEST = b'\x04'
    BATT_RESPONSE = b'\x05'

class BatteryOTA():
    def __init__(self, port=4012):
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
            rid = util.ip2id(ip)

            logging.debug("Got an Impres OTA message from radio {}: {}".format(rid, data))

    def _decodeSerialNumber(self, dataIn):
        serialBytes = dataIn[4:11]
        #flip the bytes
        serialString = ""
        #iterate backwards
        for i in range(5,-1,-1):
            stringByte = "{0:0{1}X}".format(serialBytes[i],2)
            serialString += stringByte
        return serialString

    def _decodePartNumber(dataIn):
        partNumber = dataIn[11:21]
        return partNumber.decode()

    def _decodeChargeAdded(self, dataIn):
        fields = []
        offset = 65
        #add a 0 to the start, i have no clue where the 0th byte is stored in the response
        fields.append(0)
        for i in range(1, 10):
            #convert byte to int
            field = int.from_bytes(dataIn[offset:offset+1], "big")
            fields.append(field)
            #the fields are separated by a null or space i forget
            #either way, exclude it and skip the offset up two
            offset+=2
        return fields

    def _decodeChargeRemaining(self, dataIn):
        fields = []
        offset = 83
        for i in range(0, 10):
            #convert byte to int
            field = int.from_bytes(dataIn[offset:offset+1], "big")
            fields.append(field)
            offset+=2
        return fields

    def decodeBatteryResponse(self, dataIn):
        #init empty dict
        message = {}
        message['serialNumber'] = self._decodeSerialNumber(dataIn)
        message['partNumber'] = self._decodePartNumber(dataIn)
        message['chargeAddedHist'] =  self._decodeChargeAdded(dataIn)
        message['chargeRemainingHist'] =  self._decodeChargeRemaining(dataIn)
        return message