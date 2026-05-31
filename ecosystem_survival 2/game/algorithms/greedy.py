# Ecosystem Survival - Algoritmo Greedy
# Computer Sciences I - Semestre 2026-I
# Equipo 8: Cristian Castañeda, Julian Carvajal, Juan Pablo Angulo
# Julian Carvajal - Algorithm Developer

# Este archivo implementa el algoritmo greedy que recomienda al jugador
# qué especie debe atender primero en cada turno.
# La idea es simple: calculamos un valor de riesgo para cada especie
# y le sugerimos la que esté peor. El jugador puede ignorar la sugerencia,
# pero generalmente tiene sentido seguirla.

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/state.json")


def load_state(path=DATA_PATH):
    # Cargamos el estado actual del juego desde el archivo JSON
    # que genera el engine de Cristian
    with open(path, "r") as f:
        return json.load(f)


def compute_risk(species):
    # Calculamos el riesgo de una especie usando la fórmula del enunciado:
    # riesgo = hambre + (10 - población)
    #
    # Una especie con mucha hambre tiene riesgo alto.
    # Una especie con poca población también tiene riesgo alto.
    # Esto hace que el algoritmo priorice los casos más críticos primero.
    return species["hunger"] + (10 - species["population"])


def already_fed_this_turn(species):
    # Revisamos si esta especie ya fue alimentada en el turno actual.
    # El campo "fed_this_turn" lo maneja el engine C++ y viene en el JSON.
    # Si no existe el campo, asumimos que no fue alimentada todavía.
    return species.get("fed_this_turn", False)


def greedy_recommend(species_list):
    # Recorremos todas las especies para encontrar cuál está en mayor riesgo.
    # Solo consideramos especies activas que todavía se puedan alimentar.
    # Las que ya están safe o extintas no las evaluamos.
    # Las que ya fueron alimentadas este turno tampoco las recomendamos para comer.
    #
    # Retorna el diccionario completo de la especie con mayor riesgo,
    # o None si no hay ninguna especie que necesite atención.
    best = None
    highest_risk = -1

    for sp in species_list:
        # Si ya está segura o extinta, no tiene sentido recomendarla
        if sp["status"] in ("safe", "extinct"):
            continue

        risk = compute_risk(sp)

        # Actualizamos el máximo si encontramos una especie en peor estado
        if risk > highest_risk:
            highest_risk = risk
            best = sp

    return best


def greedy_recommend_feed(species_list):
    # Esta función es igual al greedy normal pero excluye las especies
    # que ya fueron alimentadas en el turno actual.
    # Sirve para que la recomendación de alimentación sea válida
    # y no sugiera algo que el jugador no puede hacer.
    best = None
    highest_risk = -1

    for sp in species_list:
        if sp["status"] in ("safe", "extinct"):
            continue

        # Esta validación evita que una especie se alimente dos veces en el mismo turno
        if already_fed_this_turn(sp):
            continue

        risk = compute_risk(sp)

        if risk > highest_risk:
            highest_risk = risk
            best = sp

    return best


def get_recommendation(state=None):
    # Punto de entrada principal que usa Juan desde la UI.
    # Si no le pasamos el estado, lo leemos del archivo.
    # Retorna el símbolo de la especie recomendada (ej: "R") o None.
    if state is None:
        state = load_state()

    species_list = state.get("species", [])
    recommended = greedy_recommend(species_list)

    if recommended is None:
        return None

    return recommended["symbol"]


def get_feed_recommendation(state=None):
    # Igual que get_recommendation pero solo para sugerir alimentación.
    # No recomienda especies que ya comieron este turno.
    # Juan puede mostrar esta en el HUD cuando el jugador quiere alimentar.
    if state is None:
        state = load_state()

    species_list = state.get("species", [])
    recommended = greedy_recommend_feed(species_list)

    if recommended is None:
        return None

    return recommended["symbol"]


if __name__ == "__main__":
    state = load_state()
    print(f"Recomendacion general: {get_recommendation(state)}")
    print(f"Recomendacion para alimentar: {get_feed_recommendation(state)}")
