# Easy Beat Sync - EBS
Generate a video of your photos and videos, synced to the beat of your song!

## Usage
Create a new folder. This folder needs to contain the following :
* another folder, with your videos and photos to use
* a music file, for example .mp3
* a timestamps file, which you can create with the included beat marker tool (live demo: [live demo](https://jort.dev/marker))

Now run the program `main.py`. It will prompt you for a folder, select the folder you created above.
The program will:
* Extract the frames of your videos
* Match those extracted frames to the beat of the song using the timestamps file
* Generate a video with those frames, and paste the music in it
* Save that video in the selected folder

## Tips
* Edit your photos and videos with the included `video_editor` tool, for example to set them all to the same resolution, or to add text to each
* Split your videos into multiple smaller ones, using the included `video_splitter` tool
* Edit the timestamps file, by for example shifting all the timestamps 1 frame earlier, with the included `timestamp_tool`


### Improvements
* could cut videos obviously too long
