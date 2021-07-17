# Bakerbot
Bakerbot is a [discord.py](https://github.com/Rapptz/discord.py) bot written in Python :) Originally made as a learning exercise, now used by friends as a *somewhat* useful bot and used by me to experiment with dumb coding ideas.

## Prerequisites and Execution
Install Bakerbot's requirements by running the following command:
```
$ pip install -r requirements.txt
```

Once all the prerequisites are installed, create a `secrets.json` file and format it like so:
```json
{
    "discord-token": "YOUR DISCORD TOKEN HERE",

    // Optional fields, you may leave these out.
    "wolfram-id": "YOUR WOLFRAM ID HERE",
    "wolfram-salt": "YOUR WOLFRAM SALT HERE",
    "wolfram-hash": "true/false"
}
```

> If the `wolfram-id` field is not specified, functionality related to WolframAlpha will be disabled. 

Then open a terminal and run `python main.py`. Simple as that!
