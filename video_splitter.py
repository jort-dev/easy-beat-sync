#!/usr/bin/env python3
"""
Usage: python video_splitter.py 300 2000
This splits the video into 300 parts of each 2000ms long.
It launches a file picker to choose the video.

It works by spitting the full video by keyframes into parts of 2000ms long.
It then saves 300 of those parts, picked spread along the video, so this means the ending of the video will be the last part.
Then it deletes the other parts which weren't picked.
This means it is not perfectly spread across, but is fairly close and very quick.

NOTICE: if the parts are not in the length specified, the keyframes are off. Try the other video splitter.
NOTICE: does not work for short videos
"""
import sys
from pathlib import Path

import numpy as np

from common import *

# arguments
if len(sys.argv) < 3:
    quit(f"Program must be called with 2 arguments: split_amount split_length_ms")
split_amount = int(sys.argv[1])
split_length_ms = int(sys.argv[2])

# get paths
video_path = ask_file()
video_folder_path = os.path.dirname(video_path)
video_filename = Path(video_path).name
video_base_name = Path(video_path).stem
result_folder_name = f"{video_base_name}_parts"
result_folder_path = os.path.join(video_folder_path, result_folder_name)
realise_dir(result_folder_path)

# parse arguments and video
cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {video_path}"
video_length_seconds = run_cmd(cmd)
video_length_nanoseconds = video_length_seconds.replace(".", "")
video_length_ms = int(video_length_nanoseconds) // 1000
if split_amount * split_length_ms > video_length_ms:
    quit(f"The video does not fit {split_amount} videos of each {split_length_ms}ms")
duration_time_string = ms_to_time_string(split_length_ms)

# split the video
print(f"Splitting the video into parts...")
cmd = f"ffmpeg -i {video_path} -c copy -map 0 -segment_time {duration_time_string} -f segment -reset_timestamps 1 {result_folder_path}/output%03d.mp4"
run_cmd(cmd)

# get a list of all the split parts
video_paths = get_file_paths_with_extensions(result_folder_path, ".mp4")

# split up the list spread equally across
result_video_paths = []
indexes = np.linspace(start=0, stop=len(video_paths) - 1, num=split_amount)
for index in indexes:
    result_video_paths.append(video_paths[round(index)])
for video_path in video_paths:
    if video_path not in result_video_paths:
        os.remove(video_path)

print(f"Split {video_filename} into {len(result_video_paths)} parts "
      f"of each {split_length_ms}ms in folder '{result_folder_name}'!")
