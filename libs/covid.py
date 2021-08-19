import aiohttp
import ujson
import yarl

class Backend:
    """Backend COVID-19 API wrapper."""
    def __init__(self, session: aiohttp.ClientSession) -> None:
        self.base = "https://nswdac-covid-19-postcode-heatmap.azurewebsites.net"
        self.session = session

    async def request(self, path: str) -> dict:
        """Sends a HTTP GET request to the COVID-19 API."""
        url = yarl.URL(f"{self.base}/{path}")

        async with self.session.get(url) as resp:
            data = await resp.read()
            data = data.decode("utf-8")
            return ujson.loads(data)
