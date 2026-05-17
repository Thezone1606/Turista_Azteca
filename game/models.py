"""Modelos de datos para el juego.

Todo es dataclasses serializables a JSON. La lógica vive en `engine.py`;
estos objetos solo guardan estado.
"""
from __future__ import annotations

from dataclasses import dataclass, field, asdict
from enum import Enum
from typing import Any


class TipoCasilla(str, Enum):
    ESTADO = "estado"
    SALIDA = "salida"
    CARCEL = "carcel"
    IR_CARCEL = "ir_carcel"
    ESTACIONAMIENTO = "estacionamiento"
    FORTUNA = "fortuna"
    MULTA = "multa"


@dataclass
class Casilla:
    posicion: int                    # 0..39
    tipo: TipoCasilla
    nombre: str                      # "Chiapas", "Cárcel", etc.
    slug_audio: str                  # slug del mp3 que la describe
    slug_id: str                     # identificador estable ("estado_chis", "carcel", ...)
    precio_hospedaje: int = 0        # solo para ESTADO
    precio_compra: int = 0           # solo para ESTADO
    propietario_id: int | None = None  # id del jugador dueño, o None si libre


@dataclass
class Jugador:
    id: int
    nombre: str
    dinero: int
    posicion: int = 0                # casilla actual
    propiedades: list[str] = field(default_factory=list)  # slug_id de casillas suyas
    turnos_en_carcel: int = 0
    en_carcel: bool = False
    bancarrota: bool = False

    def patrimonio(self, tablero: "Tablero") -> int:
        """Dinero + suma de precios de compra de sus propiedades."""
        total = self.dinero
        by_slug = {c.slug_id: c for c in tablero.casillas}
        for slug in self.propiedades:
            c = by_slug.get(slug)
            if c is not None:
                total += c.precio_compra
        return total


@dataclass
class Tablero:
    casillas: list[Casilla]

    def __post_init__(self) -> None:
        # Index de búsqueda
        self._by_slug = {c.slug_id: c for c in self.casillas}

    @property
    def n(self) -> int:
        return len(self.casillas)

    def por_slug(self, slug_id: str) -> Casilla:
        return self._by_slug[slug_id]

    def avanzar(self, posicion: int, pasos: int) -> tuple[int, bool]:
        """Devuelve (nueva_posicion, paso_por_salida)."""
        nueva = (posicion + pasos) % self.n
        paso_por_salida = (posicion + pasos) >= self.n
        return nueva, paso_por_salida

    def casilla_carcel(self) -> int:
        for c in self.casillas:
            if c.tipo == TipoCasilla.CARCEL:
                return c.posicion
        raise RuntimeError("Tablero sin cárcel")


@dataclass
class Juego:
    tablero: Tablero
    jugadores: list[Jugador]
    turno_idx: int = 0               # índice en self.jugadores
    terminado: bool = False
    ganador_id: int | None = None

    @property
    def jugador_actual(self) -> Jugador:
        return self.jugadores[self.turno_idx]

    def siguiente_turno(self) -> None:
        # Skip jugadores en bancarrota
        for _ in range(len(self.jugadores)):
            self.turno_idx = (self.turno_idx + 1) % len(self.jugadores)
            if not self.jugadores[self.turno_idx].bancarrota:
                return

    def jugadores_activos(self) -> list[Jugador]:
        return [j for j in self.jugadores if not j.bancarrota]


def juego_to_dict(juego: Juego) -> dict[str, Any]:
    return {
        "jugadores": [asdict(j) for j in juego.jugadores],
        "turno_idx": juego.turno_idx,
        "terminado": juego.terminado,
        "ganador_id": juego.ganador_id,
        "casillas_propietarios": {
            c.slug_id: c.propietario_id for c in juego.tablero.casillas if c.propietario_id is not None
        },
    }


def juego_from_dict(data: dict[str, Any], tablero: Tablero) -> Juego:
    jugadores = [Jugador(**j) for j in data["jugadores"]]
    for slug, pid in data.get("casillas_propietarios", {}).items():
        tablero.por_slug(slug).propietario_id = pid
    return Juego(
        tablero=tablero,
        jugadores=jugadores,
        turno_idx=data.get("turno_idx", 0),
        terminado=data.get("terminado", False),
        ganador_id=data.get("ganador_id"),
    )
