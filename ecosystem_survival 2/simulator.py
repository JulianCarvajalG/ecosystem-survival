# Ecosystem Survival - Simulador de consola
# Computer Sciences I - Semestre 2026-I
# Equipo 8: Cristian Castañeda, Julian Carvajal, Juan Pablo Angulo
#
# Este simulador corre el juego completo en la terminal sin necesitar
# Pygame ni el engine C++. Es ideal para verificar que los algoritmos
# funcionan correctamente antes de integrar todo.
#
# Refleja exactamente la misma lógica que el engine C++, incluyendo
# las reglas nuevas de alimentación y migración por pasos.
#
# Cómo usarlo:
#   python simulator.py
#
# Comandos disponibles:
#   feed R     -> alimenta al conejo (si no comió ya este turno)
#   migrate F  -> mueve al zorro máximo 2 casillas hacia zona segura
#   ruta T     -> muestra la ruta completa de la tortuga sin moverla
#   skip       -> terminar el turno sin gastar más acciones
#   quit       -> salir del juego

import os
import sys

# Importamos los algoritmos de Julian desde su carpeta
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "game/algorithms"))

from greedy import get_recommendation, get_feed_recommendation, compute_risk
from backtracking import get_migration_path, get_next_steps


# --- Estado inicial del juego ---

def construir_estado_inicial():
    # Este estado tiene que coincidir exactamente con el que genera el engine C++
    # fed_this_turn arranca en False para todas las especies
    return {
        "grid_size": 8,
        "turn": 1,
        "actions_left": 2,
        "board": [
            ["[]", "R",  "[]", "[]", "[]", "X",  "[]", "[]"],
            ["[]", "[]", "X",  "[]", "[]", "[]", "[]", "[]"],
            ["[]", "[]", "[]", "[]", "F",  "[]", "[]", "[]"],
            ["[]", "X",  "[]", "[]", "[]", "[]", "[]", "[]"],
            ["[]", "[]", "[]", "[]", "[]", "[]", "T",  "[]"],
            ["[]", "[]", "[]", "[]", "X",  "[]", "[]", "[]"],
            ["[]", "[]", "C",  "[]", "[]", "[]", "[]", "[]"],
            ["Z",  "Z",  "[]", "[]", "[]", "[]", "[]", "[]"]
        ],
        "species": [
            {"symbol": "R", "name": "Rabbit", "population": 3, "hunger": 3,
             "position": [0, 1], "status": "active", "fed_this_turn": False},
            {"symbol": "F", "name": "Fox",    "population": 3, "hunger": 2,
             "position": [2, 4], "status": "active", "fed_this_turn": False},
            {"symbol": "T", "name": "Turtle", "population": 3, "hunger": 1,
             "position": [4, 6], "status": "active", "fed_this_turn": False},
        ],
        "greedy_recommendation": "",
        "migration_path": [],
        "game_status": "running"
    }


# --- Constantes de juego (iguales al engine C++) ---

FEED_REDUCTION   = 2
FOOD_CELL_BONUS  = 2
HUNGER_THRESHOLD = 3
HUNGER_PER_TURN  = 1
ACTIONS_PER_TURN = 2


# --- Funciones de búsqueda en el estado ---

def buscar_especie(state, simbolo):
    # Buscamos una especie por su símbolo en la lista de especies del estado
    for sp in state["species"]:
        if sp["symbol"] == simbolo:
            return sp
    return None


# --- Renderizado del tablero ---

# Así se ve cada celda en la consola
DISPLAY = {
    "[]": "  . ",
    "X":  "  X ",
    "C":  "  C ",
    "Z":  "  Z ",
    "R":  "  R ",
    "F":  "  F ",
    "T":  "  T ",
    "D":  "  D ",
}

def imprimir_tablero(state):
    # Imprimimos el tablero con coordenadas para que sea fácil de leer
    board = state["board"]
    print("\n      " + "    ".join(str(c) for c in range(8)))
    print("    +" + "----+" * 8)
    for r, fila in enumerate(board):
        linea = f"  {r} |"
        for celda in fila:
            linea += DISPLAY.get(celda, f" {celda} ") + "|"
        print(linea)
    print("    +" + "----+" * 8)


