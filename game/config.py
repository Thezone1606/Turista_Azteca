"""Parámetros de balance del juego Turista Mundial Azteca."""

DINERO_INICIAL = 30_000          # con qué arranca cada jugador
COBRO_SALIDA = 2_000             # se cobra al pasar/caer en Salida
MULTA_CARCEL = 1_000             # para salir de la cárcel pagando
MULTA_IMPUESTOS = 1_500          # casilla de multa
TURNOS_MAX_EN_CARCEL = 3         # tras N turnos sales obligado
COMPRA_X_HOSPEDAJE = 10          # precio_compra = precio_hospedaje * este factor

NUM_JUGADORES = 2
JUGADORES = [
    {"id": 1, "nombre": "Jugador uno"},
    {"id": 2, "nombre": "Jugador dos"},
]

# Slugs de audio reutilizables (deben existir en audio/<slug>.mp3)
AUDIO_BIENVENIDA = "bienvenida"
AUDIO_INSTRUCCIONES = "instrucciones"
AUDIO_INICIO = "inicio_partida"
AUDIO_FIN = "fin_juego"
AUDIO_GANA = {1: "gana_jugador_1", 2: "gana_jugador_2"}
AUDIO_EMPATE = "empate"
AUDIO_TURNO = {1: "turno_jugador_1", 2: "turno_jugador_2"}
AUDIO_TIRA_DADOS = "tira_dados"
AUDIO_DADO = {n: f"dado_{n}" for n in range(2, 13)}
AUDIO_PASA_SALIDA = "evento_pasa_salida"
AUDIO_CARCEL = "evento_carcel"
AUDIO_SALE_CARCEL = "evento_libre"
AUDIO_MULTA = "evento_multa"
AUDIO_PREMIO = "evento_premio"
AUDIO_CARTA = "evento_carta"
AUDIO_COMPRA = "evento_compra"
AUDIO_PAGA_RENTA = "evento_paga_renta"
AUDIO_SIN_DINERO = "evento_sin_dinero"
AUDIO_PIERDE_TURNO = "pierdes_turno"
AUDIO_PAR = "avanza_otra_vez"

# Casillas especiales
SLUG_SALIDA = "salida"
SLUG_CARCEL = "carcel"
SLUG_IR_CARCEL = "ir_carcel"
SLUG_ESTACIONAMIENTO = "estacionamiento"
SLUG_FORTUNA = "fortuna"
SLUG_MULTA_CASILLA = "multa_casilla"
