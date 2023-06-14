#!/usr/bin/env python3
"""
How the script works:
- let user pick a folder
- check if folder contains a folder with videos and/or images, an audio file, a timestamps file and a font file
- extract all the frames of the folder of videos/images to a new directory within the selected folder
- collect for each video/item the extracted frames
- for each frame of what will become the result, paste in an extracted frame from the current item
- if a timestamp is met, the new current item becomes the next item

png works?
different resolution images / videos work?
"""

import re
from pathlib import Path

import yaml

from common import *

clear_cache = False  # true: clear extracted frames, video edits, etc
short_video_action = "slow"  # possible options: "slow" and "loop"

FOLDER_PREFIX = "jort"
# extensions gets lowercased:
VIDEO_EXTENSIONS = ".mp4", ".mkv", ".webm"
IMAGE_EXTENSIONS = ".jpg", ".jpeg", ".png"
EXTENSIONS = VIDEO_EXTENSIONS + IMAGE_EXTENSIONS

AUDIO_EXTENSIONS = ".mp3", ".opus", "flac"
FONT_EXTENSIONS = ".ttf"
TIMESTAMP_EXTENSIONS = ".yaml"

########################################################################################################################
# source folder / working directory

# source_folder_path = ask_folder()
source_folder_path = "/home/jort/Videos/video_compilations/test_easy_beat_sync"
printt()
printt(f"Searching for sources in {source_folder_path}")

########################################################################################################################
# find sources folder

source_item_paths = []
source_items_folder_name = None
source_items_folder_path = None
for item_name in natsorted(os.listdir(source_folder_path), key=lambda y: y.lower()):
    item_path = os.path.join(source_folder_path, item_name)
    if not os.path.isdir(item_path):
        continue  # ignore files
    if item_name.startswith(FOLDER_PREFIX):
        continue  # ignore folders created by this program
    source_item_paths = get_file_paths_with_extensions(item_path, *EXTENSIONS)
    if not source_item_paths:
        continue  # ignore if no items were found in the folder
    source_items_folder_name = item_name
    source_items_folder_path = item_path
    break

if not source_item_paths:
    stop(f"No folder with source material found in {source_folder_path}")
printt()
printt(f"Found source items folder: {source_items_folder_name}")

########################################################################################################################
# determine fps for each item, -1 for images

item_ms_frames = []
item_fpss = []
result_video_fps = 60
ms_between_frames = 1000 / result_video_fps
for item_path in source_item_paths:
    cmd = f"ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 -show_entries stream=avg_frame_rate {item_path}"
    if ends_with_any(item_path, *IMAGE_EXTENSIONS):
        item_ms_frames.append(-1)
        item_fpss.append(-1)
        continue
    # gives a output like '24000/1001', so use that to calculate the fps (23.976)
    fps_fraction = run_cmd(cmd)
    fps = eval(fps_fraction.strip())
    ms_between_frames = 1000 / fps
    item_ms_frames.append(ms_between_frames)
    item_fpss.append(fps)
    print(f"{item_path:20} is {fps}fps ({ms_between_frames}ms)")

print(item_ms_frames)
print(item_fpss)


printt()

########################################################################################################################
# result song path

song_paths = get_file_paths_with_extensions(source_folder_path, *AUDIO_EXTENSIONS)
if not song_paths:
    stop(f"No audio file found in {source_folder_path}")
song_path = song_paths[0]
song_filename = Path(song_path).name
printt(f"Found song: {song_filename}")

########################################################################################################################
# timestamps path

timestamps_paths = get_file_paths_with_extensions(source_folder_path, *TIMESTAMP_EXTENSIONS)
if not timestamps_paths:
    stop(f"No timestamps file found in {source_folder_path}")
timestamps_path = timestamps_paths[0]
timestamps_filename = Path(timestamps_path).name
timestamp_dict = yaml.safe_load(open(timestamps_path))  # read timestamps from yaml file
type1_timestamps = timestamp_dict["type1"]
printt(f"Found timestamps: {timestamps_filename}")

########################################################################################################################
# font path

font_paths = get_file_paths_with_extensions(source_folder_path, *FONT_EXTENSIONS)
if not font_paths:
    stop(f"No font file found in {source_folder_path}")
font_path = font_paths[0]
font_filename = Path(font_path).name
printt(f"Found font: {font_filename}")

########################################################################################################################
# determine paths to create and use

printt()
extracted_frames_folder_name = f"{FOLDER_PREFIX}_{source_items_folder_name}_extracted_frames"
extracted_frames_folder_path = os.path.join(source_folder_path, extracted_frames_folder_name)
printt(f"The frames of the items will be extracted to folder: {extracted_frames_folder_name}")

