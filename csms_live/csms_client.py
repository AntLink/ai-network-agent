"""Minimal TCI CSMS (SMetricsNet) client over TCP 3302.

Implements the wire format and the greeting handshake reverse-engineered from
csmsd.elf. This is the foundation for triggering official measurements and
receiving live spectrum data.

Wire format (little-endian):
    SSmsMsg header (20B) + body + 0x0a delimiter
      +0x00 u32 marker      (echoed back)
      +0x04 u32 field4
      +0x08 u16 msgType
      +0x0A u8  cmdVer      (greeting needs >= 1)
      +0x0B u8  respVer     (greeting needs >= 1)
      +0x0C u32 subtype
      +0x10 u32 bodyLen

Session:
    1. send greeting (8565, sub0, cmdVer=1, respVer=1, 36B body)
    2. receive greeting RES (8566) -> 4-byte body is the SESSION TOKEN
    3. all subsequent requests must echo token in body[0:4] on the same socket
"""

import socket
import struct
import time

MSG_GREETING_REQ = 8565
MSG_GREETING_RES = 8566
MSG_PAN_REQ = 8563
MSG_MEASURE_CTRL = 27
MSG_ERROR = 9999

# MeasureCtrl (type 27) subtypes
SUB_SCHEDULE_MEASUREMENT = 71000   # ScheduleMeasurement, cmdVer>=2
SUB_DELETE_RESULTS = 71001         # DeleteResults
SUB_RETRIEVE_MEASUREMENT = 71002   # RetrieveMeasurement -> resp sub 72002
SUB_FORWARD_EQUIP = 71003          # ForwardToEquipControl
SUB_RETRIEVE_IQDATA = 71017        # RetrieveIqData
SUB_ANT_LIST = 9                   # SendAntListResp

# Response subtypes (type 27)
RESP_MEAS_RESULT_V5 = 72002        # SGetMeasRespV5 (respVer must be >= 2)

HDR = struct.Struct("<IIHBBII")


def pack_msg(marker, msg_type, cmd_ver, resp_ver, subtype, body=b"", field4=0):
    # NOTE: length-prefixed framing only (20B header + body). NO \n delimiter.
    # Sending a trailing \n desyncs the server by 1 byte on subsequent messages.
    return HDR.pack(marker, field4, msg_type, cmd_ver, resp_ver, subtype, len(body)) + body


class SMsg:
    def __init__(self, raw):
        self.raw = raw
        if len(raw) < 20:
            raise ValueError(f"short message {len(raw)}B")
        (self.marker, self.field4, self.msg_type, self.cmd_ver,
         self.resp_ver, self.subtype, self.body_len) = HDR.unpack(raw[:20])
        self.body = raw[20:20 + self.body_len]

    def __repr__(self):
        return (f"<SMsg type={self.msg_type} sub={self.subtype} "
                f"cmdVer={self.cmd_ver} respVer={self.resp_ver} "
                f"marker=0x{self.marker:x} bodyLen={self.body_len} body={self.body.hex()}>")


class CSMSClient:
    def __init__(self, host, port=3302, timeout=8):
        self.host = host
        self.port = port
        self.timeout = timeout
        self.sock = None
        self.token = b""
        self.marker = 0

    def connect(self):
        self.sock = socket.create_connection((self.host, self.port), timeout=self.timeout)
        self.sock.settimeout(self.timeout)

    def _read_one(self):
        # length-prefixed framing: 20B header + bodyLen body bytes (no delimiter)
        hdr = self._recv_exact(20)
        if hdr is None:
            return None
        (marker, field4, mt, cv, rv, sub, bl) = HDR.unpack(hdr)
        body = self._recv_exact(bl) if bl else b""
        return SMsg(hdr + body)

    def _recv_exact(self, n):
        buf = b""
        while len(buf) < n:
            d = self.sock.recv(n - len(buf))
            if not d:
                return None
            buf += d
        return buf

    def send(self, msg_type, cmd_ver, resp_ver, subtype, body=b""):
        self.marker += 1
        pkt = pack_msg(self.marker, msg_type, cmd_ver, resp_ver, subtype, body)
        self.sock.sendall(pkt)

    def recv(self):
        return self._read_one()

    def greeting(self, identity=b"\x00" * 36, cmd_ver=1, resp_ver=1):
        self.send(MSG_GREETING_REQ, cmd_ver, resp_ver, 0, identity)
        resp = self.recv()
        if resp and resp.msg_type == MSG_GREETING_RES and resp.body_len >= 4:
            self.token = resp.body[:4]
        return resp

    def pan(self, subtype, extra=b""):
        body = self.token + extra
        self.send(MSG_PAN_REQ, 1, 1, subtype, body)
        return self.recv()

    # RetrieveMeasurement: type 27 sub 71002.
    # Request body = measureId (u32). Response = type 27 sub 72002 (SGetMeasRespV5).
    # respVer MUST be 2: the response (sub 72002) is version-checked with
    # respVer_min=2 in the IsBodyCompressed table; rv=1 -> "Send compressed
    # messages unsupported (27,72002)" and no data is returned.
    def retrieve_measurement(self, measure_id, cmd_ver=1, resp_ver=2):
        self.send(MSG_MEASURE_CTRL, cmd_ver, resp_ver, SUB_RETRIEVE_MEASUREMENT,
                  struct.pack("<I", measure_id))
        return self.recv()

    def schedule_measurement(self, body, cmd_ver=5, resp_ver=2):
        # subtype 71000 requires cmdVer >= 5 (see MAP1/MAP2 tables)
        self.send(MSG_MEASURE_CTRL, cmd_ver, resp_ver, SUB_SCHEDULE_MEASUREMENT, body)
        return self.recv()

    def close(self):
        if self.sock:
            self.sock.close()
            self.sock = None


if __name__ == "__main__":
    c = CSMSClient("192.168.162.20")
    c.connect()
    r = c.greeting()
    print("greeting ->", r)
    print("token ->", c.token.hex())
    c.close()
