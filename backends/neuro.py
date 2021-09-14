import exceptions
import model

import ujson
import http

class Model:
    """A class representing a Neuro model."""
    backend = "Neuro API"

    def __init__(self) -> None:
        self.identifier = "60ca2a1e54f6ecb69867c72c"
        self.remove_input = False
        self.temperature = 0.9
        self.maximum = 200

    async def generate(self, query: str) -> None:
        """Generates text using this model's configuration."""
        return await Backend.generate(self, query)

class Backend:
    @classmethod
    def setup(cls, bot: model.Bakerbot) -> None:
        """Initialises an instance of `Backend` using objects from `bot`."""
        cls.base = "https://api.neuro-ai.co.uk"
        cls.session = bot.session
        cls.token = bot.secrets.get("neuro-token", None)

    @classmethod
    async def post(cls, endpoint: str, **kwargs) -> dict:
        """Sends a HTTP POST request to the Neuro API."""
        async with cls.session.post(f"{cls.base}/{endpoint}", **kwargs) as response:
            data = await response.json(encoding="utf-8", loads=ujson.loads)

            if response.status != http.HTTPStatus.OK:
                error = data.get("error", None)
                raise exceptions.HTTPUnexpected(response.status, error)

            return data

    @classmethod
    async def generate(cls, model: Model, query: str) -> str:
        """Generates text using the Neuro API."""
        if cls.token is None:
            raise exceptions.SecretNotFound("neuro-token not found in secrets.json.")

        parameters = {"include_result": "true"}
        headers = {"Authorization": f"Bearer {cls.token}"}

        payload = {
            "modelId": model.identifier,
            "data": query,
            "input_kwargs": {
                "response_length": model.maximum,
                "remove_input": model.remove_input,
                "temperature": model.temperature
            }
        }

        data = await cls.post("SyncPredict", params=parameters, json=payload, headers=headers)

        if data["state"] == "ERROR":
            # API returned HTTP 200 OK, but there's still an error.
            status = http.HTTPStatus.OK
            message = data["result"]
            raise exceptions.HTTPUnexpected(status, message)

        return data["result"][0]["generated_text"]

def setup(bot: model.Bakerbot) -> None:
    Backend.setup(bot)
