#!/usr/bin/env python3
"""
How the script works:
- let user pick a folder
- check if folder contains a folder with videos, an audio file, a timestamps file and a font file
- extract all the frames of the folder of videos to a new directory within the selected folder
- collect for each video the extracted frames
- for each frame of what will become the result, paste in an extracted frame from the current video
- if a timestamp is met, the new current video becomes the next video
"""

import re
from pathlib import Path

import yaml

from common import *

clear_cache = False  # true: clear extracted frames, video edits, etc

FOLDER_PREFIX = "jort"
VIDEO_EXTENSIONS = set(".mp4")  # gets lowercased

########################################################################################################################
source_folder_path = ask_folder()
printt()
printt(f"Searching for sources in {source_folder_path}")

########################################################################################################################

video_paths = []
video_folder = None
video_folder_name = None
for item_name in natsorted(os.listdir(source_folder_path), key=lambda y: y.lower()):
    item_path = os.path.join(source_folder_path, item_name)
    if not os.path.isdir(item_path):
        continue  # ignore files
    if item_name.startswith(FOLDER_PREFIX):
        continue  # ignore folders created by this program
    video_paths = get_file_paths_with_extensions(item_path, "mp4", "mkv")
    if not video_paths:
        continue  # ignore if no videos were found in the folder
    video_folder = item_path
    video_folder_name = item_name
    break

if not video_paths:
    stop(f"No folder with videos found in {source_folder_path}")
printt()
printt(f"Found video folder: {video_folder_name}")
first_video_fps = run_cmd(
    f"ffprobe -v 0 -of csv=p=0 -select_streams v:0 -show_entries stream=r_frame_rate {video_paths[0]}")
first_video_fps = eval(
    first_video_fps.strip())  # gives a output like '24000/1001', so use that to calculate the fps (23.976)
ms_between_frames = 1000 / first_video_fps
printt(f"The result will be {first_video_fps} FPS, which is {ms_between_frames}ms between each frame")
printt()

########################################################################################################################

song_paths = get_file_paths_with_extensions(source_folder_path, ".mp3", ".opus")
if not song_paths:
    stop(f"No audio file found in {source_folder_path}")
song_path = song_paths[0]
song_filename = Path(song_path).name
printt(f"Found song: {song_filename}")

########################################################################################################################

timestamps_paths = get_file_paths_with_extensions(source_folder_path, ".yaml")
if not timestamps_paths:
    stop(f"No timestamps .yaml file found in {source_folder_path}")
timestamps_path = timestamps_paths[0]
timestamps_filename = Path(timestamps_path).name
timestamp_dict = yaml.safe_load(open(timestamps_path))  # read timestamps from yaml file
type1_timestamps = timestamp_dict["type1"]
printt(f"Found timestamps: {timestamps_filename}")

########################################################################################################################

font_paths = get_file_paths_with_extensions(source_folder_path, ".ttf")
if not font_paths:
    stop(f"No font file found in {source_folder_path}")
font_path = font_paths[0]
font_filename = Path(font_path).name
printt(f"Found font: {font_filename}")

########################################################################################################################

printt()
extracted_frames_folder_name = f"{FOLDER_PREFIX}_{video_folder_name}_extracted_frames"
extracted_frames_folder_path = os.path.join(source_folder_path, extracted_frames_folder_name)
printt(f"The frames of the videos will be extracted to folder: {extracted_frames_folder_name}")

result_video_frame_paths_txt_file_name = f"{video_folder_name}_result_video_frame_paths.txt"
result_video_frame_paths_txt_file_path = os.path.join(source_folder_path, result_video_frame_paths_txt_file_name)
printt(f"Frame concatenation file will be saved as {result_video_frame_paths_txt_file_name}")

result_frames_folder_name = f"{FOLDER_PREFIX}_{video_folder_name}_result_frames"
result_frames_folder_path = os.path.join(source_folder_path, result_frames_folder_name)
printt(f"The frames of the result video will be saved to folder: {result_frames_folder_name}")

result_video_name = f"{video_folder_name}_result.mp4"
result_video_path = os.path.join(source_folder_path, result_video_name)
printt(f"The result video will be saved as {result_video_name}")

printt()

########################################################################################################################
amount_of_videos = len(video_paths)
if os.path.isdir(extracted_frames_folder_path) and not clear_cache:
    printt(f"WARNING: using existing extracted frames folder: {extracted_frames_folder_name}")
else:
    if not os.path.exists(extracted_frames_folder_path):
        os.mkdir(extracted_frames_folder_path)
    printt(f"Start extracting all frames from videos in {video_folder_name}")
    video_number = 0
    for video_number in range(amount_of_videos):
        video_path = video_paths[video_number]
        printt(f"Extracting frames from video {video_number} / {amount_of_videos}", end="\r")
        cmd = f"-i {video_path} -qscale:v 2 {extracted_frames_folder_path}/video{video_number}_frame%03d.jpg"
        ffmpeg_cmd(cmd)

