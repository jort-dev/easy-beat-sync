"""
Assets are all the information the program needs as input to generate the compilation with
- items to use
- song to use
- timestamps to use
"""
from pathlib import Path

import yaml

from common.common import *
from main.Clip import Clip
from main.Item import Item


class Assets:
    def __init__(self, root_folder):
        self.root_folder = root_folder
        printt(f"Searching {self.root_folder} for assets...")

        # clips / videos
        self.items_folder = None
        self.items_folder_name = None
        self.items = []
        self.parse_items()

        # output folder and files
        # a scratch disk is the folder where temporary files are stored, in this case extracted frames for example
        self.scratch_folder_name = f"{self.items_folder_name}_scratch"
        self.scratch_folder = os.path.join(self.root_folder, self.scratch_folder_name)
        realise_dir(self.scratch_folder)
        self.frame_paths_file_name = f"{self.items_folder_name}_result_frames_paths.txt"
        self.frame_paths_file = os.path.join(self.scratch_folder, self.frame_paths_file_name)
        self.result_video_name = f"{self.items_folder_name}.mp4"
        self.result_video_path = os.path.join(self.root_folder, self.result_video_name)
        # because we cannot trim a video in-place:
        self.result_video_untrimmed_name = f"{self.items_folder_name}_untrimmed.mp4"
        self.result_video_untrimmed_path = os.path.join(self.scratch_folder, self.result_video_untrimmed_name)

        # timestamps
        self.clips = []
        self.parse_timestamps()

        # song
        self.song_path = None
        self.parse_song()

    def parse_items(self):
        self.items_folder = None
        items_paths = []
        for item_name in natsorted(os.listdir(self.root_folder), key=lambda y: y.lower()):
            item_path = os.path.join(self.root_folder, item_name)
            if not os.path.isdir(item_path):
                continue  # ignore files
            if item_name.startswith(FOLDER_PREFIX):
                continue  # ignore folders created by this program
            items_paths = get_file_paths_with_extensions(item_path, *ITEM_EXTENSIONS)
            if not items_paths:
                continue  # ignore if no items were found in the folder
            self.items_folder = item_path
            break

        if not items_paths:
            stop(f"No folder with images/videos items found.")

        # convert the found paths to items
        self.items = [Item(item_path) for item_path in items_paths]
        self.items_folder_name = Path(self.items_folder).name

        printt(f"Found items folder: {self.items_folder_name}")

    def parse_song(self):
        song_paths = get_file_paths_with_extensions(self.root_folder, *AUDIO_EXTENSIONS)
        if not song_paths:
            stop(f"No audio file found.")
        self.song_path = song_paths[0]
        printt(f"Found song: {Path(self.song_path).name}")

    def parse_timestamps(self):
        timestamps_paths = get_file_paths_with_extensions(self.root_folder, *TIMESTAMP_EXTENSIONS)
        if not timestamps_paths:
            stop(f"No timestamps file found.")
        timestamps_path = timestamps_paths[0]
        timestamps_filename = Path(timestamps_path).name
        timestamp_dict = yaml.safe_load(open(timestamps_path))  # read timestamps from yaml file
        type1_timestamps = timestamp_dict["type1"]
        # convert the timestamps to clips
        last_timestamp = 0
        for i in range(0, len(type1_timestamps)):  # start at 0, as the first timestamp is not 0
            timestamp = type1_timestamps[i]
            clip = Clip(last_timestamp, timestamp)
            self.clips.append(clip)
            last_timestamp = timestamp

        printt(f"Found timestamps: {timestamps_filename}")

    def calculate_video_length(self):
        # the video either ends at the last usable clip or at the last timestamp
        last_clip = self.clips[0]
        for clip in self.clips:
            if not clip.frame_paths:
                break
            last_clip = clip
        return min(last_clip.end_ms, self.clips[-1].end_ms)

    def process_items(self):
        extracted_frames_folder_name = f"{self.items_folder_name}_extracted_frames"
        extracted_frames_folder = os.path.join(self.scratch_folder, extracted_frames_folder_name)
        realise_dir(extracted_frames_folder)
        count = 1
        printt(f"Processing items...")
        for item in self.items:
            printt(f"Processing item {count} / {len(self.items)}", end="\r")
            item.extract_frames(extracted_frames_folder)
            item.determine_fps()
            count += 1
        printt(f"Processed items! The extracted frames are stored in folder: {self.scratch_folder_name}")
