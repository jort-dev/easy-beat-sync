#!/usr/bin/env python3
"""
Generate.
todo:
check code for existing dirs
could cut videos obvious too long
count frames in output and see if it matches timestamps
"""
import sys
from pathlib import Path

from Assets import Assets
from common import *


class Compiler:
    def __init__(self, root_folder):
        self.root_folder = root_folder
        self.fps = 60
        self.ms_between_frames = 1000 / self.fps
        self.assets = Assets(self.root_folder)

        self.assets.process_items()
        self.process_clips()
        self.match_items_to_clips()
        self.compile_video()

    def process_clips(self):
        for clip in self.assets.clips:
            clip.calculate_required_frames(self.fps)

    def match_item_to_clip(self, item, clip):
        """
        Assumed: fps is always higher than item ms
        """
        item_frame_index = 0
        last_copied_frame_index = -1

        if item.frame_amount != 1:
            # 30 / 60 = 0.5, so item gets read slower such that the written speed matches
            index_increment = item.fps / self.fps

            # check if the item has enough frames for this
            # those 1's are for one-off error prevention
            if clip.frame_amount * index_increment >= item.frame_amount - 1:
                # item does not have enough frames, needs to be slowed down
                index_increment = (item.frame_amount - 1) / clip.frame_amount
        else:
            index_increment = 0  # item is an image and should not go to the next frame

        while True:
            if len(clip.frame_paths) >= clip.frame_amount:
                # clip is written
                break

            frame_index_to_copy = round(item_frame_index)

            if item.frame_amount != 1:  # in case of video, calculate next frame index
                if last_copied_frame_index != frame_index_to_copy:
                    # if out of bounds error occur, index increment calculation was wrong
                    last_copied_frame_index = frame_index_to_copy

                item_frame_index += index_increment

            clip.frame_paths.append(item.frames_paths[frame_index_to_copy])

    def match_items_to_clips(self):
        printt(f"Matching clips...")
        index = 0
        # could do: for in range
        iteration_amount = min(len(self.assets.items), len(self.assets.clips))
        while True:
            if index >= iteration_amount:
                printt(f"All clips matched")
                break
            printt(f"Matching clip {index} / {iteration_amount}", end="\r")
            item = self.assets.items[index]
            clip = self.assets.clips[index]
            self.match_item_to_clip(item, clip)
            index += 1

    def compile_video(self):
        frame_paths = []
        for clip in self.assets.clips:
            frame_paths += clip.frame_paths

        with open(self.assets.frame_paths_file, "w") as file:
            for result_frame_path in frame_paths:
                if not os.path.exists(result_frame_path):
                    # sanity check, result really should not miss any frames
                    stop(f"Result frame path does not exist: {result_frame_path}")
                file.write(f"file {result_frame_path}\n")

        cmd = f"-r {self.fps} -f concat -safe 0  -i {self.assets.frame_paths_file} -i {self.assets.song_path} " \
              f"-c:a copy -shortest -c:v libx264 -pix_fmt yuv420p {self.assets.result_video_untrimmed_path}"
        printt(f"Compiling video...")
        ffmpeg_cmd(cmd)
        # trim video, the -shortest in above command does not seem to work
        printt(f"Trimming video...")
        end_time = ms_to_time_string(self.assets.calculate_video_length())
        cmd = f"-ss 00:00:00 -to {end_time} -i {self.assets.result_video_untrimmed_path} " \
              f"-c copy {self.assets.result_video_path}"
        ffmpeg_cmd(cmd)
        printt(f"Video compiled! Saved as {self.assets.result_video_name}!")


printt("The program will prompt you for a folder. ")
printt("This folder needs to contain a music file, a timestamp file, and another folder with images and videos.")
root_folder = "/home/jort/Videos/video_compilations/brindisi"
# root_folder = sys.argv[1] if len(sys.argv) >= 2 else ask_folder()
Compiler(root_folder)
