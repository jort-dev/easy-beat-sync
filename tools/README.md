# Tools

## Useful ffmpeg commands
Split the input into parts of each 10 seconds:  
`ffmpeg -i input.mp4 -c copy -map 0 -segment_time 00:00:10 -f segment -reset_timestamps 1 output%03d.mp4`


## Google Pixel motion photo video extractor
https://github.com/cliveontoast/GoMoPho  
Sometimes, the extracted videos only play in VLC, and ffmpeg and other programs like mine do not know how to deal with them.  
If this happens, convert them using HandBrakeCli
`HandBrakeCLI -i input.mp4 -o output.mp4`

## Run a command for all files in folder
https://stackoverflow.com/questions/5784661/how-do-you-convert-an-entire-directory-with-ffmpeg  


`for i in *.mp4; do ffmpeg -i "$i" "${i%.*}_converted.mp4"; done`

