from __future__ import annotations

import asyncio
import logging
from typing import Callable

from gg_forge_kit._http import PostFn, http_post

log = logging.getLogger(__name__)

DEFAULT_INTERVAL_MINUTES = 10
RETRY_SECONDS = 30


class Heartbeat:
    """Latido hacia healthchecks.io (o cualquier URL compatible).

    Si el bot deja de hacer ping, healthchecks.io avisa por correo. Por eso **no** se hace ping
    cuando `is_healthy()` es falso (p. ej. el bot perdió la conexión con Discord): callarse es
    la forma de pedir ayuda.

    Si un ping no sale (bot aún conectándose, o fallo de red) se reintenta a los
    `RETRY_SECONDS` en vez de esperar el intervalo completo: si no, tras cada despliegue el
    primer ping tardaría un intervalo entero y healthchecks.io daría una falsa alarma.

    Sin URL configurada el latido queda desactivado; así el bot funciona igual en local.
    """

    def __init__(
        self,
        url: str | None,
        *,
        interval_minutes: float = DEFAULT_INTERVAL_MINUTES,
        is_healthy: Callable[[], bool] = lambda: True,
        post: PostFn = http_post,
    ) -> None:
        self.url = url.rstrip("/") if url else None
        self.interval_seconds = interval_minutes * 60
        self._is_healthy = is_healthy
        self._post = post
        self._task: asyncio.Task[None] | None = None
        self._was_unhealthy = False

    @property
    def enabled(self) -> bool:
        return self.url is not None

    async def ping(self) -> bool:
        """Envía un latido si el bot está sano. Devuelve si el ping llegó."""
        if not self.url:
            return False
        if not self._is_healthy():
            if not self._was_unhealthy:  # solo al cambiar de estado, para no inundar el log
                log.warning("Latido omitido: el bot no está sano.")
            self._was_unhealthy = True
            return False
        if self._was_unhealthy:
            log.info("Bot sano de nuevo: se reanuda el latido.")
            self._was_unhealthy = False
        return await self._send(self.url, None)

    async def fail(self, reason: str) -> bool:
        """Marca el monitor como caído de inmediato (sin esperar a que venza el plazo)."""
        if not self.url:
            return False
        return await self._send(f"{self.url}/fail", reason[:10_000])

    def start(self) -> None:
        if not self.url:
            log.info("Latido desactivado (sin HEARTBEAT_URL).")
            return
        if self._task is None or self._task.done():
            self._task = asyncio.create_task(self._loop(), name="heartbeat")
            log.info("Latido activo cada %.0f min.", self.interval_seconds / 60)

    async def stop(self) -> None:
        if self._task is not None:
            self._task.cancel()
            try:
                await self._task
            except asyncio.CancelledError:
                pass
            self._task = None

    async def tick(self) -> float:
        """Un ciclo del latido. Devuelve cuántos segundos esperar hasta el siguiente."""
        sent = await self.ping()
        return self.interval_seconds if sent else RETRY_SECONDS

    async def _loop(self) -> None:
        while True:
            await asyncio.sleep(await self.tick())

    async def _send(self, url: str, text: str | None) -> bool:
        try:
            status, _ = await self._post(url, {}, None, text)
        except Exception as e:  # la red nunca debe tumbar al bot
            log.warning("Latido fallido: %s", e)
            return False
        if status >= 400:
            log.warning("Latido rechazado (HTTP %d).", status)
            return False
        return True
