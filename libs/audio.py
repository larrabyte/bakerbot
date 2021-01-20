from enum import Enum

import typing as t
import wavelink

class Nodes:
    # Wavelink node dictionary.
    dictionary = {
        "main": {
            "host": "127.0.0.1",
            "port": 2333,
            "rest_uri": "http://127.0.0.1:2333",
            "password": "youshallnotpass",
            "identifier": "main",
            "region": "sydney"
        }
    }

class RepeatMode(Enum):
    none = 0
    one = 1
    all = 2

class Action(Enum):
    normal = 0
    skip = 1
    rewind = 2

class Queue:
    def __init__(self) -> None:
        self.repeating = RepeatMode.none
        self.internal = []
        self.index = 0

    @property
    def length(self) -> int:
        # Return the size of the queue.
        return len(self.internal)

    @property
    def empty(self) -> bool:
        # Return whether the queue is empty.
        return not self.internal

    @property
    def current_track(self) -> t.Optional[wavelink.Track]:
        # Returns the current track pointed to by the index.
        if not self.empty:
            return self.internal[self.index]

        return None

    @property
    def upcoming(self) -> list:
        # Returns tracks that are ahead of the cursor.
        if not self.empty:
            return self.internal[self.index + 1:]

        return []

    @property
    def history(self) -> list:
        # Returns tracks that are behind the cursor.
        if not self.empty:
            return self.internal[:self.index]

        return []

    def add_tracks(self, obj: t.Union[list, wavelink.Track]) -> None:
        # Adds tracks to the internal queue.
        if isinstance(obj, wavelink.Track):
            self.internal.append(obj)
        elif isinstance(obj, list):
            self.internal.extend(obj)

    def get_next_track(self, affect: bool) -> t.Optional[wavelink.Track]:
        # Advances the cursor and returns the next track if possible.
        if not self.empty:
            if self.repeating == RepeatMode.one:
                return self.current_track
            if 0 <= self.index + 1 < self.length:
                result = self.internal[self.index + 1]
                if affect: self.index += 1
                return result
            if self.repeating == RepeatMode.all:
                result = self.internal[0]
                if affect: self.index = 0
                return result

        return None

    def get_previous_track(self, affect: bool) -> t.Optional[wavelink.Track]:
        # Rewinds the cursor and returns the previous track if possible.
        if not self.empty:
            if self.repeating == RepeatMode.one:
                return self.current_track
            if 0 <= self.index - 1 < self.length:
                result = self.internal[self.index - 1]
                if affect: self.index -= 1
                return result
            if self.repeating == RepeatMode.all:
                result = self.internal[self.length - 1]
                if affect: self.index = self.length - 1
                return result

        return None

    def clear_queue(self) -> None:
        # Clears the queue and resets the cursor.
        self.internal.clear()
        self.index = 0

class Player(wavelink.Player):
    def __init__(self, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.action = Action.normal
        self.queue = Queue()

    def futuretrack(self) -> t.Optional[wavelink.Track]:
        # Returns the track to be played in the future depending on the current action.
        if self.action == Action.normal or self.action == Action.skip:
            return self.queue.get_next_track(affect=False)
        if self.action == Action.rewind:
            return self.queue.get_previous_track(affect=False)

    async def playback(self) -> None:
        # Plays the current track if available.
        if (track := self.queue.current_track) is not None:
            await self.play(track)

    async def advance(self) -> None:
        # Advances along the queue while respecting repeat modes.
        if self.action == Action.normal or self.action == Action.skip:
            if (track := self.queue.get_next_track(affect=True)) is not None:
                await self.play(track)
        elif self.action == Action.rewind:
            if (track := self.queue.get_previous_track(affect=True)) is not None:
                await self.play(track)

        # Reset the player action back to normal.
        self.action = Action.normal

    async def teardown(self) -> None:
        try: # Destroy this player.
            await self.destroy()
        except KeyError:
            pass
