#
# Python function library for PAKBUS communication
#
# (c) 2009 Dietrich Feist, Max Planck Institute for Biogeochemistry, Jena Germany
# 2025: Ported to Python 3 using Claude Sonnet 4
#
# Licensed under the GNU General Public License
#
# References:
#
# [1] BMP5 Transparent Commands Manual, Rev. 9/08, Campbell Scientific Inc., 2008
# [2] PakBus Networking Guide for the CR10X, CR510, CR23X, and CR200 Series
#     and LoggerNet 2.1C, Rev. 3/05, Campbell Scientific Inc., 2004-2005
#
# $Id: pakbus.py 40 2009-12-14 19:45:46Z dfeist $
#


#
# Global imports
#
import struct
import socket
import serial

#
# Global definitions
#
datatype = {
    #
    # data type summary table, check [1] Appendix A for details
    #
    # name        code        format        size
    #
    'Byte':     { 'code':  1, 'fmt': 'B',   'size': 1 },
    'UInt2':    { 'code':  2, 'fmt': '>H',  'size': 2 },
    'UInt4':    { 'code':  3, 'fmt': '>L',  'size': 4 },
    'Int1':     { 'code':  4, 'fmt': 'b',   'size': 1 },
    'Int2':     { 'code':  5, 'fmt': '>h',  'size': 2 },
    'Int4':     { 'code':  6, 'fmt': '>l',  'size': 4 },
    'FP2':      { 'code':  7, 'fmt': '>H',  'size': 2 },
    'FP3':      { 'code': 15, 'fmt': '3c',  'size': 3 },
    'FP4':      { 'code':  8, 'fmt': '4c',  'size': 4 },
    'IEEE4B':   { 'code':  9, 'fmt': '>f',  'size': 4 },
    'IEEE8B':   { 'code': 18, 'fmt': '>d',  'size': 8 },
    'Bool8':    { 'code': 17, 'fmt': 'B',   'size': 1 },
    'Bool':     { 'code': 10, 'fmt': 'B',   'size': 1 },
    'Bool2':    { 'code': 27, 'fmt': '>H',  'size': 2 },
    'Bool4':    { 'code': 28, 'fmt': '>L',  'size': 4 },
    'Sec':      { 'code': 12, 'fmt': '>l',  'size': 4 },
    'USec':     { 'code': 13, 'fmt': '6c',  'size': 6 },
    'NSec':     { 'code': 14, 'fmt': '>2l', 'size': 8 },
    'ASCII':    { 'code': 11, 'fmt': 's',   'size': None },
    'ASCIIZ':   { 'code': 16, 'fmt': 's',   'size': None },
    'Short':    { 'code': 19, 'fmt': '<h',  'size': 2 },
    'Long':     { 'code': 20, 'fmt': '<l',  'size': 4 },
    'UShort':   { 'code': 21, 'fmt': '<H',  'size': 2 },
    'ULong':    { 'code': 22, 'fmt': '<L',  'size': 4 },
    'IEEE4L':   { 'code': 24, 'fmt': '<f',  'size': 4 },
    'IEEE8L':   { 'code': 25, 'fmt': '<d',  'size': 8 },
    'SecNano':  { 'code': 23, 'fmt': '<2l', 'size': 8 },
}

#
# Link states
#
LS_OFFLINE  = 0b1000
LS_RING     = 0b1001
LS_READY    = 0b1010
LS_DONE     = 0b1011
LS_PAUSE    = 0b1100

#
# Global variables
#
transact = 0     # Running 8-bit transaction counter

#
# Send packet over PakBus
#
# - add signature nullifier
# - quote \xBC and \xBD characters
# - frame packet with \xBD characters
#
def send(s, pkt):
    #
    # pkt must be a bytes object
    #
    frame = quote(pkt + calcSigNullifier(calcSigFor(pkt)))
    msg = b'\xBD' + frame + b'\xBD'
    # print("Sending: ", "".join([hex(b) for b in msg]))
    s.write(msg)


#
# Receive packet over PakBus
#
# - remove framing \xBD characters
# - unquote quoted \xBC and \xBD characters
# - check signature
#
def recv(s):
    #
    # returns a bytes object
    #
    
    # Read until first \xBD frame character
    byte = s.read(1)
    while byte != b'\xBD':
        byte = s.read(1)
        if not byte:
            raise socket.timeout("PakBus: timeout waiting for start of frame")

    # Read until character other than \xBD
    while byte == b'\xBD':
        byte = s.read(1)
        if not byte:
            raise socket.timeout("PakBus: timeout waiting for packet content")

    # Read until next occurence of \xBD character
    msg = b''
    while byte != b'\xBD':
        msg += byte
        byte = s.read(1)
        if not byte:
            raise socket.timeout("PakBus: timeout waiting for end of frame")

    frame = unquote(msg)
    
    sig = calcSigFor(frame[:-2])
    if calcSigNullifier(sig) != frame[-2:]:
        raise Exception("PakBus: checksum error")

    return frame[:-2]


#
# Generate new 8-bit transaction number
#
def newTranNbr():
    global transact
    transact += 1
    transact &= 0xFF
    return transact


################################################################################
#
# [1] section 1.3 PakBus Packet Headers
#
################################################################################

