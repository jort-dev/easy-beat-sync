# Tools

## Useful ffmpeg commands
Split the input into parts of each 10 seconds:  
`ffmpeg -i input.mp4 -c copy -map 0 -segment_time 00:00:10 -f segment -reset_timestamps 1 output%03d.mp4`