result_video_frame_paths_txt_file_name = f"{source_items_folder_name}_result_video_frame_paths.txt"
result_video_frame_paths_txt_file_path = os.path.join(source_folder_path, result_video_frame_paths_txt_file_name)
printt(f"Frame concatenation file will be saved as {result_video_frame_paths_txt_file_name}")

result_frames_folder_name = f"{FOLDER_PREFIX}_{source_items_folder_name}_result_frames"
result_frames_folder_path = os.path.join(source_folder_path, result_frames_folder_name)
printt(f"The frames of the result video will be saved to folder: {result_frames_folder_name}")

result_video_name = f"{source_items_folder_name}_result.mp4"
result_video_path = os.path.join(source_folder_path, result_video_name)
printt(f"The result video will be saved as {result_video_name}")

printt()

########################################################################################################################
# extract frames / copy over images

amount_of_source_items = len(source_item_paths)
if os.path.isdir(extracted_frames_folder_path) and not clear_cache:
    printt(f"WARNING: using existing extracted frames folder: {extracted_frames_folder_name}")
else:
    if not os.path.exists(extracted_frames_folder_path):
        os.mkdir(extracted_frames_folder_path)
    printt(f"Extracting frames...")
    item_number = 0
    for item_number in range(amount_of_source_items):
        printt(f"Extracting frames from item {item_number} / {amount_of_source_items}", end="\r")

        item_path = source_item_paths[item_number]
        if ends_with_any(item_path, *VIDEO_EXTENSIONS):
            cmd = f"-i {item_path} -qscale:v 2 {extracted_frames_folder_path}/item{item_number}_frame%03d.jpg"
            ffmpeg_cmd(cmd)
        else:
            to_path = f"{extracted_frames_folder_path}/item{item_number}_frame1.jpg"  # does JPG work for PNG etc?
            shutil.copy2(item_path, to_path)  # copy2 keeps metadata or whatever

########################################################################################################################
# collect the frames for each item
printt(f"Collecting paths to frames...")
# literally all the frames in the extracted frames folder
all_extracted_frames_paths = get_file_paths_with_extensions(extracted_frames_folder_path, ".jpg")
# a list of lists, where each list corresponds to all the paths to the frames of one item
item_frames_paths = []

item_number = 0
for item_index in range(len(source_item_paths)):
    printt(f"Collecting frames for item {item_number} / {amount_of_source_items}", end="\r")
    regex_pattern = f".*?item{item_index}_frame\d*.jpg"
    regex = re.compile(regex_pattern)
    this_item_frame_paths = [frame_path for frame_path in all_extracted_frames_paths if regex.match(frame_path)]
    item_frames_paths.append(this_item_frame_paths)
    item_number += 1

########################################################################################################################
# determine result frames

amount_of_source_items = len(source_item_paths)
if os.path.isdir(result_frames_folder_path) and not clear_cache:
    printt(f"WARNING: Using existing result frames folder: {result_frames_folder_name}")
