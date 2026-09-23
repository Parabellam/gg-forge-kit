"""Validadores para los JSON de configuración de los bots.

Los errores dicen dónde está el problema y cómo arreglarlo, porque quien edita la config es una
persona, no un programa: `fundadores[1]: se esperaba un ID de Discord…`.
"""

from __future__ import annotations

import difflib
from typing import Any


class ConfigError(ValueError):
    pass


def check_keys(obj: Any, allowed: set[str], where: str) -> dict[str, Any]:
    """Rechaza claves desconocidas, sugiriendo la más parecida.

    Un error de tipeo no debe pasar desapercibido dejando un valor por defecto sin avisar.
    Las claves que empiezan por «_» se permiten como comentarios (JSON no tiene comentarios).
    """
    if not isinstance(obj, dict):
        raise ConfigError(f"{where}: se esperaba un objeto JSON")
    for key in obj:
        if key.startswith("_") or key in allowed:
            continue
        close = difflib.get_close_matches(key, sorted(allowed), n=1)
        hint = f" ¿Quisiste decir «{close[0]}»?" if close else ""
        raise ConfigError(f"{where}: clave desconocida «{key}».{hint}")
    return obj


def discord_id(value: Any, where: str) -> int:
    """ID de Discord (> 0). Acepta también strings de dígitos."""
    if isinstance(value, str) and value.isdigit():
        value = int(value)
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ConfigError(
            f"{where}: se esperaba un ID de Discord (número > 0), llegó {value!r}. ¿Falta rellenar el ID real?"
        )
    return value


def discord_ids(values: Any, where: str) -> frozenset[int]:
    if values is None:
        return frozenset()
    if not isinstance(values, list):
        raise ConfigError(f"{where}: se esperaba una lista de IDs")
    return frozenset(discord_id(v, f"{where}[{i}]") for i, v in enumerate(values))


def choice(value: Any, options: tuple[str, ...], where: str) -> str:
    if value not in options:
        raise ConfigError(f"{where}: debe ser uno de {', '.join(options)}; llegó {value!r}")
    return value


def positive_int(value: Any, where: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
        raise ConfigError(f"{where}: debe ser un entero > 0")
    return value


def positive_number(value: Any, where: str) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ConfigError(f"{where}: debe ser un número > 0")
    return float(value)


def string_list(values: Any, where: str) -> tuple[str, ...]:
    if values is None:
        return ()
    if not isinstance(values, list) or not all(isinstance(v, str) for v in values):
        raise ConfigError(f"{where}: se esperaba una lista de textos")
    return tuple(values)
