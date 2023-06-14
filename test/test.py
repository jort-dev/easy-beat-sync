import os

from common import *

path ="/home/jort/Pictures/2023_03_brindisi/C0010.MP4"
t = os.path.getmtime(path)

t1 = ms_to_time_string(t * 1000)
print(t)
print(t1)