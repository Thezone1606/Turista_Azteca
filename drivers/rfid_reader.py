"""Lector RFID MFRC522.

Cableado (Pi → MFRC522):
  3.3V  → 3.3V    (pin 1)
  GND   → GND     (pin 6)
  RST   → GPIO 25 (pin 22)
  SDA   → GPIO 8  (pin 24, CE0)
  SCK   → GPIO 11 (pin 23)
  MOSI  → GPIO 10 (pin 19)
  MISO  → GPIO 9  (pin 21)
  IRQ   → no conectado

Si la lib `mfrc522` o SPI no responden, queda en modo fallback: el método
read_uid() solo acepta input por consola (escribir un UID falso o pulsar Enter).

API:
  reader.available -> bool
  reader.read_uid(timeout=None, allow_console=True) -> str | None
       devuelve el UID en hex (sin :), o None en timeout.
       Debounce automático: espera a que la tarjeta se retire antes del
       siguiente read.
"""
from __future__ import annotations

import logging
import select
import sys
import threading
import time

log = logging.getLogger(__name__)

POLL_SEC = 0.1     # cada cuánto preguntamos al chip
DEBOUNCE_SEC = 0.6  # tiempo sin lectura tras un hit antes de aceptar otro


class RFIDReader:
    def __init__(self) -> None:
        self.available = False
        self._reader = None
        self._last_uid: str | None = None
        self._last_seen: float = 0.0
        self._lock = threading.Lock()
        self._init_chip()

    def _init_chip(self) -> None:
        # mfrc522 internamente usa RPi.GPIO y dispara un warning cosmético
        # cuando otro lib ya tomó el pin. Silenciar antes de importar.
        try:
            import RPi.GPIO as _GPIO  # type: ignore[import-not-found]
            _GPIO.setwarnings(False)
        except Exception:
            pass
        try:
            from mfrc522 import SimpleMFRC522  # type: ignore[import-not-found]
        except (ImportError, RuntimeError) as e:
            log.info("RFIDReader: mfrc522 no disponible (%s) — fallback consola.", e)
            return
        try:
            self._reader = SimpleMFRC522()
            self.available = True
            log.info("RFIDReader: MFRC522 inicializado.")
        except Exception as e:
            log.warning("RFIDReader: init falló (%s) — fallback consola.", e)

    # --- API pública ---

    def read_uid(self, timeout: float | None = None, allow_console: bool = True) -> str | None:
        """Espera hasta detectar una tarjeta o input de consola.
        Devuelve el UID como string hex en mayúsculas, o None en timeout."""
        deadline = None if timeout is None else time.monotonic() + timeout

        # buffer para input asíncrono de consola
        while True:
            if deadline is not None and time.monotonic() >= deadline:
                return None

            if self.available:
                uid = self._poll_chip()
                if uid is not None:
                    return uid

            if allow_console:
                ready, _, _ = select.select([sys.stdin], [], [], POLL_SEC)
                if ready:
                    line = sys.stdin.readline().strip()
                    if line:
                        # Permite "skip" para abortar (devuelve None)
                        if line.lower() in ("skip", "saltar", "x"):
                            return None
                        return line.upper()
            else:
                time.sleep(POLL_SEC)

    def _poll_chip(self) -> str | None:
        if self._reader is None:
            return None
        try:
            uid_int, _text = self._reader.read_no_block()  # type: ignore[union-attr]
        except Exception as e:
            log.debug("RFIDReader poll error: %s", e)
            return None
        if uid_int is None:
            # Si llevábamos un last_uid y ya no hay tarjeta, eso "reinicia" el debounce.
            if self._last_uid is not None and time.monotonic() - self._last_seen > DEBOUNCE_SEC:
                self._last_uid = None
            return None
        uid_hex = f"{uid_int:X}"
        now = time.monotonic()
        # Debounce: misma tarjeta dentro de DEBOUNCE_SEC se ignora
        if self._last_uid == uid_hex and (now - self._last_seen) < DEBOUNCE_SEC:
            self._last_seen = now
            return None
        self._last_uid = uid_hex
        self._last_seen = now
        return uid_hex

    def cleanup(self) -> None:
        # mfrc522 SimpleMFRC522 cierra SPI en __del__; nada más que hacer.
        self._reader = None
