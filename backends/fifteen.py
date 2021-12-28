import exceptions
import model

import asyncio
import ujson
import http

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://api.15.ai"
        cls.cdn = "https://cdn.15.ai"
        cls.session = bot.session

    @classmethod
    async def post(cls, endpoint: str, **kwargs: dict) -> dict:
        """Send a HTTP POST request to the FifteenAI API."""
        async with cls.session.post(f"{cls.base}/{endpoint}", **kwargs) as response:
            data = await response.json(loads=ujson.loads, content_type=None)

            if response.status == http.HTTPStatus.NOT_FOUND and "message" in data and data["message"] == "server error":
                # Retry the response after waiting 1s (probably some form of rate-limiting).
                await asyncio.sleep(1)
                return await cls.post(endpoint, **kwargs)
            elif response.status == http.HTTPStatus.UNPROCESSABLE_ENTITY:
                raise Unprocessable
            elif response.status != http.HTTPStatus.OK:
                raise exceptions.HTTPUnexpected(response.status)

            return data

    @classmethod
    async def generate(cls, voice: str, text: str) -> str:
        """Generate a text-to-speech WAV of `text` using the FifteenAI API."""
        payload = {"character": voice, "emotion": "Contextual", "text": text}
        response = await cls.post("app/getAudioFile5", json=payload)
        filename = response["wavNames"][0]

        return f"{cls.cdn}/audio/{filename}"

class Unprocessable(Exception):
    """Raised when the API refuses a request due to invalid text input."""
    pass

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
