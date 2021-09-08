import exceptions

import aiohttp
import ujson
import yarl

class Backend:
    """The Neuro API wrapper."""
    def __init__(self, secrets: dict, session: aiohttp.ClientSession) -> None:
        self.base = "https://api.neuro-ai.co.uk/SyncPredict?include_result=true"
        self.key = secrets.get("neuro-token", None)
        self.session = session

    async def request(self, payload: dict, headers: dict) -> object:
        """Sends a HTTP POST request to the Neuro API."""
        url = yarl.URL(self.base, encoded=True)

        async with self.session.post(url, json=payload, headers=headers) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            data = ujson.loads(data)
            return data

    async def generate(self, query: str, chars: int, **kwargs: dict) -> str:
        """Generates text from a given `model` and `query` string."""
        if self.key is None:
            raise exceptions.SecretNotFound("neuro-token not found in secrets.json.")

        headers = {"Authorization": f"Bearer {self.key}"}
        payload = {"modelId": "60ca2a1e54f6ecb69867c72c", "data": query, "input_kwargs": {"response_length": chars, "remove_input": False, **kwargs}}
        data = await self.request(payload, headers)

        return data["result"][0]["generated_text"]
