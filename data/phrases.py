"""
Frases del juego Turista Mundial Azteca.

Cada entrada es: (slug, voz, texto)
- slug: nombre de archivo sin extensión, se guarda como ~/turista/audio/<slug>.mp3
- voz: clave en VOICES
- texto: lo que dirá edge-tts

Convención de voces:
- NARRADORA (Dalia, femenina es-MX): narración general, anuncios de turno, llegadas a estados, números, instrucciones.
- EVENTOS (Jorge, masculina es-MX): eventos especiales con peso narrativo — cárcel, multas, cartas, victoria.
"""

VOICES = {
    "narradora": "es-MX-DaliaNeural",
    "eventos":   "es-MX-JorgeNeural",
}

# --- Bienvenida y cierre ---
BIENVENIDA = [
    ("bienvenida",         "narradora", "Bienvenidos a Turista Mundial Azteca. Recorran los treinta y dos estados de México y conviértanse en el mejor turista."),
    ("instrucciones",      "narradora", "Cada jugador en su turno tirará los dados, avanzará en el tablero y aprenderá sobre el estado al que llegue. Gana quien termine con más dinero al recorrer todo el país."),
    ("inicio_partida",     "narradora", "Comienza la partida. Mucha suerte."),
    ("fin_juego",          "eventos",   "El juego ha terminado."),
    ("gana_jugador_1",     "eventos",   "Felicidades, jugador uno. Eres el mejor turista de México."),
    ("gana_jugador_2",     "eventos",   "Felicidades, jugador dos. Eres el mejor turista de México."),
    ("empate",             "eventos",   "Empate. Los dos jugadores conocen México como ningún otro."),
]

# --- Turnos y mecánica ---
TURNOS = [
    ("turno_jugador_1",    "narradora", "Es el turno del jugador uno."),
    ("turno_jugador_2",    "narradora", "Es el turno del jugador dos."),
    ("tira_dados",         "narradora", "Tira los dados."),
    ("pierdes_turno",      "narradora", "Pierdes el turno."),
    ("avanza_otra_vez",    "narradora", "Sacaste par. Tira otra vez."),
]

# Números 2-12 para el resultado de dos dados
DADOS = [
    ("dado_2",  "narradora", "Sacaste un dos."),
    ("dado_3",  "narradora", "Sacaste un tres."),
    ("dado_4",  "narradora", "Sacaste un cuatro."),
    ("dado_5",  "narradora", "Sacaste un cinco."),
    ("dado_6",  "narradora", "Sacaste un seis."),
    ("dado_7",  "narradora", "Sacaste un siete."),
    ("dado_8",  "narradora", "Sacaste un ocho."),
    ("dado_9",  "narradora", "Sacaste un nueve."),
    ("dado_10", "narradora", "Sacaste un diez."),
    ("dado_11", "narradora", "Sacaste un once."),
    ("dado_12", "narradora", "Sacaste un doce."),
]

# --- Eventos / cartas / multas ---
EVENTOS = [
    ("evento_carta",       "eventos",   "Saca una tarjeta de fortuna."),
    ("evento_paga_renta",  "eventos",   "Esta propiedad ya tiene dueño. Paga la renta."),
    ("evento_compra",      "eventos",   "Puedes comprar esta propiedad."),
    ("evento_carcel",      "eventos",   "Vas directo a la cárcel. No pases por la salida."),
    ("evento_libre",       "eventos",   "Sales libre de la cárcel."),
    ("evento_multa",       "eventos",   "Recibiste una multa. Paga al banco."),
    ("evento_premio",      "eventos",   "¡Ganaste un premio! El banco te paga."),
    ("evento_pasa_salida", "narradora", "Pasaste por la salida. Cobra dos mil pesos."),
    ("evento_sin_dinero",  "eventos",   "Te quedaste sin dinero. Quedas eliminado de la partida."),
]