else:
    if not os.path.exists(result_frames_folder_path):
        os.mkdir(result_frames_folder_path)

    current_ms = 0  # the exact moment where we are with writing frames in our result video
    item_number = 0  # also the index of the timestamp list
    #  the timestamp we are currently writing frames towards,
    #  so when current_ms exceeds this timestamp, go write frames from the next item to the next timestamp
    current_timestamp = type1_timestamps[item_number]
    current_item_frame_index = 0  # at which frame of the input item we are
    amount_of_source_frames = len(os.listdir(extracted_frames_folder_path))  # we need to loop a maximum amount
    result_video_length = type1_timestamps[-1]  # the music marker puts one timestamp at the exact end of the video
    writing_inverted = False  # set to true of no more frames, so we start writing frames backwards for loop effect
    # add frame count to filenames, to keep correct order and against duplicate filenames in case of video loop
    frame_count = 0
    current_video_ms = 0  # ms within the current video being handled

    # todo: all this is literally copy paste of within loop
    current_item_fps = item_fpss[item_number]
    current_item_ms_between_frames = 1000 / current_item_fps
    current_item_amount_of_frames = len(item_frames_paths[item_number])
    current_item_is_video = current_item_amount_of_frames == 1
    current_timestamp_duration = current_timestamp - current_ms + ms_between_frames  # buffer for possible edge case
    current_timestamp_required_frames = current_timestamp_duration // ms_between_frames
    current_video_frame_index_increment = 1
    # keep looping until all frames are determined of result video
    printt(f"Composing result video...")
    while current_ms < result_video_length:
        printt(f"Composing second {round(current_ms // 1000)} / {result_video_length // 1000}",
               end="\r")  # could talk in frames
        current_ms += ms_between_frames
        current_video_ms += ms_between_frames
        # when the total time of all the currently added frames exceeds this timestamp, go to the next item
        if current_ms > current_timestamp:
            # go to next item and timestamp
            item_number += 1
            if item_number >= len(type1_timestamps):
                printt(f"\nAll timestamps processed.")
                # all timestamps processed
                break
            if item_number >= len(item_frames_paths):
                printt(f"\nAll videos processed.")
                # all videos processed
                break
            current_timestamp = type1_timestamps[item_number]
            current_item_frame_index = 0
            writing_inverted = False
            current_video_ms = 0
            current_item_fps = item_fpss[item_number]
            current_item_ms_between_frames = 1000 / current_item_fps
            current_item_amount_of_frames = len(item_frames_paths[item_number])
            current_item_is_video = current_item_amount_of_frames == 1
            current_timestamp_duration = current_timestamp - current_ms + ms_between_frames  # add buffer, maybe edge ca
            current_timestamp_required_frames = current_timestamp_duration // ms_between_frames
            current_video_frame_index_increment = 1
            if current_item_is_video:
                if current_timestamp_required_frames > current_item_amount_of_frames :
                    # we lack frames, slow down is needed
                    current_video_frame_index_increment = current_item_amount_of_frames / current_timestamp_required_frames
                else:
                    # we have enough frames, and just need to match the FPS
                    current_video_frame_index_increment = ms_between_frames / current_item_ms_between_frames


        """
        We know:
        - desired fps - so we need to write a frame each MS no matter what
        - this videos fps - if it doesnt fit, loop or slow down within this timeframe
        - this timestamps duration: from 3000 to 5000: so 2000ms long
        - desired fps = 60 = 20ms between frames

        Scenario: the FPS does not match
        - this video fps = 30 = 40ms between frames
        so: we need to write two video frames after each other
        20ms / 40ms = 0.5
        so the index of the current video should increase 0.5 for each frame written
        when rounded this makes 2 frames in the result frame 
        if its higher than 1.0, that means the source video fps is higher than the result fps

        Scenario: the source does not have enough frames
        - source has 50 frames

        2000ms long at 60 fps (20ms), means 2000 / 20 = 100 frames
        The source needs to have 100 frames, but we have 50
        50 / 100 = 0.5
        the source video index needs to increase with 0.5 for each written frame
        if 0.5 is higher than 1.0, that means speeding up, ignore that
        this scenario is only relevant with a lack of frames, as we dont try to match the speed of the video as in the
        first scenario
        """

        # move the frame to the result folder
        from_index = round(current_item_frame_index)
        if from_index >= len(item_frames_paths[item_number]):
            printt(f"\nNo more frames in current video")
            break
        from_path = item_frames_paths[item_number][from_index]
        to_filename = f"{frame_count}_item{item_number}_frame{current_item_frame_index}.jpg"
        to_path = os.path.join(result_frames_folder_path, to_filename)
        shutil.copy2(from_path, to_path)  # copy2 keeps metadata or whatever

        # handle indexes in case of a video
        if current_item_is_video:
            # the 'loop' short video action is always enabled, as it doesnt trigger if slowmo is enabled
            # loop the video backwards if no more frames to work with
            if current_item_frame_index >= current_item_amount_of_frames - 1 and not writing_inverted:
                # No more frames, looping backward
                writing_inverted = True
            if current_item_frame_index <= 0:
                # No more frames, looping forwards again
                writing_inverted = False

            # handle input vids current frame index
            if not writing_inverted:
                current_item_frame_index += current_video_frame_index_increment
            else:
                current_item_frame_index -= current_video_frame_index_increment

        frame_count += 1

########################################################################################################################
# setup command to generate result with

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

########################################################################################################################
# generate result

printt(f"Generating result video...")
cmd = f"-r {result_video_fps} -f concat -safe 0  -i {result_video_frame_paths_txt_file_path} -i {song_path} " \
      f"-c:a copy -shortest -c:v libx264 -pix_fmt yuv420p {result_video_path}"
cmd = f"-r {result_video_fps} -f concat -safe 0  -i {result_video_frame_paths_txt_file_path} " \
      f"-c:v libx264 -pix_fmt yuv420p {result_video_path}"
ffmpeg_cmd(cmd)

printt(f"Result saved as {result_video_name}!")