#
# Generate PakBus header
#
def PakBus_hdr(DstNodeId, SrcNodeId, HiProtoCode, ExpMoreCode = 0x2, LinkState = LS_READY, Priority = 0x1, HopCnt = 0x0, DstPhyAddr = None, SrcPhyAddr = None):
    #
    # DstNodeId, SrcNodeId must be integers
    # HiProtoCode, ExpMoreCode, LinkState, Priority, HopCnt must be integers
    # DstPhyAddr, SrcPhyAddr must be integers
    #
    # returns a bytes object
    #
    if DstPhyAddr is None: DstPhyAddr = DstNodeId
    if SrcPhyAddr is None: SrcPhyAddr = SrcNodeId

    hdr = struct.pack('>4H',
        (LinkState & 0xF) << 12   | (DstPhyAddr & 0xFFF),
        (ExpMoreCode & 0x3) << 14 | (Priority & 0x3) << 12 | (SrcPhyAddr & 0xFFF),
        (HiProtoCode & 0xF) << 12 | (DstNodeId & 0xFFF),
        (HopCnt & 0xF) << 12      | (SrcNodeId & 0xFFF)
    )
    return hdr


################################################################################
#
# [1] section 1.4 Encoding and DecodiI'mng Packets
#
################################################################################

#
# Calculate signature for PakBus packets
#
def calcSigFor(buff, seed = 0xAAAA):
    #
    # buff must be a bytes object
    #
    # returns an integer
    #
    sig = seed
    for x in buff:
        j = sig
        sig = (sig << 1) & 0x1FF
        if sig >= 0x100: sig += 1
        sig = ((((sig + (j >> 8) + x) & 0xFF) | (j << 8))) & 0xFFFF
    return sig

#
# Calculate signature nullifier needed to create valid PakBus packets
#
def calcSigNullifier(sig):
    #
    # sig must be an integer
    #
    # returns a bytes object
    #
    nulb = b''
    nullif = b''
    for i in (1, 2):
        sig = calcSigFor(nulb, sig)
        sig2 = (sig << 1) & 0x1FF
        if sig2 >= 0x100:
            sig2 += 1
        b = (0x100 - (sig2 + (sig >> 8))) & 0xFF
        nulb = struct.pack('B', b)
        nullif += nulb
    return nullif

#
# Quote PakBus packet
#
def quote(pkt):
    #
    # pkt must be a bytes object
    #
    # returns a bytes object
    #
    pkt = pkt.replace(b'\xBC', b'\xBC\xDC')
    pkt = pkt.replace(b'\xBD', b'\xBC\xDD')
    return pkt

#
# Unquote PakBus packet
#
def unquote(pkt):
    #
    # pkt must be a bytes object
    #
    # returns a bytes object
    #
    pkt = pkt.replace(b'\xBC\xDD', b'\xBD')
    pkt = pkt.replace(b'\xBC\xDC', b'\xBC')
    return pkt

################################################################################
#
# [1] section 2.1 Serial Link Control Packets (SerPkt)
#
################################################################################

def link_ring_cmd(DstNodeId, SrcNodeId):
    #
    # DstNodeId, SrcNodeId must be integers
    #
    # returns a bytes object
    #
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x70, LinkState = LS_RING)
    
    return hdr + calcSigNullifier(calcSigFor(hdr))

#


################################################################################
#
# [1] section 2.2 PakBus Control Packets (PakCtrl)
#
################################################################################

################################################################################
#
# [1] section 2.2.1 Deliverry Failure Message (MsgType 0x81)
#
################################################################################

#
# still missing ...
#


################################################################################
#
# [1] section 2.2.2 Hello Transaction (MsgType 0x09 & 0x89)
#
################################################################################

#
# Create Hello Command packet
#
def pkt_hello_cmd(DstNodeId, SrcNodeId, IsRouter = 0x00, HopMetric = 0x02, VerifyIntv = 1800):
    #
    # DstNodeId, SrcNodeId must be integers
    # IsRouter, HopMetric, VerifyIntv must be integers
    #
    # returns a tuple of (bytes object, transaction number)
    #
    TranNbr = newTranNbr()
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x0, 0x1, 0x9) # PakBus Control Packet
    msg = encode_bin(['Byte', 'Byte', 'Byte', 'Byte', 'UInt2'], [0x09, TranNbr, IsRouter, HopMetric, VerifyIntv])
    pkt = hdr + msg
    return pkt, TranNbr

#
# Create Hello Response packet
#
def pkt_hello_response(DstNodeId, SrcNodeId, TranNbr, IsRouter = 0x00, HopMetric = 0x02, VerifyIntv = 1800):
    #
    # DstNodeId, SrcNodeId, TranNbr must be integers
    # IsRouter, HopMetric, VerifyIntv must be integers
    #
    # returns a bytes object
    #
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x01)
    msg = struct.pack('B', 0x89) + struct.pack('B', TranNbr) + struct.pack('>H', VerifyIntv) + struct.pack('B', IsRouter) + struct.pack('B', HopMetric)

    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode Hello Command/Response packet
#
def msg_hello(msg):
    # msg: decoded default message - must contain msg['raw']
    [msg['IsRouter'], msg['HopMetric'], msg['VerifyIntv']], size = decode_bin(['Byte', 'Byte', 'UInt2'], msg['raw'][2:])
    return msg


################################################################################
#
# [1] section 2.2.3 Hello Request Message (MsgType 0x0e)
#
################################################################################

#
# still missing ...
#


################################################################################
#
# [1] section 2.2.4 Bye Message (MsgType 0x0d)
#
################################################################################

