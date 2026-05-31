# Ecosystem Survival - Algoritmo Backtracking
# Computer Sciences I - Semestre 2026-I
# Equipo 8: Cristian Castañeda, Julian Carvajal, Juan Pablo Angulo
# Julian Carvajal - Algorithm Developer

# Este archivo implementa el backtracking para encontrar rutas de migración.
# La idea es buscar un camino desde donde está la especie hasta una zona segura (Z),
# evitando depredadores (X), otras especies, y celdas ya visitadas en este recorrido.
#
# REGLA NUEVA: la especie NO puede recorrer toda la ruta en un solo movimiento.
# Solo puede avanzar máximo 2 casillas por acción de migración.
# Ejemplo de ruta A->B->C->D->E->Z:
#   Acción 1: A->B->C  (avanza 2)
#   Acción 2: C->D->E  (avanza 2)
#   Acción 3: E->Z     (avanza 1, solo quedaba una)
#
# Las rutas se recalculan SIEMPRE con el estado actual del tablero.
# Nunca reutilizamos una ruta vieja porque el tablero puede haber cambiado.

import json
import os

DATA_PATH = os.path.join(os.path.dirname(__file__), "../../data/state.json")

# Los 8 movimientos posibles: arriba, abajo, izquierda, derecha y las 4 diagonales
DIRECTIONS = [
    (-1, -1), (-1, 0), (-1, 1),
    ( 0, -1),          ( 0, 1),
    ( 1, -1), ( 1, 0), ( 1, 1),
]

# Símbolos de especies para saber cuándo una celda está ocupada por otro animal
SPECIES_SYMBOLS = {"R", "F", "T", "D"}
PREDATOR_CELL   = "X"
SAFE_ZONE       = "Z"

# Máximo de casillas que puede avanzar una especie en una sola acción de migración
MAX_STEPS_PER_ACTION = 2


def load_state(path=DATA_PATH):
    # Leemos el estado actual desde el JSON del engine
    with open(path, "r") as f:
        return json.load(f)


def is_valid_cell(board, row, col, visited, moving_symbol):
    # Revisamos si una celda es válida para moverse a ella.
    # Una celda es válida si:
    # - Está dentro del tablero (no nos salimos de los límites)
    # - No la visitamos antes en este recorrido (evita ciclos infinitos)
    # - No es una zona de peligro (X)
    # - No está ocupada por otra especie diferente a la que se mueve

    filas = len(board)
    cols  = len(board[0]) if board else 0

    # Verificamos que no nos salgamos del tablero
    if row < 0 or row >= filas:
        return False
    if col < 0 or col >= cols:
        return False

    # Si ya pasamos por aquí en este recorrido, no podemos volver
    if visited[row][col]:
        return False

    celda = board[row][col]

    # Los depredadores son intransitables siempre
    if celda == PREDATOR_CELL:
        return False

    # Las otras especies bloquean el paso, pero la propia no
    if celda in SPECIES_SYMBOLS and celda != moving_symbol:
        return False

    return True


def _buscar(board, row, col, visited, path, moving_symbol):
    # Función recursiva que hace el recorrido DFS con backtracking.
    # Explora todas las direcciones posibles desde la celda actual.
    # Si encuentra una zona segura, retorna True y el path queda armado.
    # Si no encuentra salida por este camino, retrocede (backtracking).
    #
    # El "backtracking" ocurre cuando hacemos path.pop() al final:
    # quitamos la última celda del camino y probamos otra dirección.

    # Si llegamos a una zona segura ya encontramos una solución
    if board[row][col] == SAFE_ZONE:
        return True

    # Marcamos esta celda como visitada para no volver a pasar por aquí
    visited[row][col] = True

    for dr, dc in DIRECTIONS:
        nueva_fila = row + dr
        nueva_col  = col + dc

        if is_valid_cell(board, nueva_fila, nueva_col, visited, moving_symbol):
            # Guardamos la posición para seguir construyendo la ruta
            path.append([nueva_fila, nueva_col])

            # Llamada recursiva: seguimos buscando desde la nueva celda
            if _buscar(board, nueva_fila, nueva_col, visited, path, moving_symbol):
                return True

            # Retrocedemos porque este camino no funcionó
            path.pop()

    # Si probamos todas las direcciones y ninguna funcionó, retornamos False
    return False


