from discord.ext import commands

# Admin Abuse class (stores information about the server).
class adminAbuse:
    serverID = 554211911697432576
    defaultRole = 702649631875792926

# Common colours.
errorColour = 0xFF3300
successColour = 0x00C92C
regularColour = 0xF5CC00
gamingColour = 0x0095FF

# Wavelink node dictionary.
wavelinkNodes = {
    "main": {
        "host": "127.0.0.1",
        "port": 2333,
        "rest_uri": "http://127.0.0.1:2333",
        "password": "youshallnotpass",
        "identifier": "main",
        "region": "sydney"
    }
}

# A regex for URLs.
urlRegex = r"(?i)\b((?:https?://|www\d{0,3}[.]|[a-z0-9.\-]+[.][a-z]{2,4}/)(?:[^\s()<>]+|\(([^\s()<>]+|(\([^\s()<>]+\)))*\))+(?:\(([^\s()<>]+|(\([^\s()<>]+\)))*\)|[^\s`!()\[\]{};:'\".,<>?«»“”‘’]))"

# Custom errors.
class CogDoesntExist(commands.CommandError): pass
class GiveawayInProgress(commands.CommandError): pass
class AlreadyConnectedToChannel(commands.CommandError): pass
class NoChannelToConnectTo(commands.CommandError): pass
class QueueIsEmpty(commands.CommandError): pass
class NoTracksFound(commands.CommandError): pass