def imprimir_estado(state):
    # Mostramos la información de cada especie y la recomendación del greedy
    rec_general = get_recommendation(state)
    rec_comida  = get_feed_recommendation(state)

    print(f"\n  Turno {state['turn']}  |  Acciones restantes: {state['actions_left']}/2")
    print(f"  Recomendacion general: {rec_general}  |  Recomendacion alimentar: {rec_comida}")
    print()

    for sp in state["species"]:
        if sp["status"] == "extinct":
            estado_txt = "[EXTINTA] "
        elif sp["status"] == "safe":
            estado_txt = "[SEGURA]  "
        else:
            riesgo     = compute_risk(sp)
            ya_comio   = " (ya comio)" if sp.get("fed_this_turn") else ""
            estado_txt = f"riesgo={riesgo:>2}{ya_comio}"

        print(f"  {sp['symbol']} {sp['name']:<8} | pop={sp['population']:>2} | "
              f"hambre={sp['hunger']:>2} | {estado_txt} | pos={sp['position']}")


def imprimir_ruta(simbolo, state):
    # Calculamos y mostramos la ruta completa y el próximo segmento de movimiento
    ruta_completa = get_migration_path(simbolo, state)

    if not ruta_completa:
        print(f"  {simbolo}: no hay ruta disponible hacia zona segura")
        return

    siguiente = get_next_steps(ruta_completa)

    pasos_completo  = " -> ".join(f"[{r},{c}]" for r, c in ruta_completa)
    pasos_siguiente = " -> ".join(f"[{r},{c}]" for r, c in siguiente)

    print(f"  {simbolo} ruta completa ({len(ruta_completa)} pasos): {pasos_completo}")
    print(f"  {simbolo} proximo movimiento ({len(siguiente)-1} casillas): {pasos_siguiente}")


# --- Lógica del juego ---

def procesar_alimentacion(state, simbolo):
    # Buscamos la especie y verificamos que se pueda alimentar
    sp = buscar_especie(state, simbolo)

    if sp is None or sp["status"] != "active":
        print(f"  [!] {simbolo} no está disponible para alimentar")
        return False

    # Esta validación evita que una especie se alimente dos veces en el mismo turno
    if sp.get("fed_this_turn", False):
        print(f"  [!] {sp['name']} ya fue alimentada este turno, espera al próximo")
        return False

    # Bajamos el hambre y marcamos que ya comió
    sp["hunger"] = max(0, sp["hunger"] - FEED_REDUCTION)
    sp["fed_this_turn"] = True
    print(f"  -> {sp['name']} alimentada. Hambre: {sp['hunger']}")
    return True


def procesar_migracion(state, simbolo):
    # Buscamos la especie y verificamos que se pueda mover
    sp = buscar_especie(state, simbolo)

    if sp is None or sp["status"] != "active":
        print(f"  [!] {simbolo} no está disponible para migrar")
        return False

    # Recalculamos la ruta con el estado ACTUAL del tablero
    # Nunca usamos rutas guardadas porque el tablero puede haber cambiado
    ruta_completa = get_migration_path(simbolo, state)

    if not ruta_completa:
        print(f"  [!] No hay ruta posible para {simbolo}")
        return False

    # Tomamos solo el segmento de máximo 2 casillas para este movimiento
    segmento = get_next_steps(ruta_completa)

    board   = state["board"]
    vieja_r, vieja_c = sp["position"]

    # La especie se mueve a la última posición del segmento
    nueva_r, nueva_c = segmento[-1]

    # Liberamos la celda donde estaba
    board[vieja_r][vieja_c] = "[]"

    # Revisamos si alguna celda del segmento tiene comida
    for paso_r, paso_c in segmento[1:]:   # saltamos la posición inicial
        if board[paso_r][paso_c] == "C":
            sp["hunger"] = max(0, sp["hunger"] - FOOD_CELL_BONUS)
            board[paso_r][paso_c] = "[]"   # la comida se consume
            print(f"  -> {sp['name']} pasó por comida. Hambre: {sp['hunger']}")
            break

    # Actualizamos la posición de la especie
    celda_destino = board[nueva_r][nueva_c]

    if celda_destino == "Z":
        # Si llegó a zona segura, la marcamos y dejamos la Z visible
        sp["status"] = "safe"
        board[nueva_r][nueva_c] = "Z"
        print(f"  -> {sp['name']} llegó a zona segura!")
    else:
        board[nueva_r][nueva_c] = simbolo

    sp["position"] = [nueva_r, nueva_c]

    pasos_movidos = len(segmento) - 1
    print(f"  -> {sp['name']} se movió {pasos_movidos} casilla(s): "
          f"[{vieja_r},{vieja_c}] -> [{nueva_r},{nueva_c}]")
    return True


