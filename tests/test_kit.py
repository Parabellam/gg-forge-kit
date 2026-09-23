from __future__ import annotations

import json

import pytest

from gg_forge_kit.alerts import RESEND_URL, EmailAlerter
from gg_forge_kit.config import load_json, optional_env, require_env
from gg_forge_kit.heartbeat import Heartbeat


class FakePost:
    """Registra las llamadas HTTP y devuelve una respuesta fija."""

    def __init__(self, status: int = 200, raises: Exception | None = None) -> None:
        self.status = status
        self.raises = raises
        self.calls: list[dict] = []

    async def __call__(self, url, headers, json=None, text=None):
        self.calls.append({"url": url, "headers": headers, "json": json, "text": text})
        if self.raises:
            raise self.raises
        return self.status, "{}"


# ─── config ───────────────────────────────────────────────────────────────────


def test_require_env_fails_when_missing(monkeypatch):
    monkeypatch.delenv("GGFK_TEST", raising=False)
    with pytest.raises(RuntimeError, match="GGFK_TEST"):
        require_env("GGFK_TEST")


def test_optional_env_treats_empty_as_missing(monkeypatch):
    monkeypatch.setenv("GGFK_TEST", "")
    assert optional_env("GGFK_TEST", "x") == "x"


def test_load_json_reports_position_of_syntax_error(tmp_path):
    p = tmp_path / "c.json"
    p.write_text('{"a": 1,}', encoding="utf-8")
    with pytest.raises(ValueError, match="línea 1"):
        load_json(p)


def test_load_json_requires_object_root(tmp_path):
    p = tmp_path / "c.json"
    p.write_text(json.dumps([1, 2]), encoding="utf-8")
    with pytest.raises(ValueError, match="objeto"):
        load_json(p)


def test_load_json_missing_file(tmp_path):
    with pytest.raises(FileNotFoundError):
        load_json(tmp_path / "nope.json")


# ─── heartbeat ────────────────────────────────────────────────────────────────


async def test_heartbeat_pings_url():
    post = FakePost()
    hb = Heartbeat("https://hc-ping.com/abc/", post=post)
    assert await hb.ping() is True
    assert post.calls[0]["url"] == "https://hc-ping.com/abc"


async def test_heartbeat_stays_silent_when_unhealthy():
    post = FakePost()
    hb = Heartbeat("https://hc-ping.com/abc", is_healthy=lambda: False, post=post)
    assert await hb.ping() is False
    assert post.calls == []


async def test_heartbeat_fail_hits_fail_endpoint_with_reason():
    post = FakePost()
    hb = Heartbeat("https://hc-ping.com/abc", post=post)
    await hb.fail("sin permisos")
    assert post.calls[0]["url"] == "https://hc-ping.com/abc/fail"
    assert post.calls[0]["text"] == "sin permisos"


async def test_heartbeat_disabled_without_url():
    post = FakePost()
    hb = Heartbeat(None, post=post)
    assert hb.enabled is False
    assert await hb.ping() is False
    hb.start()  # no debe crear tarea ni fallar
    assert post.calls == []


async def test_heartbeat_swallows_network_errors():
    hb = Heartbeat("https://hc-ping.com/abc", post=FakePost(raises=OSError("sin red")))
    assert await hb.ping() is False


def test_heartbeat_default_interval_is_ten_minutes():
    assert Heartbeat("https://x").interval_seconds == 600


# ─── alerts ───────────────────────────────────────────────────────────────────


async def test_alert_payload_for_resend():
    post = FakePost()
    alerter = EmailAlerter("key", ["a@gmail.com"], bot_name="Centinela", post=post)
    assert await alerter.send("Intento en Privacity", "detalle") is True
    call = post.calls[0]
    assert call["url"] == RESEND_URL
    assert call["headers"]["Authorization"] == "Bearer key"
    assert call["json"]["to"] == ["a@gmail.com"]
    assert call["json"]["subject"] == "[Centinela] Intento en Privacity"
    assert call["json"]["text"] == "detalle"


async def test_alert_rate_limit_and_suppressed_count():
    now = [0.0]
    post = FakePost()
    alerter = EmailAlerter("k", ["a@gmail.com"], max_per_hour=2, post=post, clock=lambda: now[0])
    assert await alerter.send("1", "b") is True
    assert await alerter.send("2", "b") is True
    assert await alerter.send("3", "b") is False
    assert await alerter.send("4", "b") is False
    assert alerter.suppressed == 2

    now[0] = 3601  # pasa la hora: se libera el cupo
    assert await alerter.send("5", "cuerpo") is True
    assert "Se omitieron 2 alertas" in post.calls[-1]["json"]["text"]
    assert alerter.suppressed == 0


async def test_alert_never_raises_on_http_error():
    alerter = EmailAlerter("k", ["a@gmail.com"], post=FakePost(status=422))
    assert await alerter.send("x", "y") is False


def test_alert_from_env_disabled_when_incomplete(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "k")
    monkeypatch.delenv("ALERTAS_DESTINATARIOS", raising=False)
    assert EmailAlerter.from_env() is None


def test_alert_from_env_splits_recipients(monkeypatch):
    monkeypatch.setenv("RESEND_API_KEY", "k")
    monkeypatch.setenv("ALERTAS_DESTINATARIOS", "a@gmail.com, b@gmail.com ,")
    alerter = EmailAlerter.from_env()
    assert alerter is not None
    assert alerter.recipients == ["a@gmail.com", "b@gmail.com"]
