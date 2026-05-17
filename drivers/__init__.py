"""Drivers de hardware para Turista Mundial Azteca.

Todos los drivers son plug-and-play: intentan inicializar el hardware
al arrancar; si falla, marcan `available = False` y el código de juego
cae limpio a entrada por consola.
"""
from drivers.dice_button import DiceButton
from drivers.rfid_reader import RFIDReader
from drivers.rfid_registry import RFIDRegistry

__all__ = ["DiceButton", "RFIDReader", "RFIDRegistry"]
