from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

load_dotenv()


def require_env(name: str) -> str:
    """Devuelve la variable de entorno o falla con un mensaje claro si falta o está vacía."""
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Variable de entorno requerida: {name}")
    return value


def optional_env(name: str, default: str | None = None) -> str | None:
    """Devuelve la variable de entorno, o `default` si falta o está vacía."""
    value = os.getenv(name)
    return value if value else default


def load_json(path: str | Path) -> dict[str, Any]:
    """Carga un archivo de configuración JSON cuyo contenido raíz debe ser un objeto."""
    path = Path(path)
    if not path.exists():
        raise FileNotFoundError(f"No se encontró el archivo de configuración: {path}")
    try:
        with open(path, encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as e:
        raise ValueError(f"JSON inválido en {path} (línea {e.lineno}, columna {e.colno}): {e.msg}") from e
    if not isinstance(data, dict):
        raise ValueError(f"{path} debe contener un objeto JSON en la raíz")
    return data
