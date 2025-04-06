from typing import List
from datetime import datetime, timezone
import json
import struct

import numpy as np
import pymap3d
from numba import njit

class FlightState:
    t: float
    LLA: np.ndarray
    ECEF: np.ndarray
    AER: np.ndarray
    # track: float
    # groundSpeed: float
    # altRate: float

    def __init__(self, message: dict, tStart: datetime):
        # TODO: Should we remove off the time since last seen?
        self.t = (datetime.fromtimestamp(message['t'], tz=timezone.utc) - tStart).seconds
        
        self.LLA = np.array([message['lat'], message['lon'], message['alt_geom'] * 0.3048]) # alt feet to meters
        # self.ECEF = np.array(message['ECEF'])
        self.ECEF = np.array(pymap3d.geodetic2ecef(*(self.LLA)))
        self.AER = np.array(message['AER'])
        # self.track = message['track']
        # self.groundSpeed = message['gs']
        # self.altRate = (message['geom_rate'] * 0.3048) / 60 # feet/minute to meters/second

        self.format = "!f" + "fff" + "fff" + "fff"

    def __repr__(self):
        return f"{self.LLA}, {self.t}"

    def pack(self) -> bytes:
        return struct.pack(self.format, self.t, *self.LLA, *self.ECEF, *self.AER)

    def unpack(self, data: bytes):
        members = self.unpack(self.format)
        self.t = members[0]
        self.LLA = np.array(members[1:4])
        self.ECEF = np.array(members[4:7])
        self.AER = np.array(members[7:10])
        return self


# @njit(cache=True)
def binarySearch(data: List[float], val: float):
    # https://stackoverflow.com/a/23682008

    highIndex = len(data)-1
    lowIndex = 0
    while highIndex > lowIndex:
            index = int((highIndex + lowIndex) / 2)
            sub = data[index]
            if data[lowIndex] == val:
                    return [lowIndex, lowIndex]
            elif sub == val:
                    return [index, index]
            elif data[highIndex] == val:
                    return [highIndex, highIndex]
            elif sub > val:
                    if highIndex == index:
                            return sorted([highIndex, lowIndex])
                    highIndex = index
            else:
                    if lowIndex == index:
                            return sorted([highIndex, lowIndex])
                    lowIndex = index
    return sorted([highIndex, lowIndex])

class Flight():
    id: str
    positions: List[FlightState]
    category: str
    positionTime: List[float]

    previousStateIdx: int

    def __init__(self, id: str, data: dict, tStart: datetime):
        self.id = id
        self.positions = []
        self.previousStateIdx = 0
        self.useSearchShortcut = False

        if 'category' in data[0]:
            self.category = data[0]['category']
        else:
            self.category = 'A1' # Assume small

        for message in data:
            state = FlightState(message, tStart)
            self.positions.append(state)
        
        self.positions.sort(key=lambda x: x.t)
        self.positionTime = [p.t for p in self.positions]


    def getState(self, t: float) -> FlightState:
        # Should consider returning none if timedelta is too large
        # Since we later filter by a constant elevation angle we could do that here before interpolation
        
        # For large search spaces the binary search can still be a bottleneck
        # However the user generally calls getState with t values going in linearly increasing amounts
        # So if we do a quick check to see if the current or next index is closest we can probably reduce the search space significantly
        # It seems that if there are large gaps in data this method just makes things slower since it will fall back on binarySearch anyway
        if self.useSearchShortcut:
            currentIdxDt = abs(self.positions[self.previousStateIdx].t - t)
            nextIdxDt = abs(self.positions[self.previousStateIdx+1].t - t)
            minDt = min(currentIdxDt, nextIdxDt)
            if minDt < 5:
                if currentIdxDt < nextIdxDt: # Current index is still the best choice
                    return self.positions[self.previousStateIdx]
                else: # Next index is now closer
                    self.previousStateIdx += 1
                    return self.positions[self.previousStateIdx]            

        # Fall back on basic binary search if the optimization doesn't work, if there is a drop in ADSB data this will be required
        idx = binarySearch(self.positionTime, t)[0]
        if (self.positions[idx].t - t) > 15: # Too old to be real
            return None
        self.previousStateIdx = idx
        return self.positions[idx]


def loadFlights(path: str, tStart: datetime) -> List[Flight]:
    with open(path) as flightFile:
        flightData = json.load(flightFile)
    
    flights = []
    for key, value in flightData.items():
        flights.append(Flight(key, value, tStart))
    return flights
