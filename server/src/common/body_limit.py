"""What a request may weigh, before anybody has read it.

A file is capped at ten megabytes by the entity that carries it — but an
entity only ever sees a request the server has already read to the end. In
between sits a multipart body that Starlette spools to disk while nobody is
counting, so a caller sending ten gigabytes fills the host's disk long before
any rule of ours is consulted. The route's `read(MAX + 1)` bounds what we
*keep*, never what the machine takes in.

So the limit is said twice, and the two places stop two different things.
Caddy stops the bytes before they reach the process at all, which is what
actually protects the host. This says the same number inside the API: an
instance behind another proxy, or none, still refuses on its own and says why
— and a rule only a proxy knows is a rule no test describes.

It is a guard rail rather than a business rule, which is why the number lives
in the configuration and not in an entity: what a *file* may weigh is the
domain's business and stays there, immovable.
"""

from starlette.datastructures import Headers
from starlette.responses import JSONResponse
from starlette.types import ASGIApp, Message, Receive, Scope, Send


class BodySizeLimit:
    """Refuses a request that weighs more than the API agreed to read.

    Plain ASGI rather than `BaseHTTPMiddleware`, which reads the body itself:
    a middleware that swallowed the request to measure it would be the very
    thing being guarded against.
    """

    def __init__(self, app: ASGIApp, max_bytes: int) -> None:
        self._app = app
        self._max_bytes = max_bytes

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":  # pragma: no cover — no websocket here
            await self._app(scope, receive, send)
            return

        if self._announced(scope) > self._max_bytes:
            await self._refuse(scope, receive, send)
            return

        await self._app(scope, self._counted(receive), send)

    def _announced(self, scope: Scope) -> int:
        """What the caller says it is about to send, or nothing if it does not.

        A malformed `Content-Length` is read as nothing: it is the counting
        below that holds either way, and a 400 written here would be this
        module answering a question that is not its own.
        """
        declared = Headers(scope=scope).get("content-length")
        if declared is None:
            return 0
        try:
            return int(declared)
        except ValueError:
            return 0

    def _counted(self, receive: Receive) -> Receive:
        """The same stream, watched.

        Without a `Content-Length` — a chunked body — there is nothing to read
        ahead of time, so the bytes are counted as they arrive. Past the cap
        the request is cut off rather than swallowed: the caller gets no
        readable refusal, which is the price of not announcing itself, and the
        host keeps its disk.
        """
        read = 0

        async def counting() -> Message:
            nonlocal read
            message = await receive()
            if message["type"] == "http.request":
                read += len(message.get("body", b""))
                if read > self._max_bytes:
                    return {"type": "http.disconnect"}
            return message

        return counting

    async def _refuse(self, scope: Scope, receive: Receive, send: Send) -> None:
        answer = JSONResponse(
            status_code=413,
            content={
                "detail": (
                    "Corps de requête trop volumineux : "
                    f"{self._max_bytes} octets au plus."
                )
            },
        )
        await answer(scope, receive, send)