# --- Estados ---
# Cada entrada: (slug, voz, texto)
# Para el formato final con precio, llenar texto como:
#   "Llegaste a Aguascalientes. Capital: Aguascalientes. Paga ___ pesos de hospedaje."
# Mientras se definen los precios, dejamos un placeholder PRECIO=None y el texto provisional.
#
# Lista oficial de los 32 estados (31 + CDMX).
ESTADOS_META = [
    # (slug,                   nombre,                 capital)
    ("ags",  "Aguascalientes",       "Aguascalientes"),
    ("bc",   "Baja California",      "Mexicali"),
    ("bcs",  "Baja California Sur",  "La Paz"),
    ("camp", "Campeche",             "Campeche"),
    ("chis", "Chiapas",              "Tuxtla Gutiérrez"),
    ("chih", "Chihuahua",            "Chihuahua"),
    ("cdmx", "Ciudad de México",     "Ciudad de México"),
    ("coah", "Coahuila",             "Saltillo"),
    ("col",  "Colima",               "Colima"),
    ("dgo",  "Durango",              "Durango"),
    ("gto",  "Guanajuato",           "Guanajuato"),
    ("gro",  "Guerrero",             "Chilpancingo"),
    ("hgo",  "Hidalgo",              "Pachuca"),
    ("jal",  "Jalisco",              "Guadalajara"),
    ("mex",  "Estado de México",     "Toluca"),
    ("mich", "Michoacán",            "Morelia"),
    ("mor",  "Morelos",              "Cuernavaca"),
    ("nay",  "Nayarit",              "Tepic"),
    ("nl",   "Nuevo León",           "Monterrey"),
    ("oax",  "Oaxaca",               "Oaxaca de Juárez"),
    ("pue",  "Puebla",               "Puebla"),
    ("qro",  "Querétaro",            "Querétaro"),
    ("qroo", "Quintana Roo",         "Chetumal"),
    ("slp",  "San Luis Potosí",      "San Luis Potosí"),
    ("sin",  "Sinaloa",              "Culiacán"),
    ("son",  "Sonora",               "Hermosillo"),
    ("tab",  "Tabasco",              "Villahermosa"),
    ("tamps","Tamaulipas",           "Ciudad Victoria"),
    ("tlax", "Tlaxcala",             "Tlaxcala"),
    ("ver",  "Veracruz",             "Xalapa"),
    ("yuc",  "Yucatán",              "Mérida"),
    ("zac",  "Zacatecas",            "Zacatecas"),
]

# Precios de hospedaje por estado (en pesos del juego).
# Tiers definidos con el usuario en sesión inicial:
#   Premium       $5000 — 4 estados
#   Turístico alto $3500 — 6 estados
#   Medio-alto    $2500 — 8 estados
#   Medio         $1500 — 8 estados
#   Bajo          $1000 — 6 estados
PRECIOS_HOSPEDAJE = {
    # Premium
    "cdmx": 5000, "nl": 5000, "jal": 5000, "qroo": 5000,
    # Turístico alto
    "yuc": 3500, "bcs": 3500, "oax": 3500, "mex": 3500, "pue": 3500, "gto": 3500,
    # Medio-alto
    "qro": 2500, "ver": 2500, "chih": 2500, "son": 2500,
    "sin": 2500, "mich": 2500, "mor": 2500, "bc": 2500,
    # Medio
    "hgo": 1500, "slp": 1500, "coah": 1500, "tamps": 1500,
    "ags": 1500, "tab": 1500, "chis": 1500, "nay": 1500,
    # Bajo
    "camp": 1000, "col": 1000, "dgo": 1000, "zac": 1000, "tlax": 1000, "gro": 1000,
}

def estado_texto(nombre: str, capital: str, precio: int | None) -> str:
    if precio is None:
        return f"Llegaste a {nombre}. Capital: {capital}."
    return f"Llegaste a {nombre}. Capital: {capital}. Paga {precio} pesos de hospedaje."

ESTADOS = [
    (f"estado_{slug}", "narradora", estado_texto(nombre, capital, PRECIOS_HOSPEDAJE.get(slug)))
    for slug, nombre, capital in ESTADOS_META
]

# Lista completa que el generador consume
ALL_PHRASES = BIENVENIDA + TURNOS + DADOS + EVENTOS + ESTADOS
