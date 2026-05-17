"""State machine del juego.

El motor opera sobre un `Juego` y emite audio + texto a través de la
interfaz `IO`. No conoce nada del medio (consola, RFID, GPIO), eso lo
inyecta `main.py`.
"""
from __future__ import annotations

import random
from dataclasses import dataclass
from typing import Protocol

from game import config as C
from game.audio import AudioPlayer
from game.models import Casilla, Juego, Jugador, Tablero, TipoCasilla


class IO(Protocol):
    """Interfaz mínima de entrada/salida — implementaciones: consola, RFID, etc."""
    def show(self, text: str) -> None: ...
    def ask_yes_no(self, prompt: str) -> bool: ...
    def press_to_continue(self, prompt: str = "Presiona Enter") -> None: ...
    def trigger_dice(self) -> None:
        """Bloquea hasta que el jugador 'dispare' los dados (Enter en consola, botón GPIO en hardware)."""
        ...


# --- Cartas de fortuna (MVP simple) ---

@dataclass
class CartaFortuna:
    descripcion: str               # texto a mostrar
    delta_dinero: int = 0          # +cobra / -paga
    ir_a_carcel: bool = False


CARTAS_FORTUNA: list[CartaFortuna] = [
    CartaFortuna("Cumpleaños: cobra mil pesos del banco.",        +1000),
    CartaFortuna("Premio de lotería: cobra dos mil pesos.",       +2000),
    CartaFortuna("Devolución de impuestos: cobra quinientos.",     +500),
    CartaFortuna("Multa de tránsito: paga quinientos pesos.",      -500),
    CartaFortuna("Reparación de auto: paga mil pesos.",           -1000),
    CartaFortuna("Servicio médico: paga ochocientos pesos.",       -800),
    CartaFortuna("Te metiste al carril contrario. Ve a la cárcel.",  0, ir_a_carcel=True),
]


# --- Helpers ---

def _tirar_dos_dados() -> tuple[int, int]:
    return random.randint(1, 6), random.randint(1, 6)


def _ajustar_dinero(j: Jugador, delta: int, tablero: Tablero) -> bool:
    """Aplica delta al dinero del jugador. Si queda negativo y no puede cubrirlo
    con sus propiedades, marca bancarrota y devuelve False (no-cubierto)."""
    j.dinero += delta
    if j.dinero >= 0:
        return True
    # Intenta liquidar propiedades hipotéticamente — en MVP simple, si no
    # cubre con dinero+patrimonio queda en bancarrota.
    if j.patrimonio(tablero) < 0:
        j.bancarrota = True
        return False
    # Tiene patrimonio pero no líquido; en MVP marcamos bancarrota igual
    # (sin sistema de hipoteca). Mejorable después.
    j.bancarrota = True
    return False


# --- Acciones del motor ---

def jugar_turno(juego: Juego, audio: AudioPlayer, io: IO) -> None:
    """Ejecuta un turno completo del jugador actual."""
    j = juego.jugador_actual
    if j.bancarrota:
        juego.siguiente_turno()
        return

    io.show(f"\n=== Turno del {j.nombre} (dinero: ${j.dinero:,}) ===")
    audio.play(C.AUDIO_TURNO[j.id])

    # --- Cárcel: si está dentro, ofrece pagar / cumplir turnos ---
    if j.en_carcel:
        j.turnos_en_carcel += 1
        io.show(f"{j.nombre} está en la cárcel (turno {j.turnos_en_carcel}/{C.TURNOS_MAX_EN_CARCEL}).")
        if j.dinero >= C.MULTA_CARCEL and io.ask_yes_no(f"¿Pagar ${C.MULTA_CARCEL:,} para salir?"):
            j.dinero -= C.MULTA_CARCEL
            j.en_carcel = False
            j.turnos_en_carcel = 0
            audio.play(C.AUDIO_SALE_CARCEL)
        elif j.turnos_en_carcel >= C.TURNOS_MAX_EN_CARCEL:
            io.show("Sale de la cárcel obligado.")
            if j.dinero >= C.MULTA_CARCEL:
                j.dinero -= C.MULTA_CARCEL
            j.en_carcel = False
            j.turnos_en_carcel = 0
            audio.play(C.AUDIO_SALE_CARCEL)
        else:
            audio.play(C.AUDIO_PIERDE_TURNO)
            juego.siguiente_turno()
            return

    # --- Tirar dados ---
    io.show("(activa los dados)")
    audio.play(C.AUDIO_TIRA_DADOS)
    io.trigger_dice()
    d1, d2 = _tirar_dos_dados()
    total = d1 + d2
    par = d1 == d2
    io.show(f"Dados: {d1} + {d2} = {total}{' (par)' if par else ''}")
    audio.play(C.AUDIO_DADO[total])

    # --- Mover ficha ---
    nueva, paso_salida = juego.tablero.avanzar(j.posicion, total)
    j.posicion = nueva
    if paso_salida:
        j.dinero += C.COBRO_SALIDA
        io.show(f"Pasó por la SALIDA, cobra ${C.COBRO_SALIDA:,}.")
        audio.play(C.AUDIO_PASA_SALIDA)

    casilla = juego.tablero.casillas[nueva]
    io.show(f"Cae en [{casilla.posicion}] {casilla.nombre}.")
    audio.play(casilla.slug_audio)

    # --- Resolver casilla ---
    _resolver(juego, j, casilla, audio, io)

    # --- Par = otro turno (a menos que esté en cárcel ahora) ---
    if par and not j.en_carcel and not j.bancarrota:
        audio.play(C.AUDIO_PAR)
        io.show("Par: tira otra vez.")
        # llamada recursiva controlada (no avanza turno)
        jugar_turno(juego, audio, io)
        return

    # --- Verificar fin de juego ---
    activos = juego.jugadores_activos()
    if len(activos) <= 1:
        juego.terminado = True
        juego.ganador_id = activos[0].id if activos else None
        return

    juego.siguiente_turno()