#
# Create Bye Command packet
#
def pkt_bye_cmd(DstNodeId, SrcNodeId):
    #
    # DstNodeId, SrcNodeId must be integers
    #
    # returns a bytes object
    #
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x01)
    msg = struct.pack('B', 0x0D)

    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))


################################################################################
#
# [1] section 2.2.5 Get/Set String Settings Transactions (MsgType 0x07, 0x87, 0x08, & 0x88)
#
################################################################################

#
# still missing ... (only useful for CR200)
#


################################################################################
#
# [1] section 2.2.6.1 DevConfig Get Settings Message (MsgType 0x0f & 0x8f)
#
################################################################################

#
# Create DevConfig Get Settings Command packet
#
def pkt_devconfig_get_settings_cmd(DstNodeId, SrcNodeId, BeginSettingId = None, EndSettingId = None, SecurityCode = 0x0000):
    #
    # DstNodeId, SrcNodeId must be integers
    # BeginSettingId, EndSettingId, SecurityCode must be integers
    #
    # returns a bytes object
    #
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x01)
    msg = struct.pack('B', 0x0F) + struct.pack('B', newTranNbr()) + struct.pack('>H', SecurityCode)
    
    if BeginSettingId is not None:
        msg += struct.pack('>H', BeginSettingId)
    if EndSettingId is not None:
        msg += struct.pack('>H', EndSettingId)

    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode DevConfig Get Settings Response packet
#
def msg_devconfig_get_settings_response(msg):
    # msg: decoded default message - must contain msg['raw']
    offset = 2
    [msg['Outcome']], size = decode_bin(['Byte'], msg['raw'][offset:])
    offset += size
    # Generate dictionary of all settings
    msg['Settings'] = []
    return msg

#
# Decode DevConfig Set Settings Response packet
#
def msg_devconfig_set_settings_response(msg):
    # msg: decoded default message - must contain msg['raw']
    offset = 2
    [msg['Outcome']], size = decode_bin(['Byte'], msg['raw'][offset:])
    offset += size
    msg['SettingStatus'] = []
    return msg

#
# Decode DevConfig Control Response packet
#
def msg_devconfig_control_response(msg):
    # msg: decoded default message - must contain msg['raw']
    offset = 2
    [msg['Outcome']], size = decode_bin(['Byte'], msg['raw'][offset:])
    return msg

#
# Decode Clock Response packet
#
def msg_clock_response(msg):
    # msg: decoded default message - must contain msg['raw']
    [msg['RespCode'], msg['Time']], size = decode_bin(['Byte', 'NSec'], msg['raw'][2:])
    return msg

#
# Decode Get Programming Statistics Response packet
#
def msg_getprogstat_response(msg):
    # msg: decoded default message - must contain msg['raw']
    [msg['RespCode']], size = decode_bin(['Byte'], msg['raw'][2:])
    return msg

#
# Decode File Download Response packet
#
def msg_filedownload_response(msg):
    # msg: decoded default message - must contain msg['raw']
    [msg['RespCode'], msg['FileOffset']], size = decode_bin(['Byte', 'UInt4'], msg['raw'][2:])
    return msg

#
# Decode File Upload Response packet
#
def msg_fileupload_response(msg):
    # msg: decoded default message - must contain msg['raw']
    [msg['RespCode'], msg['FileOffset']], size = decode_bin(['Byte', 'UInt4'], msg['raw'][2:7])
    msg['FileData'] = msg['raw'][7:] # return raw file data for later parsing
    return msg

#
# Decode File Control Response packet
#
def msg_filecontrol_response(msg):
    # msg: decoded default message - must contain msg['raw']
    [msg['RespCode'], msg['HoldOff']], size = decode_bin(['Byte', 'UInt2'], msg['raw'][2:])
    return msg


################################################################################
#
# [1] section 2.2.6.2 DevConfig Set Settings Message (MsgType 0x10 & 0x90)
#
################################################################################

#
# Create DevConfig Set Settings Command packet
#
def pkt_devconfig_set_settings_cmd(DstNodeId, SrcNodeId, Settings = [], SecurityCode = 0x0000):
    #
    # DstNodeId, SrcNodeId, SecurityCode must be integers
    # Settings must be a list of dictionaries
    #
    # returns a bytes object
    #
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x01)
    msg = struct.pack('B', 0x10) + struct.pack('B', newTranNbr()) + struct.pack('>H', SecurityCode)
    
    for s in Settings:
        msg += struct.pack('>H', s['Id'])
        msg += struct.pack('>H', len(s['Value']))
        msg += s['Value']

    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode DevConfig Set Settings Response packet
#
def msg_devconfig_set_settings_response(msg):
    #
    # msg must be a bytes object
    #
    # returns a dictionary
    #
    result = { 'TranNbr': msg[1], 'RespCode': msg[2], 'Settings': [] }
    
    i = 3
    while i < len(msg):
        result['Settings'].append({ 'Id': struct.unpack('>H', msg[i:i+2])[0], 'Ack': msg[i+2] })
        i += 3
        
    return result


################################################################################
#
# [1] section 2.2.6.3 DevConfig Get Setting Fragment Transaction Message (MsgType 0x11 & 0x91)
#
################################################################################

#
# still missing ...
#


################################################################################
#
# [1] section 2.2.6.4 DevConfig Set Setting Fragment Transaction Message (MsgType 0x12 & 0x92)
#
################################################################################

#
# still missing ...
#


################################################################################
#
# [1] section 2.2.6.4 DevConfig Control Transaction Message (MsgType 0x13 & 0x93)
#
################################################################################

