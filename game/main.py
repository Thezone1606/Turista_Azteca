"""Loop principal del juego Turista Mundial Azteca.

Modo por defecto: PLUG-AND-PLAY
    python -m game.main
    - Detecta automáticamente el botón GPIO de dados y el lector RFID MFRC522.
    - Si están conectados, los usa; si no, cae limpio a entrada por consola.

Opciones:
    --no-audio          no reproduce mp3 (texto solo)
    --reset             ignora data/state.json y empieza partida nueva
    --auto N            juega N turnos automáticos para stress test
    --console-only      ignora hardware aunque esté presente
"""
from __future__ import annotations

import argparse
import logging
import random
import select
import sys

from drivers import DiceButton, RFIDReader, RFIDRegistry
from game import config as C, state_store
from game.audio import AudioPlayer
from game.board import construir_tablero
from game.engine import jugar_turno
from game.models import Juego, Jugador


# --- IO implementations ---

class ConsoleIO:
    """IO 100% por consola. Sin hardware."""
    def show(self, text: str) -> None:
        print(text)

    def ask_yes_no(self, prompt: str) -> bool:
        while True:
            r = input(f"{prompt} [s/n]: ").strip().lower()
            if r in ("s", "si", "sí", "y", "yes"):
                return True
            if r in ("n", "no"):
                return False

    def press_to_continue(self, prompt: str = "Presiona Enter") -> None:
        input(f"{prompt}... ")

    def trigger_dice(self) -> None:
        input("[Enter] para tirar los dados... ")


class HardwareIO:
    """Plug-and-play. Usa botón GPIO + RFID si están; cae a consola si no."""
    def __init__(self, dice: DiceButton, rfid: RFIDReader, registry: RFIDRegistry) -> None:
        self.dice = dice
        self.rfid = rfid
        self.registry = registry
        # Precomputo: ¿hay tarjetas si/no registradas?
        self._has_yes_no_cards = any(
            c.kind == "action" and c.payload.get("name") in ("si", "no")
            for c in registry.all()
        )

    def show(self, text: str) -> None:
        print(text)

    def trigger_dice(self) -> None:
        if self.dice.available:
            print("[presiona el botón de dados o Enter]... ", end="", flush=True)
        else:
            print("[Enter para tirar los dados]... ", end="", flush=True)
        src = self.dice.wait_for_trigger(allow_console=True)
        print(f"({src})")

    def press_to_continue(self, prompt: str = "Presiona Enter") -> None:
        hint = " (o escanea cualquier tarjeta)" if self.rfid.available else ""
        print(f"{prompt}{hint}... ", end="", flush=True)
        if self.rfid.available:
            uid = self.rfid.read_uid(timeout=300, allow_console=True)
            print(f"({uid or 'enter'})")
        else:
            input()

    def ask_yes_no(self, prompt: str) -> bool:
        # Si stdin no es TTY (service mode), no leer consola — solo RFID
        stdin_ok = sys.stdin.isatty()
        hint = ""
        if self._has_yes_no_cards and self.rfid.available:
            hint = " (escanea SÍ/NO" + (" o teclea s/n" if stdin_ok else ")")
            if stdin_ok:
                hint += ")"
        print(f"{prompt}{hint}", flush=True)
        while True:
            if self.rfid.available and self._has_yes_no_cards:
                uid = self.rfid.read_uid(timeout=0.2, allow_console=False)
                if uid:
                    info = self.registry.lookup(uid)
                    if info and info.kind == "action":
                        name = info.payload.get("name")
                        if name == "si":
                            print("  → SÍ (tarjeta)")
                            return True
                        if name == "no":
                            print("  → NO (tarjeta)")
                            return False
            if stdin_ok:
                ready, _, _ = select.select([sys.stdin], [], [], 0.1)
                if ready:
                    r = sys.stdin.readline().strip().lower()
                    if r in ("s", "si", "sí", "y", "yes"):
                        return True
                    if r in ("n", "no"):
                        return False
            else:
                # Sin stdin y sin RFID con tarjetas SI/NO disponibles, esperaríamos
                # para siempre — por seguridad, default conservador NO (no compra)
                if not (self.rfid.available and self._has_yes_no_cards):
                    print("  (sin medio de respuesta; asumiendo NO)")
                    return False
                # Si hay RFID pero sin tarjetas, hacemos polling más lento
                import time as _t; _t.sleep(0.2)


