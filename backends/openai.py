from abcs import text
import exceptions
import model

import ujson
import http

class Backend(text.Backend):
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        cls.base = "https://api.openai.com/v1"
        cls.session = bot.session
        cls.token = bot.secrets.get("openai-token", None)

    @classmethod
    def name(cls) -> str:
        return "OpenAI"

    @classmethod
    async def post(cls, endpoint: str, **kwargs) -> dict:
        """Send a HTTP POST request to OpenAI."""
        async with cls.session.post(f"{cls.base}/{endpoint}", **kwargs) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                raise exceptions.HTTPUnexpected(response.status)

            return data

    @classmethod
    async def generate(cls, model: text.Model, query: str) -> str:
        """Generate text using OpenAI."""
        if cls.token is None:
            raise exceptions.SecretNotFound("openai-token not found in secrets.json.")

        headers = {"Authorization": f"Bearer {cls.token}"}

        payload = {
            "prompt": query,
            "max_tokens": model.maximum,
            "temperature": model.temperature,
            "echo": not model.remove_input,
            "frequency_penalty": model.repetition_penalty - 1.0
        }

        data = await cls.post(f"engines/{model.identifier}/completions", json=payload, headers=headers)
        return data["choices"][0]["text"]

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
