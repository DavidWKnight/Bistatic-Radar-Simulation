import numpy as np
import scipy
import pymap3d

import scipy.constants
import yaml

def feet2meters(f: float) -> float:
    return f*0.3048

def linear2db(l: float) -> float:
    return 10*np.log10(l)

def db2linear(db: float) -> float:
    return 10**(db/10)

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

# transmitter = transmitters['ASR-11']
transmitter = transmitters['WSR-88D']
target = targets['Boeing 737']
antenna = antennas['Dipole']
receiver = receivers['Pluto SDR']
location = locations['Mount Jurupa']

T0 = 290 # Kelvin - System temperature
SNR_Min = 10 # db - How much more powerful does the signal need to be in order to detect it

Pt = float(transmitter['Pt'])   # Transmitter power
Gt = db2linear(float(transmitter['Gt']))   # Transmitter gain
Fc = float(transmitter['Fc'])   # Transmitter frequency
Tau = float(transmitter['Tau']) # Transmitter pulse width

RCS = float(target['RCS']) # Target Radar Cross Section

Gr = db2linear(float(antenna['Gr'])) # Reciver antenna gain

Fn = float(receiver['F'])  # Receiver noise figure
Tr = float(receiver['T'])  # Receiver temperature
BW = float(receiver['BW']) # Receiver Bandwidth


# Later comes from simulations
transmitterLLA = [34.052724, -117.596634, 0] # altitude might be off...
targetLLA = [34.05638, -117.66055, feet2meters(2250)] # 737 at takeoff
# targetLLA = [34.0687, -117.51134, feet2meters(11500)] # 737 flying to LAX
# targetLLA = [34.09941, -117.76307, feet2meters(29000)] # 737 flying to LAX
receiverLLA = location['LLA']


transmitterECEF = np.array(pymap3d.geodetic2ecef(*transmitterLLA))
targetECEF = np.array(pymap3d.geodetic2ecef(*targetLLA))
receiverECEF = np.array(pymap3d.geodetic2ecef(*receiverLLA))

transmitter2targetENU = np.array(pymap3d.ecef2enu(*receiverECEF, *transmitterLLA))
elevationAngle = np.rad2deg(np.tan(transmitter2targetENU[2] / np.sqrt(transmitter2targetENU[0]**2 + transmitter2targetENU[1]**2)))
print(f"Transmitter to Receiver elevation angle = {round(elevationAngle, 3)} degrees")


Rt = np.linalg.norm(targetECEF - transmitterECEF)
Rr = np.linalg.norm(targetECEF - receiverECEF)
# Rt = 5e3 # 5km transmitter to target
# Rr = 12e3 # 12km target to receiver
print(f"Transmitter to Target distance = {round(Rt/1e3, 3)}km")
print(f"Receiver to Target distance = {round(Rr/1e3, 3)}km")
Rt2 = Rt*Rt
Rr2 = Rr*Rr

wavelength = scipy.constants.c / Fc
wavelength2 = wavelength*wavelength

# https://www.mathworks.com/help/radar/ug/radar-equation.html
# Skipping propagation pattern F and Loss L
Pr = (Pt*Gt*Gr*wavelength2*RCS) / ((4*np.pi)**3 * Rt2*Rr2)

# N = (scipy.constants.k * Tr * Fn) / Tau # using pulse to set bandwidth
N = db2linear(linear2db(scipy.constants.k*Tr) + Fn + linear2db(BW)) # https://en.wikipedia.org/wiki/Minimum_detectable_signal#General

# Alternative noise floor calculation: https://en.wikipedia.org/wiki/Minimum_detectable_signal

MDS = linear2db(N) + SNR_Min # dB

print(f"Pr = {Pr} = {round(linear2db(Pr), 3)}dB")
print(f"N = {N} = {round(linear2db(N), 3)}dB")
print(f"MDS = {round(MDS, 3)}dB")

if (linear2db(Pr) > MDS):
    print(f"Signal is detectable")
else:
    print(f"Signal cannot be detected")
print(f"Margin = {round(linear2db(Pr) - MDS, 3)} dB")