#
# Create DevConfig Control Command packet
#
def pkt_devconfig_control_cmd(DstNodeId, SrcNodeId, Action = 0x04, SecurityCode = 0x0000):
    #
    # DstNodeId, SrcNodeId, Action, SecurityCode must be integers
    #
    # returns a bytes object
    #
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x01)
    msg = struct.pack('B', 0x13) + struct.pack('B', newTranNbr()) + struct.pack('>H', SecurityCode) + struct.pack('B', Action)

    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode DevConfig Control Response packet
#
def msg_devconfig_control_response(msg):
    #
    # msg must be a bytes object
    #
    # returns a dictionary
    #
    return { 'TranNbr': msg[1], 'RespCode': msg[2] }


################################################################################
#
# [1] section 2.3 BMP5 Application Packets
#
################################################################################

################################################################################
#
# [1] section 2.3.1 Please Wait Message (MsgType 0xa1)
#
################################################################################

#
# Create Please Wait Message packet
#

#
# still missing ...
#

#
# Decode Please Wait Message packet
#
def msg_pleasewait(msg):
    # msg: decoded default message - must contain msg['raw']
    [msg['CmdMsgType'], msg['WaitSec']], size = decode_bin(['Byte', 'UInt2'], msg['raw'][2:])
    return msg


################################################################################
#
# [1] section 2.3.2 Clock Transaction (MsgType 0x17 & 0x97)
#
################################################################################

#
# Create Clock Command packet
#
def pkt_clock_cmd(DstNodeId, SrcNodeId, Adjustment = (0, 0), SecurityCode = 0x0000):
    #
    # DstNodeId, SrcNodeId, SecurityCode must be integers
    # Adjustment must be a tuple of two integers
    #
    # returns a bytes object
    #
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x02)
    msg = struct.pack('B', 0x17) + struct.pack('B', newTranNbr()) + struct.pack('>H', SecurityCode) + struct.pack('>l', Adjustment[0]) + struct.pack('>L', Adjustment[1])

    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode Clock Response packet
#
def msg_clock_response(msg):
    #
    # msg must be a bytes object
    #
    # returns a dictionary
    #
    return { 'TranNbr': msg[1], 'RespCode': msg[2] }


################################################################################
#
# [1] section 2.3.3.1 File Download Transaction (MsgType 0x1c & 0x9c)
#
################################################################################

#
# Create File Download Command packet
#
def pkt_filedownload_cmd(DstNodeId, SrcNodeId, FileName, FileData, SecurityCode = 0x0000, FileOffset = 0x00000000, TranNbr = None, CloseFlag = 0x01, Attribute = 0x00):
    #
    # DstNodeId, SrcNodeId, SecurityCode, FileOffset, TranNbr, CloseFlag, Attribute must be integers
    # FileName must be a string
    # FileData must be a bytes object
    #
    # returns a bytes object
    #
    if TranNbr is None:
        TranNbr = newTranNbr()
    
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x02)
    msg = struct.pack('B', 0x1C) + struct.pack('B', TranNbr) + struct.pack('>H', SecurityCode) + struct.pack('B', len(FileName)) + FileName.encode('ascii') + struct.pack('>L', FileOffset) + struct.pack('B', CloseFlag) + struct.pack('B', Attribute) + FileData
    
    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode File Download Response packet
#
def msg_filedownload_response(msg):
    #
    # msg must be a bytes object
    #
    # returns a dictionary
    #
    return { 'TranNbr': msg[1], 'RespCode': msg[2] }


################################################################################
#
# [1] section 2.3.3.2 File Upload Transaction (MsgType 0x1d & 0x9d)
#
################################################################################

#
# Create File Upload Command packet
#
def pkt_fileupload_cmd(DstNodeId, SrcNodeId, FileName, SecurityCode = 0x0000, FileOffset = 0x00000000, TranNbr = None, CloseFlag = 0x01, Swath = 0x0200):
    #
    # DstNodeId, SrcNodeId, SecurityCode, FileOffset, TranNbr, CloseFlag, Swath must be integers
    # FileName must be a string
    #
    # returns a bytes object
    #
    if TranNbr is None:
        TranNbr = newTranNbr()
    
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x02)
    msg = struct.pack('B', 0x1D) + struct.pack('B', TranNbr) + struct.pack('>H', SecurityCode) + struct.pack('B', len(FileName)) + FileName.encode('ascii') + struct.pack('>L', FileOffset) + struct.pack('B', CloseFlag) + struct.pack('>H', Swath)
    
    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode File Upload Response packet
#
def msg_fileupload_response(msg):
    #
    # msg must be a bytes object
    #
    # returns a dictionary
    #
    return { 'TranNbr': msg[1], 'RespCode': msg[2], 'FileData': msg[3:] }


################################################################################
#
# [1] section 2.3.3.3 File Directory Format
#
################################################################################

#
# Parse File Directory Format
#
def parse_filedir(raw):
    #
    # raw must be a bytes object
    #
    # returns a list of dictionaries
    #
    files = []
    
    i = 0
    while i < len(raw):
        file = {}
        name_len = raw[i]
        i += 1
        file['Name'] = raw[i:i+name_len].decode('ascii')
        i += name_len
        file['Size'] = struct.unpack('>L', raw[i:i+4])[0]
        i += 4
        file['Timestamp'] = struct.unpack('>L', raw[i:i+4])[0]
        i += 4
        file['Attribute'] = raw[i]
        i += 1
        files.append(file)
        
    return files


