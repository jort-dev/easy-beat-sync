#!/usr/bin/env python3
"""
Tool to mark timestamps on a music.
Plays the music when spacebar is pressed.
Each time a key is pressed, the timestamp of that key press is recorded.
When spacebar is pressed again, or when the song ends, the timestamps are written to a .yaml file.

Example usage:
./music_marker.py ~/this/vid/compilation/test_beta/gimme_love.mp3 ~/this/vid/compilation/test_beta/timestamps.yaml
./music_marker.py ~/this/vid/compilation/lovefool.mp3 ~/this/vid/compilation/lovefool_timestamps.yaml
"""
import os
import sys
import tkinter as tk
from pathlib import Path

import pygame
import time
import yaml
from common import *
from PIL import Image, ImageTk


class MusicMarker:
    # this is in a class because then the order of definitions does not matter, and no need to use 'global'
    def __init__(self, music_path, result_path):
        self.music_path = music_path
        self.result_path = result_path
        self.running = True
        self.timestamps = {"type1": [], "type2": []}
        self.left_keyboard = ["q", "a", "z", "w", "s", "x", "e", "d", "c", "r", "f", "v", "t", "g", "b"]
        self.right_keyboard = ["y", "h", "n", "u", "j", "m", "i", "k", "o", "l", "p"]
        self.start_time = 0
        self.started = False
        self.switch_on = False

        # setup music player
        self.SONG_END = pygame.USEREVENT
        pygame.init()
        pygame.mixer.init()
        x = pygame.mixer.music.load(self.music_path)
        print(f"X={x}, type={type(x)}")

        # setup GUI
        self.root = tk.Tk()
        self.root.bind("<Escape>", lambda x: self.stop())
        self.root.bind("<Key>", self.on_key)
        self.root.bind("<space>", self.space_toggle)
        self.root.protocol("WM_DELETE_WINDOW", self.stop)  # set window closing event callback
        # self.root.minsize(500, 400)
        self.root.title("Jorts Music Marker")

        title_label1 = tk.Label(self.root, text="Jorts", font=("arial", 12, "italic"))
        title_label1.pack(side=tk.TOP, fill=tk.X)
        title_label2 = tk.Label(self.root, text="Music Marker", font=("arial", 50, "bold"))
        title_label2.pack(side=tk.TOP, fill=tk.X)

        instruction_label = tk.Label(self.root, text="Press space to start / stop recording song",
                                     font=("arial", 14))
        instruction_label.pack(pady=0)

        self.img1 = Image.open("src/hands_open.png")
        self.img2 = Image.open("src/hands_closed.png")
        self.canvas = tk.Canvas(self.root)
        self.tkinter_image = None  # !!this reference needs to be kept, keeps it safe from garbage collection
        self.canvas.pack(pady=20)

        self.timestamp_label_text = self.generate_label(f"Latest recorded timestamp: 0")
        self.timestamp_count_label_text = self.generate_label(f"Amount of recorded timestamps: 0")
        self.bpm_label_text = self.generate_label(f"BPM: 0")

        # run GUI
        while True:
            if not self.running:
                quit()  # weird crashes if not called from this loop
            self.root.update()
            self.root.update_idletasks()
            if self.started:
                for pygame_event in pygame.event.get():
                    if pygame_event.type == self.SONG_END:  # check if our custom song stopped event has been published
                        print(f"Song ended.")
                        self.on_end()

    def switch_image(self):
        self.canvas.delete("all")  # clear canvas, images otherwise stack
        if not self.switch_on:
            self.tkinter_image = ImageTk.PhotoImage(image=self.img1)
        else:
            self.tkinter_image = ImageTk.PhotoImage(image=self.img2)
        self.switch_on = not self.switch_on

        max_width = self.canvas.winfo_width()
        max_height = self.canvas.winfo_height()
        self.canvas.create_image(max_width // 2, max_height // 2, anchor=tk.CENTER, image=self.tkinter_image)

    def stop(self):
        self.root.destroy()
        self.running = False
        print(f"Stopped.")

    def on_key(self, event):
        pressed_key = str(event.char)
        if self.started:
            timestamp = round(time.time() * 1000) - self.start_time
            type1 = True
            if pressed_key == "r":
                song_pos = pygame.mixer.music.get_pos()
                song_length = pygame.mixer.Sound(self.music_path).get_length()
                song_length = round(song_length * 1000)
                bpm = self.get_bpm()
                bpm_ms = round(60000 / bpm)
                print(f"Repeating sequence with {bpm}bpm ({bpm_ms}ms) from position {song_pos}/{song_length}")
                predicted_type1_timestamps = self.timestamps["type1"]
                last_timestamp = predicted_type1_timestamps[-1]

                while True:
                    generated_timestamp = last_timestamp + bpm_ms
                    predicted_type1_timestamps.append(generated_timestamp)
                    last_timestamp = generated_timestamp
                    song_pos += bpm_ms
                    if song_pos >= song_length:
                        print(f"Filled.")
                        break
                predicted_type1_timestamps.append(song_length)  # so generator script knows how long song is
                self.timestamps["type1"] = predicted_type1_timestamps
                self.on_end(write_end_timestamp=False)
            elif pressed_key in self.left_keyboard:
                self.timestamps["type1"].append(timestamp)
            elif pressed_key in self.right_keyboard:
                self.timestamps["type2"].append(timestamp)
                type1 = False
            else:
                print(f"Key '{pressed_key}' is not bound, use keys [a-z].")
                return

            self.timestamp_label_text.set(f"Last recorded timestamp: {timestamp}")
            self.bpm_label_text.set(f"BPM of last 10 timestamps: {self.get_bpm()}")
            self.timestamp_count_label_text.set(f"Amount of recorded timestamps: {len(self.timestamps['type1'])}")
            self.switch_image()
            print(f"Key '{pressed_key}' pressed, type{1 if type1 else 2} timestamp {timestamp} recorded!")
        else:
            print(f"Key pressed but no song playing.")

    def on_end(self, write_end_timestamp=True):
        timestamp = round(time.time() * 1000) - self.start_time
        if write_end_timestamp:
            self.timestamps["type1"].append(
                timestamp)  # put timestamp at end, so my next scripts knows how long the song is
            print(f"Inserted ending timestamp {timestamp}.")
        print(f"Recording ended.")
        self.started = False
        print(f"Timestamps: {self.timestamps}")
        self.stop_song()
        file = open(self.result_path, "w")
        yaml.safe_dump(self.timestamps, file)
        print(f"Timestamps written to {self.result_path}")
        print(f"You can exit the application now.")
        self.timestamps = {"type1": [], "type2": []}

    def space_toggle(self, _):
        if not self.started:
            self.started = True
            self.start_time = round(time.time() * 1000)
            self.play_song()
            self.switch_image()
        else:
            self.started = False
            self.on_end()

    def get_bpm(self):
        timestamp_sum = 0
        count = 0

        type1_timestamps = self.timestamps["type1"]
        for x in range(1, len(type1_timestamps)):
            timestamp_sum += type1_timestamps[x] - type1_timestamps[x - 1]
            count += 1

        if count == 0:
            return 0
        avg_ms = timestamp_sum / count
        if avg_ms == 0:
            return 0
        bpm = round((60 / avg_ms) * 1000, 1)
        return bpm

    def generate_label(self, initial_text):
        # wrapper function which returns the stringvar of the label, which can be used to edit the label text
        label_text = tk.StringVar()
        label = tk.Label(self.root, textvariable=label_text)
        label.pack(pady=(40, 0))
        label_text.set(initial_text)
        return label_text

    def play_song(self):
        pygame.mixer.music.play()
        pygame.mixer.music.set_endevent(self.SONG_END)  # custom event name which gets published when song is ended

    def stop_song(self):
        pygame.mixer.music.stop()
        pygame.mixer.music.rewind()
        pygame.event.clear()  # clear the published events, so we don't think our song keeps gettings stopped


# argument1: path to music
music_path = sys.argv[1] if len(sys.argv) >= 2 else ask_file()
p = Path(music_path)
output_path = os.path.join(p.parent, f"{p.stem}_timestamps.yaml")

MusicMarker(music_path=music_path, result_path=output_path)