########################################################################################################################
# collect the frames for each video
printt(f"Collecting paths to frames...")
# literally all the frames in the extracted frames folder
all_extracted_frames_paths = get_file_paths_with_extensions(extracted_frames_folder_path, ".jpg")
# a list of lists, where each list corresponds to all the paths to the frames of one video
video_frames_paths = []

video_number = 0
for video_index in range(len(video_paths)):
    printt(f"Collecting frames for video {video_number} / {amount_of_videos}", end="\r")
    regex_pattern = f".*?video{video_index}_frame\d*.jpg"
    regex = re.compile(regex_pattern)
    this_video_frame_paths = [frame_path for frame_path in all_extracted_frames_paths if regex.match(frame_path)]
    video_frames_paths.append(this_video_frame_paths)
    video_number += 1

########################################################################################################################
# compile result


amount_of_videos = len(video_paths)
if os.path.isdir(result_frames_folder_path) and not clear_cache:
    printt(f"WARNING: Using existing result frames folder: {result_frames_folder_name}")
else:
    if not os.path.exists(result_frames_folder_path):
        os.mkdir(result_frames_folder_path)

    current_ms = 0  # the exact moment where we are with writing frames in our result video
    video_number = 0  # also the index of the timestamp list
    #  the timestamp we are currently writing frames towards,
    #  so when current_ms exceeds this timestamp, go write frames from the next video to the next timestamp
    current_timestamp = type1_timestamps[video_number]
    current_video_frame_index = 0  # at which frame of the input video we are
    amount_of_source_frames = len(os.listdir(extracted_frames_folder_path))  # we need to loop a maximum amount
    result_video_length = type1_timestamps[-1]  # the music marker puts one timestamp at the exact end of the video
    writing_inverted = False  # set to true of no more frames, so we start writing frames backwards for loop effect
    # add frame count to filenames, to keep correct order and against duplicate filenames in case of video loop
    frame_count = 0
    current_video_ms = 0  # ms within the current video being handled
    # keep looping until all frames are determined of result video
    # add little buffer so music does not get cut off, ffmpeg automatically trims this with --shortest or whatever
    printt(f"Composing result video...")
    while current_ms < result_video_length + 500:
        printt(f"Composing second {round(current_ms // 1000)} / {(result_video_length + 500) // 1000}"
               f" of result video.", end="\r")
        current_ms += ms_between_frames
        current_video_ms += ms_between_frames
        # when the total time of all the currently added frames exceeds this timestamp, go to the next video
        if current_ms > current_timestamp:
            # go to next video and timestamp
            video_number += 1
            if video_number >= len(type1_timestamps):
                # all timestamps processed
                break
            current_timestamp = type1_timestamps[video_number]
            current_video_frame_index = 0
            writing_inverted = False
            current_video_ms = 0

        amount_of_vid_frames = len(video_frames_paths[video_number])

        if amount_of_vid_frames < 2:
            # this case can happen when there are less videos than timestamps
            printt(f"Warning: not enough frames in video {video_number}! Going to next video.")
            video_number += 1
            continue

        # move the frame to the result folder
        from_path = video_frames_paths[video_number][current_video_frame_index]
        to_filename = f"{frame_count}_video{video_number}_frame{current_video_frame_index}.jpg"
        to_path = os.path.join(result_frames_folder_path, to_filename)
        shutil.copy2(from_path, to_path)  # copy2 keeps metadata or whatever

        # loop the video backwards if no more frames to work with
        if current_video_frame_index >= amount_of_vid_frames - 1 and not writing_inverted:
            # No more frames, looping backward
            writing_inverted = True
        if current_video_frame_index <= 0:
            # No more frames, looping forwards again
            writing_inverted = False

        # handle input vids current frame index
        if not writing_inverted:
            current_video_frame_index += 1
        else:
            current_video_frame_index -= 1

        frame_count += 1

printt(f"Composing command to generate result video from...")
result_frames_paths = [os.path.join(result_frames_folder_path, filename) for filename in
                       os.listdir(result_frames_folder_path)]
result_frames_paths = natsorted(result_frames_paths, key=lambda y: y.lower())
with open(result_video_frame_paths_txt_file_path, "w") as file:
    for result_frame_path in result_frames_paths:
        if not os.path.exists(result_frame_path):
            # sanity check, result really should not miss any frames
            stop(f"Result frame path does not exist: {result_frame_path}")
        file.write(f"file {result_frame_path}\n")

printt(f"Generating result video...")
cmd = f"-r {first_video_fps} -f concat -safe 0  -i {result_video_frame_paths_txt_file_path} -i {song_path} " \
      f"-c:a copy -shortest -c:v libx264 -pix_fmt yuv420p {result_video_path}"
ffmpeg_cmd(cmd)

printt(f"Result saved as {result_video_name}!")
