#!/usr/bin/env python3
"""Registro interactivo de tarjetas RFID para el juego.

Uso:
    python -m scripts.register_card             # menú interactivo
    python -m scripts.register_card --list      # lista todo lo registrado
    python -m scripts.register_card --delete UID

Si el lector MFRC522 está conectado, escanea físicamente la tarjeta.
Si no, te permite escribir el UID a mano (útil para preparar el mapping
antes de tener hardware).
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from data.phrases import ESTADOS_META  # noqa: E402
from drivers.rfid_reader import RFIDReader  # noqa: E402
from drivers.rfid_registry import VALID_ACTIONS, RFIDRegistry  # noqa: E402
from game.config import JUGADORES  # noqa: E402


def _scan_uid(reader: RFIDReader) -> str | None:
    print()
    if reader.available:
        print("  → Acerca la tarjeta al lector (o escribe un UID hex, o 'skip').")
    else:
        print("  → MFRC522 no detectado. Escribe el UID hex de la tarjeta (o 'skip').")
    uid = reader.read_uid(timeout=60)
    if uid is None:
        print("  (cancelado)")
        return None
    print(f"  UID: {uid}")
    return uid


def cmd_list(registry: RFIDRegistry) -> int:
    cards = registry.all()
    if not cards:
        print("(sin tarjetas registradas)")
        return 0
    print(f"{len(cards)} tarjetas registradas:\n")
    print(f"  {'UID':16s}  {'TIPO':10s}  PAYLOAD")
    for c in cards:
        if c.kind == "player":
            payload = f"id={c.payload['id']}"
        elif c.kind == "casilla":
            payload = f"slug={c.payload['slug']}"
        elif c.kind == "action":
            payload = f"name={c.payload['name']}"
        else:
            payload = str(c.payload)
        print(f"  {c.uid:16s}  {c.kind:10s}  {payload}")
    return 0


def cmd_delete(registry: RFIDRegistry, uid: str) -> int:
    if registry.delete(uid):
        print(f"Eliminado UID {uid.upper()}")
        return 0
    print(f"No estaba registrado: {uid}", file=sys.stderr)
    return 1


def cmd_interactive(registry: RFIDRegistry, reader: RFIDReader) -> int:
    while True:
        print("\n=== Registrar tarjeta ===")
        print("  1) Jugador")
        print("  2) Casilla / estado")
        print("  3) Acción del juego")
        print("  4) Listar todo lo registrado")
        print("  5) Eliminar tarjeta")
        print("  0) Salir")
        opt = input("Opción: ").strip()
        if opt == "0":
            return 0
        if opt == "1":
            _register_player(registry, reader)
        elif opt == "2":
            _register_casilla(registry, reader)
        elif opt == "3":
            _register_action(registry, reader)
        elif opt == "4":
            cmd_list(registry)
        elif opt == "5":
            uid = input("UID a eliminar: ").strip()
            cmd_delete(registry, uid)
        else:
            print("Opción inválida.")


def _register_player(registry: RFIDRegistry, reader: RFIDReader) -> None:
    print("\nJugadores disponibles:")
    for p in JUGADORES:
        print(f"  {p['id']}) {p['nombre']}")
    pid = input("ID del jugador: ").strip()
    try:
        pid_int = int(pid)
    except ValueError:
        print("ID inválido.")
        return
    if pid_int not in {p["id"] for p in JUGADORES}:
        print("ID no existe.")
        return
    uid = _scan_uid(reader)
    if uid is None:
        return
    registry.register_player(uid, pid_int)
    print(f"✓ UID {uid} → jugador {pid_int}")


def _register_casilla(registry: RFIDRegistry, reader: RFIDReader) -> None:
    print("\nCasillas registrables:")
    print("  Estados (slug abreviado):")
    for clave, nombre, _cap in ESTADOS_META:
        print(f"    estado_{clave:6s}  {nombre}")
    print("  Especiales:")
    print("    salida, carcel, ir_carcel, estacionamiento,")
    print("    fortuna_1, fortuna_2, fortuna_3, multa_casilla")
    slug = input("Slug exacto: ").strip()
    if not slug:
        return
    uid = _scan_uid(reader)
    if uid is None:
        return
    registry.register_casilla(uid, slug)
    print(f"✓ UID {uid} → casilla {slug}")


def _register_action(registry: RFIDRegistry, reader: RFIDReader) -> None:
    print(f"\nAcciones válidas: {sorted(VALID_ACTIONS)}")
    name = input("Nombre de la acción: ").strip()
    if name not in VALID_ACTIONS:
        print(f"Acción inválida.")
        return
    uid = _scan_uid(reader)
    if uid is None:
        return
    registry.register_action(uid, name)
    print(f"✓ UID {uid} → acción '{name}'")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--list", action="store_true")
    parser.add_argument("--delete", metavar="UID")
    args = parser.parse_args()

    registry = RFIDRegistry()
    reader = RFIDReader()

    if args.list:
        return cmd_list(registry)
    if args.delete:
        return cmd_delete(registry, args.delete)
    return cmd_interactive(registry, reader)


if __name__ == "__main__":
    sys.exit(main())
