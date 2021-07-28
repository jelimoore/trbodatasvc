import socket
from multiprocessing import Process, Value
import TrboDataSvc.util as util
import logging

class LrrpBytes():
    LRRP_ACK = b'\x38'
    LRRP_SIMPLE_POINT = b'\x66'

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
3m point+time: 09 07 23 01 52 34 31 81 34   b4
4m point+time: 09 07 23 01 52 34 31 81 70   f0
5m point+time: 09 07 23 01 52 34 31 82 2c   12c
'''
class LRRP():
    LRRP_SP = 1
    LRRP_SP_TIME = 2
    LRRP_SP_ACCURACY = 3
    LRRP_SP_ACCURACY_SPEED = 4
    LRRP_SP_ACCURACY_SPEED_DIRECTION = 5
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
            rid = util.ip2id(ip)
            opByte = data[2:3]
            if (opByte == LrrpBytes.LRRP_ACK):
                #nothing to do, this is acking our request
                logging.debug("Got an LRRP ack from {}".format(rid))
            elif (opByte == LrrpBytes.LRRP_SIMPLE_POINT):
                simpleBytes = data[3:11]
                lat, lon = self._decodeSimplePoint(simpleBytes)
                logging.debug("Got an LRRP simple point from radio {}: {} {}".format(rid, lat, lon))
                geoDict = {}
                geoDict['type'] = LRRP.LRRP_SP
                geoDict['lat'] = lat
                geoDict['lon'] = lon
                self._callback(rid, geoDict)
            else:
                logging.warning("Got unknown LRRP opbyte from {}: ".format(rid, opByte))

    def _decodeSimplePoint(self, bytesIn):
        latBytes = bytesIn[:4]
        lonBytes = bytesIn[4:]
        lat = self._decodeLat(latBytes)
        lon = self._decodeLon(lonBytes)
        return lat, lon

    def _decodeLat(self, data):
        num = int.from_bytes(data, "big")
        # wrap number if two's complement
        if (num > 2147483647):
            num = ~num ^ 0xFFFFFFFF
        lat = num * (180.0 / 0xFFFFFFFF)
        return round(lat, 6)

    def _decodeLon(self, data):
        num = int.from_bytes(data, "big")
        # wrap number if two's complement
        if (num > 2147483647):
            num = ~num ^ 0xFFFFFFFF
        lon = num * (360.0 / 0xFFFFFFFF)
        return round(lon, 6)

    def sendIntervalRequest(self, rid, seconds):
        """Sends a request to the radio to send its location every n seconds."""

        # request goes like 09 07 23 01 52 34 31 81 34
        #the last byte or two are the seconds of the interval, i.e. wait this many seconds before sending loc
        #31 is the opbyte meaning time interval - this many seconds
        #one byte after that means that many seconds as decimal - 3c is 60s
        #two bytes gets interesting though
        #81 34 means 80 + 34 = b4
        #82 2c means 80 + 80 + 2c = 01 2c
        divisions = 0
        while seconds > 128:
            seconds = seconds - 128
            divisions += 1

        multiplierBytes = int(128 + divisions).to_bytes(1, "big")
        secondBytes = int(seconds).to_bytes(1, "big")

        if (multiplierBytes == b'\x80'):
            intervalBytes = secondBytes
        else:
            intervalBytes = multiplierBytes + secondBytes
        
        requestBody = b'\x23\x01\x52\x34\x31' + intervalBytes
        #get the length of the request and send it
        length = len(requestBody)
        length = length.to_bytes(1, "big")
        request = b'\x09' + length + requestBody
        ip = util.id2ip(self._cai, rid)
        self._sock.sendto(request, (ip, self._port))

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