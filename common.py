"""
A collection of general use / common functions used between multiple scripts.
"""
import os
import shutil
import subprocess
import traceback
from datetime import datetime, timedelta

import webview
from natsort import natsorted

FOLDER_PREFIX = "jort"
VIDEO_EXTENSIONS = ".mp4", ".mkv", ".webm"
IMAGE_EXTENSIONS = ".jpg", ".jpeg", ".png"
ITEM_EXTENSIONS = VIDEO_EXTENSIONS + IMAGE_EXTENSIONS

AUDIO_EXTENSIONS = ".mp3", ".opus", "flac"
FONT_EXTENSIONS = ".ttf"
TIMESTAMP_EXTENSIONS = ".yaml"


def printt(*argss, **kwargs):
    to_print = " ".join(map(str, argss))
    to_print = f"{datetime.now().time()}     {to_print}"
    print(to_print, **kwargs)


def stop(msg):
    printt()  # spacing and flushes the \r ending
    quit(f"Program stopped: {msg}")


def realise_dir(path, clear=False):
    # makes sure the directory exists and is empty
    if clear:
        if os.path.isdir(path):
            shutil.rmtree(path)  # faster than removing each file individually
    else:
        if os.path.isdir(path):
            return
    os.mkdir(path)


def run_cmd(cmd):
    try:
        cmd_output = subprocess.run(cmd, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        cmd_output = cmd_output.stdout.decode()
    except subprocess.CalledProcessError as e:
        cmd_output = e.output.decode()
        printt(f"Error process output: {cmd_output}")
        printt(f"Error command:{cmd}\n{traceback.format_exc()}\n{cmd_output}\n"
               f"Process failed with exit code {e.returncode}.")
    return cmd_output


def get_video_ms(path):
    cmd = f"ffprobe -v error -show_entries format=duration -of default=noprint_wrappers=1:nokey=1 {path}"
    video_length = run_cmd(cmd)
    video_length = video_length.replace(".", "")
    video_length = int(video_length) // 1000
    return video_length


def get_video_average_fps(path):
    cmd = f"ffprobe -v error -select_streams v -of default=noprint_wrappers=1:nokey=1 " \
          f"-show_entries stream=avg_frame_rate {path}"
    fps_fraction = run_cmd(cmd)
    fps = eval(fps_fraction.strip())  # is an int
    return fps


def ffmpeg_cmd(arguments_string):
    # wrapper function to make calls to ffmpeg
    cmd = f"ffmpeg -y {arguments_string}"  # -y: overwrite without asking
    return run_cmd(cmd)


def ends_with_any(string, *endings):
    for ending in endings:
        if string.lower().endswith(ending.lower()):
            return True
    return False


def get_file_paths_with_extensions(folder_path, *extensions):
    file_paths = []
    if not os.path.isdir(folder_path):
        return file_paths
    item_names = natsorted(os.listdir(folder_path))
    for item_name in item_names:
        item_path = os.path.join(folder_path, item_name)
        if not os.path.isfile(item_path):
            continue
        for extension in extensions:
            if item_path.lower().endswith(extension.lower()):
                file_paths.append(item_path)
                break  # no need to check the other file extensions if this one matches (this break is not required)
    return file_paths


def ask_folder(multiple=False):
    # returns None if no folder is choosen, otherwise a list of paths
    # all the IDE warnings in this function are false
    folder_paths = None

    def open_file_dialog(w):
        nonlocal folder_paths
        try:
            folder_paths = w.create_file_dialog(dialog_type=webview.FOLDER_DIALOG,
                                                allow_multiple=multiple,
                                                directory=os.getcwd()
                                                )
        except TypeError:
            # user exited file dialog without picking (seems impossible to trigger this statement)
            stop("No folder picked.")
        finally:
            w.destroy()

    window = webview.create_window("", hidden=True)
    webview.start(open_file_dialog, window)
    if folder_paths is None or len(folder_paths) == 0:
        stop("No folder picked.")
    if multiple:
        return folder_paths
    return folder_paths[0]


def ask_file(multiple=False):
    # returns None if no file is choosen, otherwise a list of paths
    # all the IDE warnings in this function are false
    file_paths = None

    def open_file_dialog(w):
        nonlocal file_paths
        try:
            file_paths = w.create_file_dialog(dialog_type=webview.OPEN_DIALOG,
                                              allow_multiple=multiple,
                                              directory=os.getcwd()
                                              )
        except TypeError:
            # user exited file dialog without picking (seems impossible to trigger this statement)
            quit("No file picked.")
        finally:
            w.destroy()

    window = webview.create_window("", hidden=True)
    webview.start(open_file_dialog, window)
    if file_paths is None or len(file_paths) == 0:
        quit("No file picked.")
    if multiple:
        return file_paths
    return file_paths[0]


def ms_to_time_string(ms):
    # 2001 returns 00:00:02.001000
    time_string = datetime.fromtimestamp(ms / 1000.0)
    time_string = time_string - timedelta(hours=1)
    time_string = time_string.strftime("%H:%M:%S.%f")
    return time_string
