#!/usr/bin/env python3
"""
Edit your input videos/images, add a text for example.
"""
import sys
from pathlib import Path
from natsort import natsorted

from common import *


def get_ffmpeg_text_format(text, xy_string, font_path, font_size=24):
    # xy_string: see table at https://stackoverflow.com/questions/17623676/text-on-video-ffmpeg
    return f"drawtext=fontfile={font_path}:text='{text}':fontcolor=white:fontsize={font_size}:box=1:boxcolor=black@0.5:boxborderw=5:{xy_string}"


def add_text(in_path, out_path):
    text1 = get_ffmpeg_text_format(p.name, "x=w-tw-10:y=h-th-10", font_path)
    text2 = get_ffmpeg_text_format(count, "x=10:y=10", font_path)
    cmd = f"-i {in_path} -vf \"{text1},{text2}\" -codec:a copy {out_path}"
    ffmpeg_cmd(cmd)


def scale(in_path, out_path):
    fit_res = "1920:1080"
    cmd = f"-i {in_path} -qscale:v 2 -vf 'scale={fit_res}:force_original_aspect_ratio=decrease:eval=frame," \
          f"pad={fit_res}:-1:-1:eval=frame' {out_path}"
    ffmpeg_cmd(cmd)


caller_folder = Path(sys.argv[0]).parent
font_folder = os.path.join(caller_folder, "src")
font_paths = get_file_paths_with_extensions(font_folder, FONT_EXTENSIONS)
font_path = None
if font_paths:
    font_path = font_paths[0]

# input_items_folder = sys.argv[1] if len(sys.argv) >= 2 else ask_folder()
input_items_folder = "/home/jort/Videos/video_compilations/brindisi/source"
out_folder = os.path.join(input_items_folder, "edited")
realise_dir(out_folder)
item_paths = get_file_paths_with_extensions(input_items_folder, *ITEM_EXTENSIONS)
item_paths = natsorted(item_paths)
if not font_path:
    font_path = ask_file()

count = 1
printt(f"Editing items...")
for item_path in item_paths:
    printt(f"Editing item {count} / {len(item_paths)}", end="\r")

    p = Path(item_path)
    in_filename = p.name
    in_extension = p.suffix

    # first layer
    in_path = item_path
    out_path = os.path.join(out_folder, f"{in_filename}_LAYER1{in_extension}")
    scale(in_path, out_path)

    # last layer, should have same filename as input file
    in_path = out_path
    out_path = os.path.join(out_folder, f"{in_filename}{in_extension}")
    add_text(in_path, out_path)

    count += 1

printt(f"Edited all items")

printt(f"Deleting temporary files...")
for item in os.listdir(out_folder):
    if "LAYER" in item:
        item_path = os.path.join(out_folder, item)
        os.remove(item_path)
print(f"Deleted temporary files")

print(f"Done!")
