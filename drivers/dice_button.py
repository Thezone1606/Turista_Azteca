"""Botón GPIO para tirar dados.

Cableado recomendado:
  - Un lado del botón: GPIO 17 (pin físico 11)
  - Otro lado:         GND     (pin físico 9)
  - Pull-up interno habilitado (sin resistencia externa)

Implementación con `gpiozero` (backend lgpio en kernels modernos).
Si el setup falla por falta de lib o de chip GPIO, queda en modo fallback:
solo acepta Enter por consola. Si SÍ funciona, espera lo que ocurra primero.
"""
from __future__ import annotations

import logging
import select
import sys
import threading
import time

log = logging.getLogger(__name__)

DEFAULT_PIN_BCM = 17           # pin físico 11
BOUNCE_SEC = 0.2               # debounce


class DiceButton:
    def __init__(self, pin_bcm: int = DEFAULT_PIN_BCM) -> None:
        self.pin = pin_bcm
        self.available = False
        self._press_event = threading.Event()
        self._button = None
        self._init_gpio()

    def _init_gpio(self) -> None:
        try:
            from gpiozero import Button  # type: ignore[import-not-found]
        except (ImportError, RuntimeError) as e:
            log.info("DiceButton: gpiozero no disponible (%s) — fallback consola.", e)
            return
        try:
            self._button = Button(self.pin, pull_up=True, bounce_time=BOUNCE_SEC)
            self._button.when_pressed = self._on_press
            self.available = True
            log.info("DiceButton: GPIO %d (BCM) listo via gpiozero.", self.pin)
        except Exception as e:
            log.warning("DiceButton: init falló (%s) — fallback consola.", e)

    def _on_press(self) -> None:
        self._press_event.set()

    def wait_for_trigger(self, allow_console: bool = True) -> str:
        """Bloquea hasta que se dispare el botón o Enter en consola.
        Devuelve 'button' o 'console'.

        Si stdin no es un TTY (ej. corriendo como systemd service con
        StandardInput=null), ignora la consola para no leer EOF en loop.
        """
        if allow_console and not sys.stdin.isatty():
            allow_console = False
        self._press_event.clear()
        while True:
            if self.available and self._press_event.is_set():
                return "button"
            if allow_console:
                ready, _, _ = select.select([sys.stdin], [], [], 0.05)
                if ready:
                    sys.stdin.readline()
                    return "console"
            else:
                time.sleep(0.05)

    def cleanup(self) -> None:
        if self._button is not None:
            try:
                self._button.close()
            except Exception:
                pass
            self._button = None
