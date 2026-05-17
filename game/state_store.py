"""Persistencia del estado del juego en data/state.json."""
from __future__ import annotations

import json
from pathlib import Path

from game.models import Juego, Tablero, juego_from_dict, juego_to_dict

STATE_PATH = Path(__file__).resolve().parent.parent / "data" / "state.json"


def guardar(juego: Juego, path: Path = STATE_PATH) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(juego_to_dict(juego), ensure_ascii=False, indent=2))
    tmp.replace(path)


def cargar(tablero: Tablero, path: Path = STATE_PATH) -> Juego | None:
    if not path.exists():
        return None
    try:
        data = json.loads(path.read_text())
        return juego_from_dict(data, tablero)
    except (json.JSONDecodeError, KeyError, TypeError):
        return None


def limpiar(path: Path = STATE_PATH) -> None:
    if path.exists():
        path.unlink()
