#INCOMPLETE
#this is mostly a proto with a bit of parsing
import binascii
class BatteryMgmtOpCodes():
    RADIO_HELLO = b'\x02'
    HELLO_ACK = b'\x03'
    BATT_REQUEST = b'\x04'
    BATT_RESPONSE = b'\x05'

def _decodeSerialNumber(dataIn):
    serialBytes = dataIn[4:11]
    #flip the bytes
    serialString = ""
    for i in range(5,-1,-1):
        stringByte = "{0:0{1}X}".format(serialBytes[i],2)
        serialString += stringByte
    return serialString

def _decodePartNumber(dataIn):
    partNumber = dataIn[11:21]
    return partNumber.decode()

def _decodeChargeAdded(dataIn):
    fields = []
    #fields[0] = ???
    offset = 65
    #add a 0 to the start, i have no clue where the 0th byte is stored in the response
    fields.append(0)
    for i in range(1, 10):
        #convert byte to int
        field = int.from_bytes(dataIn[offset:offset+1], "big")
        fields.append(field)
        offset+=2
    return fields

def _decodeChargeRemaining(dataIn):
    fields = []
    #fields[0] = ???
    offset = 83
    for i in range(0, 10):
        #convert byte to int
        field = int.from_bytes(dataIn[offset:offset+1], "big")
        fields.append(field)
        offset+=2
    return fields

def decodeBatteryResponse(dataIn):
    #init empty dict
    message = {}
    message['serialNumber'] = _decodeSerialNumber(dataIn)
    message['partNumber'] = _decodePartNumber(dataIn)
    message['chargeAddedHist'] =  _decodeChargeAdded(dataIn)
    message['chargeRemainingHist'] =  _decodeChargeRemaining(dataIn)
    return message