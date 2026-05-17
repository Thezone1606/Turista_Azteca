"""Tablero canónico de 40 casillas.

Orden clockwise empezando en Salida (esquina SO):
  Sur/Sureste (1-9) → CÁRCEL (10) → Centro/Este (11-19) →
  ESTACIONAMIENTO (20) → Centro/Norte (21-29) → IR A CÁRCEL (30) →
  Oeste/Pacífico (31-39) → vuelve a SALIDA.

Cada lado tiene 8 estados + 1 fortuna o multa, distribución 8-8-8-8 = 32 estados.
"""
from __future__ import annotations

from data.phrases import ESTADOS_META, PRECIOS_HOSPEDAJE
from game.config import (
    COMPRA_X_HOSPEDAJE,
    SLUG_CARCEL,
    SLUG_ESTACIONAMIENTO,
    SLUG_FORTUNA,
    SLUG_IR_CARCEL,
    SLUG_MULTA_CASILLA,
    SLUG_SALIDA,
)
from game.models import Casilla, Tablero, TipoCasilla

# Orden geográfico clockwise (clave del estado en ESTADOS_META).
# 4 grupos de 8 estados — Sur, Este/Centro, Norte/Bajío, Oeste/Pacífico.
ORDEN_GEOGRAFICO = [
    # Sur/Sureste (casillas 1..6, 8..9 con fortuna en 7)
    "gro", "oax", "chis", "tab", "camp", "yuc", "qroo", "ver",
    # Este/Centro (11..15, 17..19 con fortuna en 16)
    "pue", "tlax", "mor", "cdmx", "mex", "hgo", "qro", "gto",
    # Norte/Bajío (21..25, 27..29 con fortuna en 26)
    "slp", "ags", "zac", "nl", "coah", "tamps", "dgo", "chih",
    # Oeste/Pacífico (31..34, 36..39 con multa en 35)
    "son", "sin", "bc", "bcs", "nay", "jal", "col", "mich",
]

# Las casillas no-estado de cada lado (índice relativo dentro del lado 1..9).
# Lado 1 (sur): pos 7 = fortuna
# Lado 2 (este): pos 16 = fortuna  (= 6 dentro del lado)
# Lado 3 (norte): pos 26 = fortuna (= 6 dentro del lado)
# Lado 4 (oeste): pos 35 = multa   (= 5 dentro del lado)
# El resto del lado son estados.
ESPECIALES_POR_POS: dict[int, tuple[TipoCasilla, str, str, str]] = {
    # pos: (tipo, slug_id, nombre, slug_audio)
    0:  (TipoCasilla.SALIDA,          SLUG_SALIDA,         "Salida",                "evento_pasa_salida"),
    7:  (TipoCasilla.FORTUNA,         f"{SLUG_FORTUNA}_1", "Tarjeta de fortuna",    "evento_carta"),
    10: (TipoCasilla.CARCEL,          SLUG_CARCEL,         "Cárcel",                "evento_libre"),
    16: (TipoCasilla.FORTUNA,         f"{SLUG_FORTUNA}_2", "Tarjeta de fortuna",    "evento_carta"),
    20: (TipoCasilla.ESTACIONAMIENTO, SLUG_ESTACIONAMIENTO,"Estacionamiento gratis","evento_libre"),
    26: (TipoCasilla.FORTUNA,         f"{SLUG_FORTUNA}_3", "Tarjeta de fortuna",    "evento_carta"),
    30: (TipoCasilla.IR_CARCEL,       SLUG_IR_CARCEL,      "Ir a la cárcel",        "evento_carcel"),
    35: (TipoCasilla.MULTA,           SLUG_MULTA_CASILLA,  "Multa de impuestos",    "evento_multa"),
}


def _nombre_capital(clave: str) -> tuple[str, str]:
    for c, nombre, capital in ESTADOS_META:
        if c == clave:
            return nombre, capital
    raise KeyError(f"Estado desconocido: {clave}")


def construir_tablero() -> Tablero:
    casillas: list[Casilla] = []
    estados_iter = iter(ORDEN_GEOGRAFICO)
    for pos in range(40):
        if pos in ESPECIALES_POR_POS:
            tipo, slug_id, nombre, slug_audio = ESPECIALES_POR_POS[pos]
            casillas.append(Casilla(
                posicion=pos,
                tipo=tipo,
                nombre=nombre,
                slug_audio=slug_audio,
                slug_id=slug_id,
            ))
        else:
            clave = next(estados_iter)
            nombre, _capital = _nombre_capital(clave)
            hosp = PRECIOS_HOSPEDAJE[clave]
            casillas.append(Casilla(
                posicion=pos,
                tipo=TipoCasilla.ESTADO,
                nombre=nombre,
                slug_audio=f"estado_{clave}",
                slug_id=f"estado_{clave}",
                precio_hospedaje=hosp,
                precio_compra=hosp * COMPRA_X_HOSPEDAJE,
            ))
    # Sanity check
    n_estados = sum(1 for c in casillas if c.tipo == TipoCasilla.ESTADO)
    if n_estados != 32:
        raise RuntimeError(f"Tablero mal construido: {n_estados} estados (esperaba 32)")
    return Tablero(casillas)