################################################################################
#
# [1] section 2.3.3.4 File Control Transaction (MsgType 0x1e & 0x9e)
#
################################################################################

#
# Create File Control Transaction packet
#
def pkt_filecontrol_cmd(DstNodeId, SrcNodeId, FileName, FileCmd, SecurityCode = 0x0000, TranNbr = None):
    #
    # DstNodeId, SrcNodeId, FileCmd, SecurityCode, TranNbr must be integers
    # FileName must be a string
    #
    # returns a bytes object
    #
    if TranNbr is None:
        TranNbr = newTranNbr()
    
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x02)
    msg = struct.pack('B', 0x1E) + struct.pack('B', TranNbr) + struct.pack('>H', SecurityCode) + struct.pack('B', FileCmd) + struct.pack('B', len(FileName)) + FileName.encode('ascii')
    
    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode File Control Transaction Response packet
#
def msg_filecontrol_response(msg):
    #
    # msg must be a bytes object
    #
    # returns a dictionary
    #
    return { 'TranNbr': msg[1], 'RespCode': msg[2] }


################################################################################
#
# [1] section 2.3.3.5 Get Programming Statistics Transaction (MsgType 0x18 & 0x98)
#
################################################################################

#
# Create Get Programming Statistics Transaction packet
#
def pkt_getprogstat_cmd(DstNodeId, SrcNodeId, SecurityCode = 0x0000, TranNbr = None):
    #
    # DstNodeId, SrcNodeId, SecurityCode, TranNbr must be integers
    #
    # returns a bytes object
    #
    if TranNbr is None:
        TranNbr = newTranNbr()
    
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x02)
    msg = struct.pack('B', 0x18) + struct.pack('B', TranNbr) + struct.pack('>H', SecurityCode)
    
    return hdr + msg + calcSigNullifier(calcSigFor(hdr + msg))

#
# Decode Get Programming Statistics Transaction Response packet
#
def msg_getprogstat_response(msg):
    #
    # msg must be a bytes object
    #
    # returns a dictionary
    #
    return { 'TranNbr': msg[1], 'RespCode': msg[2], 'CompileState': msg[3], 'CompileFile': msg[4:4+16].split(b'\0', 1)[0].decode('ascii'), 'Sig': struct.unpack('>L', msg[20:24])[0], 'Owner': msg[24:24+20].split(b'\0', 1)[0].decode('ascii') }


################################################################################
#
# [1] section 2.3.4 Data Collection and Table Control Transactions
#
################################################################################

################################################################################
#
# [1] section 2.3.4.2 Getting Table Definitions and Table Signatures
#
################################################################################

#
# Parse table definition
#
def parse_tabledef(raw):
    # raw:      Raw coded data string containing table definition(s)

    TableDef = []   # List of table definitions

    offset = 0  # offset into raw buffer
    FslVersion, size = decode_bin(['Byte'], raw[offset:])
    offset += size

    # Parse list of table definitions
    while offset < len(raw):

        tblhdr = {}     # table header
        tblfld = []     # table field definitions
        start = offset  # start of table definition

        # Extract table header data
        [tblhdr['TableName'], tblhdr['TableSize'], tblhdr['TimeType'], tblhdr['TblTimeInto'], tblhdr['TblInterval']], size = decode_bin(['ASCIIZ', 'UInt4', 'Byte', 'NSec', 'NSec'], raw[offset:])
        offset += size

        # Extract field definitions
        while True:
            fld = {}
            [fieldtype], size = decode_bin(['Byte'], raw[offset:])
            offset += size

            # end loop when field list terminator reached
            if fieldtype == 0: break

            # Extract bits from fieldtype
            fld['ReadOnly'] = fieldtype >> 7    # only Bit 7

            # Convert fieldtype to ASCII FieldType (e.g. 'FP4') if possible, else return numerical value
            fld['FieldType'] = fieldtype & 0x7F # only Bits 0..6
            for Type in list(datatype.keys()):
                if fld['FieldType'] == datatype[Type]['code']:
                    fld['FieldType'] = Type
                    break

            # Extract field name
            [fld['FieldName']], size = decode_bin(['ASCIIZ'], raw[offset:])
            offset += size

            # Extract AliasName list
            fld['AliasName'] = []
            while True:
                [aliasname], size = decode_bin(['ASCIIZ'], raw[offset:])
                offset += size
                if aliasname == '': break # Alias names list terminator reached
                fld['AliasName'].append(aliasname)

            # Extract other mandatory field definition items
            [fld['Processing'], fld['Units'], fld['Description'], fld['BegIdx'], fld['Dimension']], size = decode_bin(['ASCIIZ', 'ASCIIZ', 'ASCIIZ', 'UInt4', 'UInt4'], raw[offset:])
            offset += size

            # Extract sub dimension (if any)
            fld['SubDim'] = []
            while True:
                [subdim], size = decode_bin(['UInt4'], raw[offset:])
                offset += size
                if subdim == 0: break # sub-dimension list terminator reached
                fld['SubDim'].append(subdim)

            # append current field definition to list
            tblfld.append(fld)

        # calculate table signature
        tblsig = calcSigFor(raw[start:offset])

        # Append header, field list and signature to table definition list
        TableDef.append({'Header': tblhdr, 'Fields': tblfld, 'Signature': tblsig})

    return TableDef


################################################################################
#
# [1] section 2.3.4.3 Collect Data Transaction (MsgType 0x09 & 0x89)
#
################################################################################

