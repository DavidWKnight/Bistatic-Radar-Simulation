import gzip
import json
import glob
import os
import copy
import time
import yaml

import numpy as np
import pymap3d
import pymap3d.vincenty as pmv

removeEntries = ['adsb_icao', 'squawk', 'emergency', 'nav_altitude_fms', 'nav_qnh', 'nav_modes', 'alert', 'spi', 'oat', 'tat', 'mlat', 'tisb', 'messages', 'sil', 'sil_type']
requiredFields = ['alt_geom', 'gs', 'track', 'geom_rate', 'category', 'lat', 'lon']

maxDataAge = 30 # seconds, can't reliably recreate profile otherwise
filterDistance = 30e3 # km - eye ball it using https://www.mapdevelopers.com/draw-circle-tool.php

with open("ocations.yaml") as stream:
    locations = yaml.safe_load(stream)

ONTLLA = locations['ONT Airport']
CableAirportECEF = pymap3d.geodetic2ecef(np.array([34.111906, -117.686524, 435]))

latMin = 33.5
latMax = 35.5
lonMax = -116.5
lonMin = -118.5

dirPath = "FlightData/2025/03/01/"

flightData = {}
tStart = time.time()
paths = glob.glob(dirPath + '*.json.gz')
paths.sort()
for idx, inFile, in enumerate(paths):
    if idx > 0:
        dt = time.time() - tStart
        secondsPerFile = dt / idx
        filesRemaining = len(paths) - idx
        print(f"Parsing {inFile}, estimated {round(secondsPerFile * filesRemaining)}s remaining")

    with gzip.open(inFile,'r') as fin:
        data = json.load(fin)
        
        t = int(data['now'])
        for aircraft in data['aircraft']:
            try:
                if 'lat' not in aircraft or 'lon' not in aircraft:
                    continue

                lat = float(aircraft['lat'])
                lon = float(aircraft['lon'])
                
                # Apply the easy filters first
                if (lat < latMin or lat > latMax):
                    continue
                elif (lon < lonMin or lon > lonMax):
                    continue
                elif (aircraft['alt_baro'] == 'ground'):
                    continue # Can't track targets on the ground
                elif (aircraft['seen'] > maxDataAge):
                    continue
                elif (aircraft['type'] != 'adsb_icao'): # It seems like other types are less reliable
                    continue
                
                # for field in requiredFields:
                #     if field not in aircraft:
                #         continue

                alt = float(aircraft['alt_geom']) * 0.3048 # feet to meters

                # Finished rough cut, now try fine cut
                [dist, _] = pmv.vdist(lat, lon, ONTLLA[0], ONTLLA[1])
                if dist > filterDistance:
                    continue

                # We also want to precompute some metadata that will always be true
                AER = pymap3d.geodetic2aer(lat, lon, alt, ONTLLA[0], ONTLLA[1], ONTLLA[2])
                ECEF = pymap3d.geodetic2ecef(lat, lon, alt)
                
                if (np.linalg.norm(ECEF - CableAirportECEF) < 500):
                    # This fucking airport is constantly giving false alarms...
                    continue

                aircraft['AER'] = list(AER)
                aircraft['ECEF'] = list(ECEF)

                # Remove stuff we will never need
                for entry in removeEntries:
                    if entry in aircraft:
                        del aircraft[entry]

                # Add to the dictionary
                id = aircraft['hex']
                aircraft['t'] = t

                del aircraft['hex']
                if id not in flightData:
                    flightData[id] = []
                flightData[id].append(aircraft)

            except Exception as e:
                # print(f"Failed to parse data in {aircraft} - {e}")
                pass

print(f"Finished filtering, writing data to file")
with open(dirPath.replace('/', '_')[:-1] + ".json", 'w') as filtFile:
    json.dump(flightData, filtFile)

# TODO: Consider interpolating position over time, annoying to map individual planes though
