# bakerbot

Bakerbot is a Discord bot written in Python. Originally made as a learning exercise, now used by friends as a *somewhat* useful bot and used by me to experiment with dumb ideas.

# Features
- Component-based frontends for Wolfram|Alpha and Mangadex.
- Jokes (some of them are actually funny, I swear).

## Prerequisites
Python (preferably not the snake variety).
```
$ pip install -r requirements.txt
```

You'll also need a `keychain.py` file with the following structure:
```py
DISCORD_TOKEN: str
DEBUG_GUILD: int
WOLFRAM_ID: str
WOLFRAM_SALT: str
```
