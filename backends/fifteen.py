import exceptions
import model

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
        """Sends a HTTP GET request to the FifteenAI API."""
        async with cls.session.post(f"{cls.base}/{endpoint}", **kwargs) as response:
            data = await response.json(loads=ujson.loads, content_type=None)

            if response.status == http.HTTPStatus.NOT_FOUND:
                message = data.get("message", None)
                raise exceptions.HTTPUnexpected(response.status, message)
            elif response.status != http.HTTPStatus.OK:
                raise exceptions.HTTPUnexpected(response.status)

            return data

    @classmethod
    async def generate(cls, voice: str, text: str) -> str:
        """Generates a text-to-speech WAV of `text` using the FifteenAI API."""
        payload = {"character": voice, "emotion": "Contextual", "text": text}
        response = await cls.post("app/getAudioFile5", json=payload)
        filename = response["wavNames"][0]

        return f"{cls.cdn}/audio/{filename}"

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
