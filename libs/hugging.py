import aiohttp
import ujson
import yarl

class Backend:
    """A backend Hugging Face API wrapper."""
    def __init__(self, secrets: dict, session: aiohttp.ClientSession) -> None:
        self.base = "https://api-inference.huggingface.co"
        self.key = secrets.get("hugging-token", None)
        self.session = session

    async def request(self, path: str, payload: dict, headers: dict) -> object:
        """Send a HTTP POST request to the Hugging Face Inference API."""
        url = yarl.URL(f"{self.base}/{path}", encoded=True)

        async with self.session.post(url, json=payload, headers=headers) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            data = ujson.loads(data)
            return data

    async def generate(self, model: str, query: str, chars: int) -> str:
        """Generates text from a given `model` and `query` string."""
        if self.key is None:
            raise RuntimeError("Request attempted without API key.")

        headers = {"Authorization": f"Bearer {self.key}"}
        payload = {"inputs": query, "options": {"wait_for_model": True}, "parameters": {"max_length": chars}}
        data = await self.request(f"models/{model}", payload, headers)

        if isinstance(data, list):
            return data[0]["generated_text"]

        return data["error"]
