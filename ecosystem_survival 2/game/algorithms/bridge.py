# Ecosystem Survival - Bridge (puente entre Python y C++)
# Computer Sciences I - Semestre 2026-I
# Equipo 8: Cristian Castañeda, Julian Carvajal, Juan Pablo Angulo
# Julian Carvajal - Algorithm Developer

# Este archivo es el mensajero entre el engine C++ y la UI de Pygame.
# El engine escribe state.json con el estado del juego.
# La UI escribe input.json con la acción del jugador.
# Nosotros leemos y escribimos esos archivos desde aquí.
#
# REGLA NUEVA: input.json ahora también lleva el segmento de pasos
# de migración (máximo 2 casillas) calculado por el backtracking.
# El engine C++ ya no mueve la especie al final de la ruta completa,
# sino solo al final del segmento.
#
# REGLA NUEVA: input.json lleva "fed_this_turn" para que el engine
# sepa qué especies ya comieron y no les permita comer de nuevo.

import json
import os

# Las rutas son relativas a donde está este archivo
BASE_DIR   = os.path.join(os.path.dirname(__file__), "../../data")
INPUT_PATH = os.path.join(BASE_DIR, "input.json")
STATE_PATH = os.path.join(BASE_DIR, "state.json")


def read_state():
    # Leemos el estado actual del juego desde state.json
    # Este archivo lo escribe el engine C++ después de cada acción
    with open(STATE_PATH, "r") as f:
        return json.load(f)


def write_action(action, species_symbol, migration_step=None):
    # Escribimos la acción del jugador en input.json para que el engine la procese.
    # El engine lee este archivo cada vez que lo llamamos desde la UI.
    #
    # action: "feed" o "migrate"
    # species_symbol: símbolo de la especie ("R", "F", "T", "D")
    # migration_step: lista de [row,col] con el segmento de máximo 2 pasos
    #                 Solo se usa cuando action == "migrate"

    payload = {
        "action": action,
        "species": species_symbol
    }

    # Si es una migración, incluimos el segmento de pasos calculado por backtracking
    # El engine mueve la especie a la última posición de este segmento
    if action == "migrate" and migration_step is not None:
        payload["migration_path"] = migration_step

    with open(INPUT_PATH, "w") as f:
        json.dump(payload, f, indent=2)


def state_exists():
    # Verificamos si el archivo de estado ya existe
    # Útil para saber si el engine ya generó el estado inicial
    return os.path.isfile(STATE_PATH)


# --- Funciones de acceso rápido al estado ---
# Estas las usa Juan en la UI para no tener que acceder al dict directamente

def get_board(state):
    # Retorna el tablero como lista 2D de strings
    return state.get("board", [])


def get_species_list(state):
    # Retorna la lista de todas las especies con sus datos
    return state.get("species", [])


def get_turn(state):
    # Retorna el número de turno actual
    return state.get("turn", 0)


def get_actions_left(state):
    # Retorna cuántas acciones quedan en el turno actual (0, 1 o 2)
    return state.get("actions_left", 0)


def get_game_status(state):
    # Retorna el estado del juego: "running", "won" o "lost"
    return state.get("game_status", "unknown")


def get_greedy_recommendation(state):
    # Retorna el símbolo de la especie recomendada por el greedy
    # Este campo lo puede llenar Python antes de pasarle el state a Juan
    return state.get("greedy_recommendation", None)


def get_migration_path(state):
    # Retorna el path de migración guardado en el estado
    # Puede estar vacío si no hay migración en curso
    return state.get("migration_path", [])


def was_fed(state, symbol):
    # Revisamos si una especie ya fue alimentada en el turno actual.
    # Buscamos la especie por símbolo y leemos su campo "fed_this_turn".
    for sp in state.get("species", []):
        if sp["symbol"] == symbol:
            return sp.get("fed_this_turn", False)
    return False