#
# Create Collect Data Command packet
#
def pkt_collectdata_cmd(DstNodeId, SrcNodeId, TableNbr, TableDefSig, FieldNbr = [], CollectMode = 0x05, P1 = 0, P2 = 0, SecurityCode = 0x0000):
    # DstNodeId:    Destination node ID (12-bit int)
    # SrcNodeId:    Source node ID (12-bit int)
    # TableNbr:     Table number
    # TableDefSig:  Table defintion signature
    # FieldNbr:     list of field numbers (empty to collect all)
    # CollectMode:  Collection mode code (P1 and P2 will be used depending on value)
    # P1:           1st parameter used to specify what to collect (optional)
    # P2:           2nd parameter used to specify what to collect (optional)
    # SecurityCode: security code of the data logger
    #
    # Note: theoretically, several requests with different TableNbr, Fieldnbr etc. could be
    #       requested in a single collect data command packet. This was not implemented
    #       on purpose, as the decoding of the retrieved packet is not trivial

    TranNbr = newTranNbr()  # Generate new transaction number
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x1) # BMP5 Application Packet
    msg = encode_bin(['Byte', 'Byte', 'UInt2', 'Byte'], [0x09, TranNbr, SecurityCode, CollectMode])

    # encode table number and signature
    msg += encode_bin(['UInt2', 'UInt2'], [TableNbr, TableDefSig])

    # add P1 and P2 according to CollectMode
    if (CollectMode == 0x04) | (CollectMode == 0x05): # only P1 used (type UInt4)
        msg += encode_bin(['UInt4'], [P1])
    elif (CollectMode == 0x06) | (CollectMode == 0x08): # P1 and P2 used (type UInt4)
        msg += encode_bin(['UInt4', 'UInt4'], [P1, P2])
    elif CollectMode == 0x07: # P1 and P2 used (type NSec)
        msg += encode_bin(['NSec', 'NSec'], [P1, P2])

    # add field list
    fieldlist = FieldNbr + [0]
    msg += encode_bin(len(fieldlist) * ['UInt2'], fieldlist)

    pkt = hdr + msg
    return pkt, TranNbr

#
# Decode Collect Data Response body
#
def msg_collectdata_response(msg_bytes):
    # msg_bytes: raw bytes of the message payload

    offset = 2
    resp_code, size = decode_bin(['Byte'], msg_bytes[offset:])
    offset += size

    rec_data = msg_bytes[offset:] # return raw record data for later parsing

    return {
        'RespCode': resp_code,
        'RecData': rec_data
    }

#
# Parse data returned by msg_collectdata_response(msg)
#
def parse_collectdata(raw, tabledef, FieldNbr = []):
    # raw:      Raw coded data string containing record data
    # tabledef: Table definition structure (as returned by parse_tabledef())
    # FieldNbr:     list of field numbers (empty to collect all)

    offset = 0
    recdata = [] # output structure

    while offset < len(raw) - 1:
        frag = {} # record fragment

        [frag['TableNbr'], frag['BegRecNbr']], size = decode_bin(['UInt2', 'UInt4'], raw[offset:])
        offset += size

        # Provide table name
        frag['TableName'] = tabledef[frag['TableNbr'] - 1]['Header']['TableName']

        # Decode number of records (16 bits) or ByteOffset (32 Bits)
        [isoffset], size = decode_bin(['Byte'], raw[offset:])
        frag['IsOffset'] = isoffset >> 7

        # Handle fragmented records (must be put together by external function)
        if frag['IsOffset']:
            [byteoffset], size = decode_bin(['UInt4'], raw[offset:])
            offset += size
            frag['ByteOffset'] = byteoffset & 0x7FFFFFFF
            frag['NbrOfRecs'] = None
            # Copy remaining raw data into RecFrag
            frag['RecFrag'] = raw[offset:-1]
            offset += len(frag['RecFrag'])

        # Handle complete records (standard case)
        else:
            [nbrofrecs], size = decode_bin(['UInt2'], raw[offset:])
            offset += size
            frag['NbrOfRecs'] = nbrofrecs & 0x7FFF
            frag['ByteOffset'] = None

            # Get time of first record and time interval information
            interval = tabledef[frag['TableNbr'] - 1]['Header']['TblInterval']
            if interval == (0, 0):  # event-driven table
                timeofrec = None
            else:                   # interval data, read time of first record
                [timeofrec], size = decode_bin(['NSec'], raw[offset:])
                offset += size

            # Loop over all records
            frag['RecFrag'] = []
            for n in range(frag['NbrOfRecs']):
                record = {}

                # Calculate current record number
                record['RecNbr'] = frag['BegRecNbr'] + n

                # Get TimeOfRec for interval data or event-driven tables
                if timeofrec:   # interval data
                    record['TimeOfRec'] = (timeofrec[0] + n * interval[0], timeofrec[1] + n * interval[1])
                else:           # event-driven, time data precedes each record
                    [record['TimeOfRec']], size = decode_bin(['NSec'], raw[offset:])
                    offset += size

                # Loop over all field indices
                record['Fields'] = {}
                if FieldNbr:    # explicit field numbers provided
                    fields = FieldNbr
                else:           # default: generate list of all fields in table
                    fields = list(range(1, len(tabledef[frag['TableNbr'] - 1]['Fields']) + 1))

                for field in fields:
                    fieldname = tabledef[frag['TableNbr'] - 1]['Fields'][field - 1]['FieldName']
                    fieldtype = tabledef[frag['TableNbr'] - 1]['Fields'][field - 1]['FieldType']
                    dimension = tabledef[frag['TableNbr'] - 1]['Fields'][field - 1]['Dimension']
                    # print("parsing %s: %s (%s)" % (field, fieldname, fieldtype)) 
                    if fieldtype == 'ASCII':
                        record['Fields'][fieldname], size = decode_bin([fieldtype], raw[offset:], dimension)
                    else:
                        record['Fields'][fieldname], size = decode_bin(dimension * [fieldtype], raw[offset:])
                    offset += size
                print("parsed fields")
                frag['RecFrag'].append(record)
        recdata.append(frag)
    return recdata

