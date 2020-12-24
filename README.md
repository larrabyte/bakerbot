# Bakerbot
Bakerbot is a [discord.py](https://github.com/Rapptz/discord.py) bot written in Python :) Originally made as a learning exercise, now used by friends as a useful bot.

## Things To Be Aware Of
The [`extern`](https://github.com/larrabyte/bakerbot/blob/master/cogs/extern.py) command group is specific to the bot hoster. Most commands written by me will utilise Linux binaries, something which cannot work under Windows without WSL. You should probably check it out before you start using this cog.

## Prerequisites and Execution
The following packages are required before running Bakerbot:
* [youtube_dl](https://github.com/ytdl-org/youtube-dl) and [validators](https://github.com/kvesteri/validators): Required for streaming YouTube videos.
* [PyNaCl](https://github.com/pyca/pynacl) and [FFmpeg](https://www.ffmpeg.org/): Required for voice-related functionality.
* [discord.py](https://github.com/Rapptz/discord.py): Core functionality.

Once the packages are installed, make sure to create a `btoken.py` file and paste your bot token.
```python
token = "ozpH5zE95Cv9DOUGzagKp9zsYdm3Dj99rUhBI1yz5CQ9Ll4ROvHUgyK7OrkcjpkAHk5G1cac3ZUO7jntAAYSHQaPygpW9c1tvp74"
```
Please don't actually try and use this token, I just used [random.org](https://random.org/strings) and generated 5 strings, 20 characters each.

Now, simply open a terminal and run:
```
python main.py
```
