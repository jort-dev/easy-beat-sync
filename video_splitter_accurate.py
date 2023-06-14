#!/usr/bin/env python3
"""
Simple tool to split a video into multiple shorter ones.

Usage:
python video_splitter_accurate.py 300 2000

This splits the video into 300 parts of each 2000ms long.
It launches a file picker to choose (multiple) videos.

It tries to spread the splits over the whole video, it does not just get splits from only the beginning.
"""
import sys
from pathlib import Path

from common import *

video_paths = ask_file(multiple=True)
first_parent_folder = Path(video_paths[0]).parent
split_output_folder = os.path.join(first_parent_folder, "splitted_videos")
realise_dir(split_output_folder)

# argument 1: amount of splits, or percentage of video which should be split
split_amount = 3
split_amount = sys.argv[1] if len(sys.argv) >= 1 else split_amount
split_amount = int(split_amount)

# argument 2: length for the splits
split_length = 2000
split_length = int(sys.argv[2]) if len(sys.argv) >= 2 else split_length

printt(f"Splitting {len(video_paths)} videos into max {split_amount} pieces of each {split_length}ms long")

count = 0
for video_path in video_paths:
    video_name = Path(video_path).name
    printt(f"Splitting video {count + 1} / {len(video_paths)}: {video_name}", end="\r")


    def calculate_time_between_splits():
        time_taken_by_splits = split_amount * split_length
        # printt(f"{time_taken_by_splits}ms taken of {video_length}ms by the splits.")
        time_to_divide = video_length - time_taken_by_splits
        amount_of_padding_needed = split_amount + 1
        # printt(f"{time_to_divide}ms can be used for {amount_of_padding_needed}x padding.")
        time_for_each_padding = round(time_to_divide / amount_of_padding_needed)
        # printt(f"That makes each padding {time_for_each_padding}ms long.")
        return time_for_each_padding


    video_length = get_video_ms(video_path)

    # lower split amount if not enough video (failsafe)
    if split_amount * split_length > video_length:
        split_amount = video_length / (split_length + 100)  # small padding to prevent off-by-one errors
        if split_amount < 1:
            printt(f"Video {video_name} is shorter than {split_length}, skipped splitting.")
            continue
        split_amount = int(split_amount)

    time_between_splits = calculate_time_between_splits()

    for x in range(split_amount):
        video_filename = Path(video_path).stem
        video_extension = Path(video_path).suffix
        part_result_path = os.path.join(split_output_folder, f"{video_filename}_part{x}{video_extension}")
        start_ms = (x + 1) * time_between_splits + split_length * x  # yeah boy gl figuring out this advanced algebra
        end_ms = start_ms + split_length

        start_time_string = ms_to_time_string(start_ms)
        end_time_string = ms_to_time_string(end_ms)
        # -c copy somehow results in bad footage (maybe because it splits on keyframes?)
        run_cmd(f"ffmpeg -y -ss {start_time_string} -to {end_time_string} "
                f" -i {video_path} {part_result_path}")

    count += 1
