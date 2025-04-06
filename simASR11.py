from typing import Optional, List
import yaml

import numpy as np
import pymap3d
import scipy
import scipy.constants
from numba import njit

from flightData import FlightState, Flight
from detection import Detection

# Simulates the Bistatic receiver

def feet2meters(f: float) -> float:
    return f*0.3048

def linear2db(l: float) -> float:
    return 10*np.log10(l)

def db2linear(db: float) -> float:
    return 10**(db/10)

ASR11_RPM = 12.5
ASR11_ROT_HZ = ASR11_RPM / 60
ASR11_ROT_S = 1/ASR11_ROT_HZ

BEAMWIDTH_HORIZONAL = 1.4
BEAMWIDTH_VERTICAL = 5

with open("transmitters.yaml") as stream:
    transmitters = yaml.safe_load(stream)

with open("targets.yaml") as stream:
    targets = yaml.safe_load(stream)

with open("antennas.yaml") as stream:
    antennas = yaml.safe_load(stream)

with open("receivers.yaml") as stream:
    receivers = yaml.safe_load(stream)

with open("locations.yaml") as stream:
    locations = yaml.safe_load(stream)


transmitter = transmitters['ASR-11']
antenna = antennas['Dipole']
receiver = receivers['Pluto SDR']
location = locations['Clairemont Hills']


T0 = 290 # Kelvin - System temperature
SNR_Min = 5 # db - How much more powerful does the signal need to be in order to detect it

Pt = float(transmitter['Pt'])   # Transmitter power
Gt = db2linear(float(transmitter['Gt']))   # Transmitter gain
Fc = float(transmitter['Fc'])   # Transmitter frequency
Tau = float(transmitter['Tau']) # Transmitter pulse width

Gr = db2linear(float(antenna['Gr'])) # Reciver antenna gain

Fn = float(receiver['F'])  # Receiver noise figure
Tr = float(receiver['T'])  # Receiver temperature
BW = float(receiver['BW']) # Receiver Bandwidth

# Altitudes from https://en-gb.topographic-map.com/map-4d9jnh/The-World/?center=34.05351%2C-117.64143&popup=34.05623%2C-117.60057
transmitterLLA = [34.052724, -117.596634, 282]
receiverLLA = location['LLA']

transmitterECEF = np.array(pymap3d.geodetic2ecef(*transmitterLLA))
receiverECEF = np.array(pymap3d.geodetic2ecef(*receiverLLA))

transmitter2targetENU = np.array(pymap3d.ecef2enu(*receiverECEF, *transmitterLLA))
elevationAngle = np.rad2deg(np.tan(transmitter2targetENU[2] / np.sqrt(transmitter2targetENU[0]**2 + transmitter2targetENU[1]**2)))

print(f"elevationAngle = {elevationAngle}")
# if elevationAngle < 1:
#     print(f"Receiver unlikely to get direct signal from antenna at elevation angle {elevationAngle}")
#     exit(0)

# @njit(cache=True)
def getAz(t: float) -> float:
    return ((t / ASR11_ROT_S) % 1) * 360

# @njit(cache=True)
def isInFOV(t: float, AER: np.ndarray) -> bool:
    # Can't be above beam and can't be too close to the ground due to clutter
    # if AER[1] > BEAMWIDTH_VERTICAL or AER[1] < 0.5:
    if AER[1] > BEAMWIDTH_VERTICAL:
        return False
    az = getAz(t)
    if (abs(AER[0] - az) > BEAMWIDTH_HORIZONAL):
        return False        
    return True

# Constants with respect to inputs to this function
wavelength = scipy.constants.c / Fc
wavelength2 = wavelength*wavelength
DETECT_POWER_SCALAR = (Pt*Gt*Gr*wavelength2) / ((4*np.pi)**3)
# DETECT_NOISE = (scipy.constants.k * Tr * Fn) / Tau # using pulse to set bandwidth
DETECT_NOISE = db2linear(linear2db(scipy.constants.k*Tr) + Fn + linear2db(BW)) # https://en.wikipedia.org/wiki/Minimum_detectable_signal#General
# Alternative noise floor calculation: https://en.wikipedia.org/wiki/Minimum_detectable_signal
DETECT_MDS = linear2db(DETECT_NOISE) + SNR_Min # dB

# @njit(cache=True)
def getSNR(targetECEF: np.ndarray, RCS: float) -> float:
    Rt = np.linalg.norm(targetECEF - transmitterECEF)
    Rr = np.linalg.norm(targetECEF - receiverECEF)

    Rt2 = Rt*Rt
    Rr2 = Rr*Rr

    # https://www.mathworks.com/help/radar/ug/radar-equation.html
    # Skipping propagation pattern F and Loss L
    Pr = DETECT_POWER_SCALAR * ((RCS) / (Rt2*Rr2))
    N = DETECT_NOISE

    return Pr / N

def simulateFlight(tPulses: np.ndarray, flight: Flight) -> List[Detection]:
    RCS = float(targets[flight.category]['RCS'])

    detects = []
    for t in tPulses:
        state = flight.getState(t)
        if state is None:
            continue

        if not isInFOV(t, state.AER):
            continue

        snr = getSNR(state.ECEF, RCS)
        if snr > SNR_Min:
            detects.append(Detection(t, state, snr))
    return detects

