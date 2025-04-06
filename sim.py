from datetime import datetime, timezone, timedelta
import time
import cProfile
from multiprocessing import Pool
from functools import partial
from itertools import repeat


import numpy as np

import flightData
import simASR11

# Pulse repetition frequency of 1ms - Field Measurements of Pulsed Radar with the Field Master ProTM MS2090A
# @ 4.8s/rev this gives spacial resolution of 0.075 degrees - no chance I'm that good
# So if we simulate ato 10ms we still giet 0.75 degree resolution

simRange = 24*60*60
# simRange = 5*60
tPulses = np.arange(0, simRange, 1e-2)
tStart = datetime(2025, 3, 1, 0, 0, 0, tzinfo=timezone.utc)

# First load in all of the aircrafts
flights = flightData.loadFlights("FlightData/2025_03_01.json.bak", tStart)

# cProfile.run('simASR11.simulateFlight(tPulses, flights[1])')
# exit(0)

useMultiprocessing = True
start = time.time()
flightDetects = []
if useMultiprocessing:
    with Pool() as p:
        flightDetects = p.starmap(simASR11.simulateFlight, zip(repeat(tPulses), flights))

else:
    for flightIdx, flight in enumerate(flights):
        if (flightIdx % 50) == 0:
            print(f"Processing index {flightIdx}")
        flightDetects.append(simASR11.simulateFlight(tPulses, flight))


print(f"Simulation took {time.time() - start}s")

print(f"Detected {len(flightDetects) - flightDetects.count([])} flights")
for flight, detects in zip(flights, flightDetects):
    if len(detects) > 0:
        print(f"Target {flight.id} with cat {flight.category} detected {len(detects)} times:")
        print(f"detects[0] - {detects[0].state.LLA} - snr = {detects[0].snr}")



