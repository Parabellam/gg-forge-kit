from __future__ import annotations

from typing import Any, Awaitable, Callable

import aiohttp

# (url, headers, json|None, texto|None) -> (status, cuerpo). Se inyecta en los tests.
PostFn = Callable[[str, dict[str, str], Any, str | None], Awaitable[tuple[int, str]]]

_TIMEOUT = aiohttp.ClientTimeout(total=15)


async def http_post(url: str, headers: dict[str, str], json: Any = None, text: str | None = None) -> tuple[int, str]:
    """POST mínimo con timeout. Devuelve (status, cuerpo) y deja que el llamador decida qué es error."""
    async with aiohttp.ClientSession(timeout=_TIMEOUT) as session:
        async with session.post(url, headers=headers, json=json, data=text) as resp:
            return resp.status, await resp.text()
