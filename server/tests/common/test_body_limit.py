"""What a request may weigh, before anybody has read it."""

import pytest
from fastapi import FastAPI, Request
from httpx import ASGITransport, AsyncClient
from starlette.requests import ClientDisconnect

from src.common.body_limit import BodySizeLimit

CAP = 1024


def _app() -> FastAPI:
    """An application that reads its body, behind the limit."""
    app = FastAPI()

    @app.post("/swallow")
    async def swallow(request: Request) -> dict[str, int]:
        return {"read": len(await request.body())}

    app.add_middleware(BodySizeLimit, max_bytes=CAP)
    return app


def _client() -> AsyncClient:
    return AsyncClient(transport=ASGITransport(app=_app()), base_url="http://test")


async def test_a_body_within_the_cap_goes_through() -> None:
    async with _client() as client:
        response = await client.post("/swallow", content=b"x" * CAP)

    assert response.status_code == 200
    assert response.json() == {"read": CAP}


async def test_a_body_announcing_too_much_is_refused_before_it_is_read() -> None:
    """The refusal reads off `Content-Length`: nothing is spooled to answer it."""
    async with _client() as client:
        response = await client.post("/swallow", content=b"x" * (CAP + 1))

    assert response.status_code == 413
    assert "volumineux" in response.json()["detail"]


async def test_the_refusal_says_what_the_cap_is() -> None:
    async with _client() as client:
        response = await client.post("/swallow", content=b"x" * (CAP + 1))

    assert str(CAP) in response.json()["detail"]


async def test_a_body_that_announces_nothing_is_cut_off_at_the_cap() -> None:
    """Chunked, there is no `Content-Length` to read: the bytes are counted as
    they arrive, and the request is dropped rather than swallowed whole."""

    async def streamed() -> bytes:
        for _ in range(10):
            yield b"x" * CAP  # type: ignore[misc]

    async with _client() as client:
        # What the cut-off looks like from inside: the parser asks for more
        # and is told the caller has gone.
        with pytest.raises(ClientDisconnect):
            await client.post("/swallow", content=streamed())


async def test_a_request_with_no_body_at_all_is_untouched() -> None:
    async with _client() as client:
        response = await client.post("/swallow")

    assert response.status_code == 200
    assert response.json() == {"read": 0}