def find_migration_path(board, start_row, start_col, moving_symbol):
    # Función principal del backtracking.
    # Arma la matriz de visitados y el path inicial, luego inicia la búsqueda.
    #
    # Retorna la ruta COMPLETA desde la posición actual hasta la zona segura,
    # incluyendo la celda de inicio.
    # Si no hay ningún camino posible, retorna lista vacía.
    #
    # IMPORTANTE: esta función siempre trabaja con el tablero actual.
    # Nunca guardamos rutas viejas. Cada vez que el jugador quiere migrar,
    # recalculamos desde cero con el estado real del tablero en ese momento.

    filas   = len(board)
    cols    = len(board[0]) if board else 0

    # La matriz de visitados empieza toda en False
    visited = [[False] * cols for _ in range(filas)]

    # El path empieza con la posición actual de la especie
    path = [[start_row, start_col]]

    if _buscar(board, start_row, start_col, visited, path, moving_symbol):
        return path

    # Si no encontramos ningún camino, avisamos con lista vacía
    return []


def get_next_steps(full_path):
    # Con la regla nueva, la especie solo puede avanzar 2 casillas por acción.
    # Esta función toma la ruta completa y retorna solo el segmento
    # que la especie puede recorrer en esta acción.
    #
    # El segmento incluye la posición actual (índice 0) más las siguientes
    # hasta MAX_STEPS_PER_ACTION casillas.
    #
    # Ejemplo con MAX_STEPS = 2:
    # Ruta completa: [A, B, C, D, E, Z]
    # get_next_steps retorna: [A, B, C]   (posición actual + 2 pasos)
    #
    # En la siguiente llamada, la posición actual ya es C:
    # Ruta nueva (recalculada): [C, D, E, Z]
    # get_next_steps retorna: [C, D, E]

    if not full_path:
        return []

    # Tomamos la posición actual más hasta MAX_STEPS_PER_ACTION pasos adelante
    fin = min(MAX_STEPS_PER_ACTION + 1, len(full_path))
    return full_path[:fin]


def get_migration_path(species_symbol, state=None):
    # Punto de entrada para Julian/Juan.
    # Recibe el símbolo de la especie y el estado actual del juego.
    # Localiza la especie en el JSON, obtiene su posición, y calcula la ruta.
    #
    # Retorna la ruta COMPLETA (no el segmento de 2 pasos).
    # El segmento de pasos lo calcula get_next_steps() por separado
    # para que Juan pueda mostrar toda la ruta en pantalla pero solo
    # mover la especie el pedazo que le toca.

    if state is None:
        state = load_state()

    board = state.get("board", [])

    # Buscamos la posición actual de la especie en la lista del JSON
    # Es más confiable que escanear el tablero celda por celda
    species_list = state.get("species", [])
    start_row, start_col = None, None

    for sp in species_list:
        if sp["symbol"] == species_symbol:
            pos = sp.get("position")
            if pos:
                start_row, start_col = pos[0], pos[1]
            break

    # Si no encontramos la especie, no podemos hacer nada
    if start_row is None:
        return []

    # Calculamos la ruta completa con el tablero actual
    # Esto garantiza que nunca usamos una ruta obsoleta
    return find_migration_path(board, start_row, start_col, species_symbol)


def get_migration_step(species_symbol, state=None):
    # Función de conveniencia que retorna directamente el segmento
    # de máximo 2 pasos que la especie puede recorrer ahora.
    # Internamente recalcula la ruta completa y luego la recorta.
    #
    # Esta es la que debe llamar el engine (y el simulador) cuando
    # el jugador confirma una migración.
    full_path = get_migration_path(species_symbol, state)
    return get_next_steps(full_path)


if __name__ == "__main__":
    state = load_state()
    for sp in state.get("species", []):
        if sp["status"] == "active":
            simbolo   = sp["symbol"]
            ruta      = get_migration_path(simbolo, state)
            siguiente = get_next_steps(ruta)
            print(f"{simbolo} ruta completa ({len(ruta)} pasos): {ruta}")
            print(f"{simbolo} proximo movimiento: {siguiente}\n")