################################################################################
#
# [1] section 2.3.5 Get/Set Values Transaction (MsgType 0x1a, 0x9a, 0x1b, & 0x9b)
#
################################################################################

#
# Create Get Values Command packet
#
def pkt_getvalues_cmd(DstNodeId, SrcNodeId, TableName, Type, FieldName, Swath = 1, SecurityCode = 0x0000):
    # DstNodeId:    Destination node ID (12-bit int)
    # SrcNodeId:    Source node ID (12-bit int)
    # TableName:    Table name as string
    # Type:         Type name as defined in datatype (e.g. 'Byte')
    # FieldName:    Field name (including index if applicable)
    # Swath:        Number of columns to retrieve from an indexed field
    # SecurityCode: 16-bit security code (optional)

    TranNbr = newTranNbr()  # Generate new transaction number
    hdr = PakBus_hdr(DstNodeId, SrcNodeId, 0x1) # BMP5 Application Packet
    msg = encode_bin(['Byte', 'Byte', 'UInt2', 'ASCIIZ', 'Byte', 'ASCIIZ', 'UInt2'], [0x1a, TranNbr, SecurityCode, TableName, datatype[Type]['code'], FieldName, Swath])
    pkt = hdr + msg
    return pkt, TranNbr

#
# Decode Get Values Response packet
#
def msg_getvalues_response(msg):
    # msg: decoded default message - must contain msg['raw']
    [msg['RespCode']], size = decode_bin(['Byte'], msg['raw'][2:3])
    msg['Values'] = msg['raw'][3:] # return raw coded values for later parsing
    return msg

#
# Parse values retrieved from get values command
#
def parse_values(raw, Type, Swath = 1):
    # raw:      Raw coded data string containing values (as returned by decode_pkt)
    # Type:     Data type name as defined in datatype
    # Swath:    Number of columns to retrieve from an indexed field
    values, size = decode_bin(Swath * [Type], raw)
    return values


################################################################################
#
# Utility functions for encoding and decoding packets and messages
#
################################################################################

#
# Decode packet
#
def decode_pkt(pkt):
    # pkt: buffer containing unquoted packet, signature nullifier stripped

    # Initialize output variables
    hdr = {'LinkState': None, 'DstPhyAddr': None, 'ExpMoreCode': None, 'Priority': None, 'SrcPhyAddr': None, 'HiProtoCode': None, 'DstNodeId': None, 'HopCnt': None, 'SrcNodeId': None}
    msg = {'MsgType': None, 'TranNbr': None, 'raw': None}

    try:
        # decode PakBus header
        rawhdr = struct.unpack('>4H', pkt[0:8]) # raw header bits
        hdr['LinkState']   =  rawhdr[0] >> 12
        hdr['DstPhyAddr']  =  rawhdr[0] & 0x0FFF
        hdr['ExpMoreCode'] = (rawhdr[1] & 0xC000) >> 14
        hdr['Priority']    = (rawhdr[1] & 0x3000) >> 12
        hdr['SrcPhyAddr']  =  rawhdr[1] & 0x0FFF
        hdr['HiProtoCode'] =  rawhdr[2] >> 12
        hdr['DstNodeId']   =  rawhdr[2] & 0x0FFF
        hdr['HopCnt']      =  rawhdr[3] >> 12
        hdr['SrcNodeId']   =  rawhdr[3] & 0x0FFF

        # decode default message fields: raw message, message type and transaction number
        msg['raw'] = pkt[8:]
        [msg['MsgType'], msg['TranNbr']], size = decode_bin(['Byte', 'Byte'], msg['raw'][:2])
    except:
        pass

    # try to add fields from known message types
    try:
        msg = {
            # PakBus Control Packets
            (0, 0x09): msg_hello,
            (0, 0x89): msg_hello,
            (0, 0x8f): msg_devconfig_get_settings_response,
            (0, 0x90): msg_devconfig_set_settings_response,
            (0, 0x93): msg_devconfig_control_response,
           # BMP5 Application Packets
            (1, 0x89): msg_collectdata_response,
            (1, 0x97): msg_clock_response,
            (1, 0x98): msg_getprogstat_response,
            (1, 0x9a): msg_getvalues_response,
            (1, 0x9c): msg_filedownload_response,
            (1, 0x9d): msg_fileupload_response,
            (1, 0x9e): msg_filecontrol_response,
            (1, 0xa1): msg_pleasewait,
        }[(hdr['HiProtoCode'], msg['MsgType'])](msg)
    except (KeyError, IndexError):
        pass # if not listed above

    return hdr, msg


################################################################################
#
# Utility functions for routine tasks
#
################################################################################

