"""
Item: either a video or image which gets converted to a clip
"""
from pathlib import Path
from common import *


class Item:
    def __init__(self, path):
        self.path = path
        self.name = Path(path).name

        # initialized later
        self.frames_paths = None
        self.frame_amount = None
        self.frames_folder = None
        self.fps = None
        self.ms_between_frames = None

    def extract_frames(self, extract_folder_root):
        # extract the frames from the video / image to a folder within the extract folder root
        extract_folder_name = f"{self.name}"  # possible problem: extension is included in folder name
        extract_folder = os.path.join(extract_folder_root, extract_folder_name)

        if not os.path.exists(extract_folder):  # only extract frames if not already extracted
            os.mkdir(extract_folder)
            # the ffmpeg commands also works for images
            cmd = f"-i {self.path} -qscale:v 2 -vf 'scale=1920:1080:force_original_aspect_ratio=decrease:eval=frame," \
                  f"pad=1920:1080:-1:-1:eval=frame' {extract_folder}/frame%03d.jpg"
            ffmpeg_cmd(cmd)

        self.frames_paths = get_file_paths_with_extensions(extract_folder, ".jpg")
        self.frame_amount = len(self.frames_paths)

    def determine_fps(self):
        if ends_with_any(self.name, *IMAGE_EXTENSIONS):
            self.fps = -1
            self.ms_between_frames = -1
        else:
            self.fps = get_video_average_fps(self.path)
            self.ms_between_frames = 1000 / self.fps

    def __repr__(self):
        return f"Item({self.name})"
