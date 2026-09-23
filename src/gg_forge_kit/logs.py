from __future__ import annotations

import logging
import sys


def setup_logging(level: str = "INFO") -> None:
    """Configura el formato de logs común a todos los bots de GG Forge."""
    logging.basicConfig(
        level=getattr(logging, level.upper(), logging.INFO),
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
        force=True,
    )