def efectos_fin_turno(state):
    # Al final del turno, todas las especies activas sufren las consecuencias del tiempo.
    # El hambre sube, y si supera el umbral la población baja.
    # También reiniciamos el estado de alimentación para el próximo turno.
    board = state["board"]
    print("\n  --- Fin del turno ---")

    for sp in state["species"]:
        if sp["status"] != "active":
            continue

        sp["hunger"] += HUNGER_PER_TURN

        if sp["hunger"] >= HUNGER_THRESHOLD:
            sp["population"] -= 1
            print(f"  ! {sp['name']} perdió población por hambre. Pop: {sp['population']}")

        if sp["population"] <= 0:
            sp["population"] = 0
            sp["status"]     = "extinct"
            r, c = sp["position"]
            board[r][c] = "[]"
            print(f"  !! {sp['name']} se extinguió.")

        # Reiniciamos el estado de alimentación cuando termina el día
        sp["fed_this_turn"] = False


def verificar_estado_juego(state):
    # Revisamos si alguien ganó o perdió con el estado actual
    for sp in state["species"]:
        if sp["population"] <= 0 or sp["status"] == "extinct":
            return "lost"

    if all(sp["status"] == "safe" for sp in state["species"]):
        return "won"

    return "running"


# --- Loop principal del simulador ---

def game_loop():
    state = construir_estado_inicial()

    print("=" * 65)
    print("  ECOSYSTEM SURVIVAL - Simulador de consola")
    print("  Comandos: feed R | migrate F | ruta T | skip | quit")
    print("=" * 65)

    while True:
        state["game_status"] = verificar_estado_juego(state)

        if state["game_status"] == "won":
            imprimir_tablero(state)
            print("\n  *** GANASTE - Todas las especies están seguras ***\n")
            break

        if state["game_status"] == "lost":
            imprimir_tablero(state)
            print("\n  *** PERDISTE - Una especie se extinguió ***\n")
            break

        imprimir_tablero(state)
        imprimir_estado(state)

        # Mostramos el próximo movimiento disponible para cada especie activa
        print("\n  Rutas disponibles:")
        for sp in state["species"]:
            if sp["status"] == "active":
                imprimir_ruta(sp["symbol"], state)

        print(f"\n  Acciones restantes: {state['actions_left']}")
        raw = input("  > ").strip().lower()

        if raw == "quit":
            print("  Saliendo.")
            break

        elif raw == "skip":
            # Saltamos directo al fin de turno
            state["actions_left"] = 0

        elif raw.startswith("feed "):
            partes = raw.split()
            if len(partes) == 2:
                simbolo = partes[1].upper()
                ok = procesar_alimentacion(state, simbolo)
                if ok:
                    state["actions_left"] -= 1
            else:
                print("  Uso: feed R")
                continue

        elif raw.startswith("migrate "):
            partes = raw.split()
            if len(partes) == 2:
                simbolo = partes[1].upper()
                ok = procesar_migracion(state, simbolo)
                if ok:
                    state["actions_left"] -= 1
            else:
                print("  Uso: migrate R")
                continue

        elif raw.startswith("ruta "):
            # Solo muestra la ruta, no gasta acción ni mueve nada
            partes = raw.split()
            if len(partes) == 2:
                imprimir_ruta(partes[1].upper(), state)
            continue

        else:
            print("  Comando no reconocido. Usa: feed R | migrate F | ruta T | skip | quit")
            continue

        # Cuando se agotan las acciones del turno, aplicamos efectos y avanzamos
        if state["actions_left"] <= 0:
            efectos_fin_turno(state)
            state["turn"]        += 1
            state["actions_left"] = ACTIONS_PER_TURN
            input("\n  [Enter para continuar al turno siguiente...]")


if __name__ == "__main__":
    game_loop()