#
# Wait for an incoming packet
#
def wait_pkt(s, SrcNodeId, DstNodeId, TranNbr, timeout = 1):
    # s:            socket object
    # SrcNodeId:    source node ID (12-bit int)
    # DstNodeId:    destination node ID (12-bit int)
    # TranNbr:      expected transaction number
    # timeout:      timeout in seconds

    import time
    max_time = time.time() + 0.9 * timeout

    # Loop until timeout is reached
    while time.time() < max_time:
        try:
            rcv = recv(s)
        except socket.timeout:
            rcv = None
        
        if not rcv:
            continue
            
        hdr, msg = decode_pkt(rcv)

        # ignore packets that are not for us
        if hdr.get('DstNodeId') != DstNodeId or hdr.get('SrcNodeId') != SrcNodeId:
            continue

        # Respond to incoming hello command packets
        if msg.get('MsgType') == 0x09:
            pkt = pkt_hello_response(hdr['SrcNodeId'], hdr['DstNodeId'], msg['TranNbr'])
            send(s, pkt)
            continue

        # Handle "please wait" packets
        if msg.get('TranNbr') == TranNbr and msg.get('MsgType') == 0xa1:
            timeout = msg.get('WaitSec', 1)
            max_time += timeout
            continue

        # this should be the packet we are waiting for
        if msg.get('TranNbr') == TranNbr:
            break

    else:
        hdr = {}
        msg = {}

    return hdr, msg

#
# Encode binary data
#
def encode_bin(Types, Values):
    # Types:   List of strings containing data types for fields
    # Values:  List of values (must have same number of elements as Types)

    buff = b'' # buffer for binary data
    for i in range(len(Types)):
        Type = Types[i]
        fmt = datatype[Type]['fmt'] # get default format for Type
        value = Values[i]

        if Type == 'ASCIIZ':   # special handling: nul-terminated string
            if isinstance(value, str):
                value = value.encode('ascii')
            value += b'\0' # Add nul to end of string
            enc = struct.pack('%d%s' % (len(value), 's'), value)
        elif Type == 'ASCII':   # special handling: fixed-length string
            if isinstance(value, str):
                value = value.encode('ascii')
            enc = struct.pack('%d%s' % (len(value), 's'), value)
        elif Type == 'NSec':   # special handling: NSec time
            enc = struct.pack(fmt, value[0], value[1])
        else:                  # default encoding scheme
            enc = struct.pack(fmt, value)

        buff += enc
    return buff

#
# Decode binary data
#
def decode_bin(Types, buff, length = 1):
    # Types:   List of strings containing data types for fields
    # buff:    Buffer containing binary data
    # length:  length of ASCII string (optional)

    offset = 0 # offset into buffer
    values = [] # list of values to return
    for Type in Types:
        # get default format and size for Type
        fmt = datatype[Type]['fmt']
        size = datatype[Type]['size']
        
        if size is not None and size > len(buff) - offset:
            # print("**** decode_bin: no more data! ***")
            return [], 0

        if Type == 'ASCIIZ': # special handling: nul-terminated string
            nul = buff.find(b'\0', offset) # find first '\0' after offset
            if nul == -1:
                value = buff[offset:].decode('ascii')
                size = len(buff) - offset
            else:
                value = buff[offset:nul].decode('ascii') # return string without trailing '\0'
                size = nul - offset + 1
        elif Type == 'ASCII': # special handling: fixed-length string
            size = length
            value = buff[offset:offset + size].decode('ascii') # return fixed-length string
        elif Type == 'FP2': # special handling: FP2 floating point number
            fp2 = struct.unpack(fmt, buff[offset:offset+size])
            mant = fp2[0] & 0x1FFF    # mantissa is in bits 1-13
            exp  = fp2[0] >> 13 & 0x3 # exponent is in bits 14-15
            sign = fp2[0] >> 15       # sign is in bit 16
            value = ((-1)**sign * float(mant) / 10**exp, )
        else:                # default decoding scheme
            value = struct.unpack(fmt, buff[offset:offset+size])

        # un-tuple single values
        if isinstance(value, tuple) and len(value) == 1:
            value = value[0]

        values.append(value)
        offset += size

    # Return decoded values and current offset into buffer (size)
    return values, offset

def open_serial(device, baud=9600):
    return serial.Serial(device, baud, timeout=1)

def ping_node(s, DstNodeId, SrcNodeId):
    pkt, tran_nbr = pkt_hello_cmd(DstNodeId, SrcNodeId)
    send(s, pkt)
    response = recv(s)
    return response

def getvalues(s, DstNodeId, SrcNodeId, TableName, Type, FieldName, Swath = 1, SecurityCode = 0x0000):
    # s:            Socket object
    # DstNodeId:    Destination node ID (12-bit int)
    # SrcNodeId:    Source node ID (12-bit int)
    # TableName:    Table name as string
    # Type:         Type name as defined in datatype (e.g. 'Byte')
    # FieldName:    Field name (including index if applicable)
    # Swath:        Number of columns to retrieve from an indexed field
    # SecurityCode: 16-bit security code (optional)

    # Send Get Values Command and wait for response
    try:
        pkt, TranNbr = pkt_getvalues_cmd(DstNodeId, SrcNodeId, TableName, Type, FieldName, Swath, SecurityCode)
        send(s, pkt)
        hdr, msg = wait_pkt(s, DstNodeId, SrcNodeId, TranNbr)
        
        if msg.get('RespCode') == 0:
            values = msg.get('Values', b'')
            parse = parse_values(values, Type, Swath)
        else:
            parse = [None]
    except Exception as e:
        print(f"Error in getvalues: {e}")
        parse = [None]

    # Return list with retrieved values
    return parse
