# Bakerbot
Bakerbot is a [discord.py](https://github.com/Rapptz/discord.py) bot written in Python :) Originally made as a learning exercise, now used by friends as a *somewhat* useful bot and used by me to experiment with dumb coding ideas.

## Prerequisites and Execution
You'll need the following Python packages to run Bakerbot:
* [wavelink](https://github.com/PythonistaGuild/Wavelink): Voice functionality.
* [discord.py[voice]](https://github.com/Rapptz/discord.py): Core functionality.

You will also need to download [Lavalink](https://github.com/Frederikam/Lavalink) and a Java runtime (check the Lavalink repository for supported JREs). Make sure your Lavalink server is running before running Bakerbot, otherwise voice commands will not work properly.

These packages are optional but recommended by [aiohttp](https://github.com/aio-libs/aiohttp) to improve performance:
* [cchardet](https://github.com/PyYoshi/cChardet): Python wrapper for the C++ implementation of uchardet.
* [aiodns](https://github.com/saghul/aiodns): Asynchronous DNS resolver using c-ares.
* [brotlipy](https://github.com/python-hyper/brotlicffi): CFFI bindings for Brotli.

Once you've installed all the prerequisites, create a `btoken.py` file and paste your bot token.
```python
token = "ozpH5zE95Cv9DOUGzagKp9zsYdm3Dj99rUhBI1yz5CQ9Ll4ROvHUgyK7OrkcjpkAHk5G1cac3ZUO7jntAAYSHQaPygpW9c1tvp74"
```

Then open a terminal and run `python main.py`. Simple as that!
