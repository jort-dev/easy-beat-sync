"""
Shifts all the timestamps in a timestamps.yaml file.
Use this if the beat sync seems off a little bit.
"""
import os
import sys
from pathlib import Path

import yaml

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), os.pardir, 'common')))  # HACK >:)
from common import *
try:
    from common.common import *
except ImportError:
    pass

timestamps_path = ask_file()
timestamps_filename = Path(timestamps_path).name
try:
    timestamp_dict = yaml.safe_load(open(timestamps_path))
except:
    quit("Could not find read YAML from supplied file.")

timestamps = timestamp_dict["type1"]

ms_between_frames = 15
last_timestamp = timestamps[-1]
frames_needed = last_timestamp / ms_between_frames
frame_count = 0
last_iterated_timestamp = 0
for i in range(len(timestamps)):
    timestamp = timestamps[i]
    duration = timestamp - last_iterated_timestamp
    add = duration / ms_between_frames
    frame_count += round(add)
    last_iterated_timestamp = timestamp

print(f"Frames needed for video of {last_timestamp}ms: {frames_needed}, but was {frame_count}")

new_timestamps = []

shift = -1000 / 60
for i in range(len(timestamps)):
    timestamp = timestamps[i]
    timestamp += shift
    new_timestamps.append(round(timestamp))

p = Path(timestamps_path)
output_file_name = f"{p.stem}_shifted{p.suffix}"
output_file_path = os.path.join(p.parent, output_file_name)
with open(output_file_path, "w") as file:
    file.write("type1:\n")
    for t in new_timestamps:
        file.write(f" - {t}\n")
    file.write("type2:\n")