class AutoIO:
    """IO automatizado para stress test."""
    def show(self, text: str) -> None:
        print(text)

    def ask_yes_no(self, prompt: str) -> bool:
        r = random.random() < 0.7
        print(f"{prompt} [s/n]: {'s' if r else 'n'} (auto)")
        return r

    def press_to_continue(self, prompt: str = "") -> None:
        return

    def trigger_dice(self) -> None:
        return


class _SilentAudio:
    """Drop-in replacement de AudioPlayer cuando --no-audio."""
    def play(self, slug: str) -> None: return
    def play_many(self, slugs: list[str]) -> None: return
    def wait_idle(self, timeout=None) -> None: return
    def stop(self) -> None: return


# --- Setup ---

def nueva_partida() -> Juego:
    tablero = construir_tablero()
    jugadores = [
        Jugador(id=p["id"], nombre=p["nombre"], dinero=C.DINERO_INICIAL)
        for p in C.JUGADORES
    ]
    return Juego(tablero=tablero, jugadores=jugadores)


def imprimir_estado(juego: Juego) -> None:
    print("\n--- Estado ---")
    for j in juego.jugadores:
        flag = " [BANCARROTA]" if j.bancarrota else (" [cárcel]" if j.en_carcel else "")
        prop = ", ".join(j.propiedades) if j.propiedades else "—"
        print(f"  {j.nombre}{flag}: ${j.dinero:,} @ {j.posicion:2d}  | props: {prop}")
    print("--------------")


def _print_banner(dice: DiceButton | None, rfid: RFIDReader | None, console_only: bool) -> None:
    print("=" * 60)
    print("  TURISTA MUNDIAL AZTECA")
    print("=" * 60)
    print(f"  Audio bocina BT: configurado")
    if console_only:
        print(f"  Hardware:        ignorado (--console-only)")
    else:
        ok = lambda b: "\033[32m✓\033[0m" if b else "\033[33m✗ fallback consola\033[0m"
        print(f"  Botón dados:     {ok(dice.available if dice else False)}")
        print(f"  Lector RFID:     {ok(rfid.available if rfid else False)}")
    print("=" * 60)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--no-audio", action="store_true")
    parser.add_argument("--reset", action="store_true")
    parser.add_argument("--auto", type=int, default=0, help="N turnos automáticos")
    parser.add_argument("--console-only", action="store_true",
                        help="ignora hardware (no inicializa GPIO/SPI)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

    audio = _SilentAudio() if args.no_audio else AudioPlayer()

    # --- IO selection ---
    dice: DiceButton | None = None
    rfid: RFIDReader | None = None
    if args.auto > 0:
        io: object = AutoIO()
        _print_banner(None, None, console_only=True)
    elif args.console_only:
        io = ConsoleIO()
        _print_banner(None, None, console_only=True)
    else:
        dice = DiceButton()
        rfid = RFIDReader()
        registry = RFIDRegistry()
        _print_banner(dice, rfid, console_only=False)
        io = HardwareIO(dice, rfid, registry)

    if args.reset:
        state_store.limpiar()

    tablero = construir_tablero()
    juego = state_store.cargar(tablero) or nueva_partida()
    if juego.tablero is not tablero:
        juego.tablero = tablero

    if juego.turno_idx == 0 and all(j.posicion == 0 and j.dinero == C.DINERO_INICIAL for j in juego.jugadores):
        audio.play(C.AUDIO_BIENVENIDA)
        audio.play(C.AUDIO_INSTRUCCIONES)
        audio.play(C.AUDIO_INICIO)

    try:
        turno_count = 0
        while not juego.terminado:
            jugar_turno(juego, audio, io)  # type: ignore[arg-type]
            imprimir_estado(juego)
            state_store.guardar(juego)
            turno_count += 1
            if args.auto and turno_count >= args.auto:
                print(f"\n[auto] alcanzados {args.auto} turnos, deteniendo.")
                break
    except KeyboardInterrupt:
        print("\n[interrumpido] Estado guardado.")
        state_store.guardar(juego)
    finally:
        if dice is not None:
            dice.cleanup()
        if rfid is not None:
            rfid.cleanup()

    if juego.terminado:
        if juego.ganador_id:
            ganador = next(j for j in juego.jugadores if j.id == juego.ganador_id)
            print(f"\n*** GANA {ganador.nombre} ***")
            audio.play(C.AUDIO_GANA[juego.ganador_id])
        else:
            audio.play(C.AUDIO_EMPATE)
        audio.play(C.AUDIO_FIN)
        audio.wait_idle()
        state_store.limpiar()

    audio.stop()
    return 0


if __name__ == "__main__":
    sys.exit(main())
