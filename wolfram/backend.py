import wolfram.types as types

import urllib.parse
import dataclasses
import titlecase
import multidict
import keychain
import aiohttp
import hashlib
import yarl

class Error(Exception):
    """Wolfram|Alpha returned an error."""
    def __init__(self, reason: str):
        self.reason = reason

    def __str__(self):
        return self.reason

@dataclasses.dataclass
class State:
    """The equivalent of a State object."""
    name: str
    input: str

@dataclasses.dataclass
class Pod:
    """The equivalent of a Pod object."""
    id: str
    title: str
    pictures: list[str]
    states: list[State]

@dataclasses.dataclass
class Response:
    """Answers from Wolfram|Alpha."""
    parameters: multidict.MultiDict
    pods: list[Pod]

def digest(parameters: multidict.MultiDict) -> str:
    """Compute the MD5 digest for a set of parameters."""
    payload = "".join(f"{k}{urllib.parse.quote_plus(v)}" for k, v in sorted(parameters.items()))
    data = f"{keychain.WOLFRAM_SALT}{payload}"

    signature = hashlib.md5(data.encode())
    return signature.hexdigest().upper()

def parse(payload: types.Payload) -> list[Pod]:
    """Parse a payload into a list of capsules."""
    result = payload["queryresult"]

    if result["error"] != False:
        reason = result["error"]["msg"]
        raise Error(reason)

    return [
        Pod(
            pod["id"],
            titlecase.titlecase(pod["title"]),
            [subpod["img"]["src"] for subpod in pod.get("subpods") or [] if "img" in subpod],

            [
                State(titlecase.titlecase(substate["name"]), substate["input"]) # type: ignore
                for state in (pod.get("states") or [])
                for substate in (state.get("states") or [state])
            ]
        )

        for pod in result.get("pods") or []
    ]

async def request(session: aiohttp.ClientSession, parameters: multidict.MultiDict) -> types.Payload:
    """Send a request to the Wolfram|Alpha API."""
    signed = multidict.MultiDict(parameters, sig=digest(parameters))

    # Seems like aiohttp doesn't know how to canonicalise properly.
    # Or maybe I'm dumb. Either way, this gets around the issue.
    query = urllib.parse.urlencode(signed, quote_via=urllib.parse.quote_plus)
    url = yarl.URL(f"https://api.wolframalpha.com/v2/query.jsp?{query}", encoded=True)

    async with session.get(url) as response:
        return await response.json()

async def ask(session: aiohttp.ClientSession, query: str) -> Response:
    """Query Wolfram|Alpha."""
    parameters = multidict.MultiDict(
        appid=keychain.WOLFRAM_ID,
        output="json",
        format="image",
        mag="3",
        width="1536",
        reinterpret="true",
        input=query
    )

    payload = await request(session, parameters)
    return Response(parameters, parse(payload))
