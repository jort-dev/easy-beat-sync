"""
A clip is a moment within the result video
- it has a duration with a start and end time
- it has a list of paths to the frames

- the amount of frames should fit the start and end ms
- the fps should fit the result video
"""


class Clip:
    def __init__(self, start_ms, end_ms):
        self.start_ms = start_ms
        self.end_ms = end_ms
        self.duration = self.end_ms - self.start_ms
        self.frame_amount = None
        self.frame_paths = []

    def calculate_required_frames(self, fps):
        ms_between_frames = 1000 / fps
        self.frame_amount = round(self.duration / ms_between_frames)

    def __repr__(self):
        return f"Clip({self.start_ms} to {self.end_ms})"
