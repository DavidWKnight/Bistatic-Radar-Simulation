from datetime import datetime
import struct

from flightData import FlightState

class Detection():
    t: float
    snr: float
    state: FlightState

    def __init__(self, t:float, state: FlightState, snr:float):
        self.t = t
        self.state = state
        self.snr = snr

    def __repr__(self) -> str:
        return f"{self.t} - {self.snr} - {self.state.LLA}"

    def pack(self) -> bytes:
        return struct.pack("!ff", self.t, self.snr) + self.state.pack()

    def unpack(self, data: bytes):
        format = "!ff"
        size = struct.calcsize(format)
        members = self.unpack(format, data[0:size])
        self.t = members[0]
        self.snr = members[1]
        self.state.unpack(data[size:])
        return self
