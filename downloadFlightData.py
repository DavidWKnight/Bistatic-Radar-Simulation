import subprocess
import shutil
import time
import os


stem = "https://samples.adsbexchange.com/readsb-hist/"
folder = "FlightData/"
day = "2025/02/01/"
ext = "Z.json.gz"

SecondsPerDay = 24*60*60
for hour in range(24):
    for minute in range(60):
        for second in range(0, 60, 5):
            fileName = str(hour).zfill(2) + str(minute).zfill(2) + str(second).zfill(2) + ext
            
            if (os.path.isfile(day + fileName)):
                print(f"Skipping {fileName}")
                continue

            time.sleep(1)
            
            try:
                subprocess.call(['wget', stem + day + fileName])
                src = fileName
                dest = folder + day + fileName
                shutil.copyfile(src, dest)
                os.remove(src)
            except:
                continue