def _resolver(juego: Juego, j: Jugador, casilla: Casilla, audio: AudioPlayer, io: IO) -> None:
    """Aplica la mecánica de la casilla donde cayó el jugador."""
    if casilla.tipo == TipoCasilla.SALIDA:
        # ya cobró al pasar
        return

    if casilla.tipo == TipoCasilla.CARCEL:
        io.show("Está solo de visita en la cárcel.")
        return

    if casilla.tipo == TipoCasilla.ESTACIONAMIENTO:
        io.show("Estacionamiento gratis. Descansa.")
        return

    if casilla.tipo == TipoCasilla.IR_CARCEL:
        _enviar_carcel(j, juego.tablero, audio, io)
        return

    if casilla.tipo == TipoCasilla.MULTA:
        io.show(f"Paga multa de ${C.MULTA_IMPUESTOS:,}.")
        if not _ajustar_dinero(j, -C.MULTA_IMPUESTOS, juego.tablero):
            audio.play(C.AUDIO_SIN_DINERO)
        return

    if casilla.tipo == TipoCasilla.FORTUNA:
        carta = random.choice(CARTAS_FORTUNA)
        io.show(f"Carta de fortuna: {carta.descripcion}")
        if carta.ir_a_carcel:
            _enviar_carcel(j, juego.tablero, audio, io)
            return
        if carta.delta_dinero > 0:
            j.dinero += carta.delta_dinero
            audio.play(C.AUDIO_PREMIO)
        elif carta.delta_dinero < 0:
            if not _ajustar_dinero(j, carta.delta_dinero, juego.tablero):
                audio.play(C.AUDIO_SIN_DINERO)
            else:
                audio.play(C.AUDIO_MULTA)
        return

    if casilla.tipo == TipoCasilla.ESTADO:
        _resolver_estado(juego, j, casilla, audio, io)


def _resolver_estado(juego: Juego, j: Jugador, casilla: Casilla, audio: AudioPlayer, io: IO) -> None:
    if casilla.propietario_id is None:
        # Libre: ofrecer comprar
        if j.dinero >= casilla.precio_compra:
            audio.play(C.AUDIO_COMPRA)
            if io.ask_yes_no(f"¿Comprar {casilla.nombre} por ${casilla.precio_compra:,}? (renta ${casilla.precio_hospedaje:,})"):
                j.dinero -= casilla.precio_compra
                casilla.propietario_id = j.id
                j.propiedades.append(casilla.slug_id)
                io.show(f"{j.nombre} ahora es dueño de {casilla.nombre}.")
        else:
            io.show(f"No alcanza para comprar {casilla.nombre} (cuesta ${casilla.precio_compra:,}).")
        return

    if casilla.propietario_id == j.id:
        io.show("Está en su propio estado, no paga renta.")
        return

    # De otro jugador: paga renta
    renta = casilla.precio_hospedaje
    dueño = next((o for o in juego.jugadores if o.id == casilla.propietario_id), None)
    io.show(f"Paga ${renta:,} de renta al {dueño.nombre if dueño else 'banco'}.")
    audio.play(C.AUDIO_PAGA_RENTA)
    if _ajustar_dinero(j, -renta, juego.tablero):
        if dueño is not None:
            dueño.dinero += renta
    else:
        # bancarrota: el dueño se queda con lo que pueda y las propiedades
        if dueño is not None:
            dueño.dinero += max(0, j.dinero + renta)  # lo que tenía antes del intento
            for slug in j.propiedades:
                juego.tablero.por_slug(slug).propietario_id = dueño.id
            dueño.propiedades.extend(j.propiedades)
            j.propiedades.clear()
        audio.play(C.AUDIO_SIN_DINERO)
        io.show(f"{j.nombre} cae en bancarrota.")


def _enviar_carcel(j: Jugador, tablero: Tablero, audio: AudioPlayer, io: IO) -> None:
    j.posicion = tablero.casilla_carcel()
    j.en_carcel = True
    j.turnos_en_carcel = 0
    audio.play(C.AUDIO_CARCEL)
    io.show(f"{j.nombre} va directo a la cárcel.")
