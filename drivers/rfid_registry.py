"""Mapeo persistente UID de tarjeta RFID → entidad del juego.

Tipos de tarjeta soportados:
  player    → identifica a un jugador: {"kind":"player","id":1|2}
  casilla   → casilla del tablero:    {"kind":"casilla","slug":"estado_cdmx"}
  action    → acción del juego:       {"kind":"action","name":"comprar"|"cancelar"|"si"|"no"|"dados"|"pagar_carcel"}

Persistencia: data/rfid_cards.json (versionado en git para que las tarjetas
del set físico viajen con el repo).
"""
from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

REGISTRY_PATH = Path(__file__).resolve().parent.parent / "data" / "rfid_cards.json"

VALID_ACTIONS = {"comprar", "cancelar", "si", "no", "dados", "pagar_carcel"}


@dataclass
class CardInfo:
    uid: str
    kind: str       # "player" | "casilla" | "action"
    payload: dict   # depende de kind


class RFIDRegistry:
    def __init__(self, path: Path = REGISTRY_PATH) -> None:
        self.path = path
        self._cards: dict[str, dict] = {}
        self._load()

    def _load(self) -> None:
        if not self.path.exists():
            self._cards = {}
            return
        try:
            self._cards = json.loads(self.path.read_text())
        except (json.JSONDecodeError, OSError):
            self._cards = {}

    def _save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.path.with_suffix(".json.tmp")
        tmp.write_text(json.dumps(self._cards, ensure_ascii=False, indent=2, sort_keys=True))
        tmp.replace(self.path)

    # --- consulta ---

    def lookup(self, uid: str) -> CardInfo | None:
        uid = uid.upper()
        data = self._cards.get(uid)
        if data is None:
            return None
        return CardInfo(uid=uid, kind=data["kind"], payload=data)

    def all(self) -> list[CardInfo]:
        return [CardInfo(uid=u, kind=d["kind"], payload=d) for u, d in self._cards.items()]

    # --- registro ---

    def register_player(self, uid: str, player_id: int) -> None:
        self._cards[uid.upper()] = {"kind": "player", "id": player_id}
        self._save()

    def register_casilla(self, uid: str, slug: str) -> None:
        self._cards[uid.upper()] = {"kind": "casilla", "slug": slug}
        self._save()

    def register_action(self, uid: str, name: str) -> None:
        if name not in VALID_ACTIONS:
            raise ValueError(f"acción inválida: {name} (válidas: {sorted(VALID_ACTIONS)})")
        self._cards[uid.upper()] = {"kind": "action", "name": name}
        self._save()

    def delete(self, uid: str) -> bool:
        if uid.upper() in self._cards:
            del self._cards[uid.upper()]
            self._save()
            return True
        return False
