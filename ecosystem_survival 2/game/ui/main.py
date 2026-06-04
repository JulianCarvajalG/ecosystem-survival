"""
Ecosystem Survival - Graphical User Interface (GUI)
Esta interfaz gráfica fue desarrollada utilizando Pygame,funciona 
como el cliente visual del proyecto. Su labor principal es leer el 
estado del ecosistema desde un archivo JSON (state.json) generado por el 
backend en C++ y renderizar una cuadrícula de 8x8 junto con un panel HUD de 
estadísticas en tiempo real.

La interactividad se logra a través del módulo "bridge". La interfaz 
captura los eventos del mouse y teclado del jugador, envía las instrucciones al 
motor mediante un archivo 'input.json', e invoca al binario compilado de C++ 
"game_engine.exe" para calcular el siguiente turno.
"""

# Imports
import pygame
import sys
import subprocess
import os 
import json

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from game import bridge
from game.algorithms import backtracking, greedy
from simulator import (
    ACTIONS_PER_TURN,
    FEED_REDUCTION,
    HUNGER_PER_TURN,
    HUNGER_THRESHOLD,
    construir_estado_inicial,
    efectos_fin_turno,
    procesar_alimentacion,
    procesar_migracion,
    verificar_estado_juego,
)

# Initialization
pygame.init()

# Dimensions
ANCHO_TABLERO = 640
ANCHO_HUD = 260
ANCHO_PANTALLA = ANCHO_TABLERO + ANCHO_HUD
ALTO_PANTALLA = 640
TAMANO_CELDA = ANCHO_TABLERO // 8 

pantalla = pygame.display.set_mode((ANCHO_PANTALLA, ALTO_PANTALLA))
pygame.display.set_caption("Ecosystem Survival")
reloj = pygame.time.Clock()

# Fonts
fuente = pygame.font.SysFont(None, 28)
fuente_pequena = pygame.font.SysFont(None, 22)
fuente_grande = pygame.font.SysFont(None, 70) 

# Colors
COLORES = {
    "[]": (240, 240, 240),
    "R": (139, 69, 19),
    "F": (255, 140, 0),
    "T": (34, 139, 34),
    "D": (160, 110, 70),
    "X": (220, 20, 60),
    "Z": (0, 255, 255)
}

# Images
IMAGENES = {}
nombres_archivos = {
    "R": "conejo.png",
    "F": "zorro.png",
    "T": "tortuga.png",
    "D": "ciervo.png",
    "X": "peligro.png",
    "Z": "zona_segura.png"
}

for simbolo, archivo in nombres_archivos.items():
    ruta = os.path.join(PROJECT_ROOT, "assets", archivo)
    try:
        img = pygame.image.load(ruta).convert_alpha()
        IMAGENES[simbolo] = pygame.transform.scale(img, (TAMANO_CELDA, TAMANO_CELDA))
    except (pygame.error, FileNotFoundError):
        IMAGENES[simbolo] = None

# Variables
especie_seleccionada = None

# Engine
def reiniciar_estado():
    if os.path.exists(bridge.STATE_PATH):
        os.remove(bridge.STATE_PATH)
    if os.path.exists(bridge.INPUT_PATH):
        os.remove(bridge.INPUT_PATH)

    ejecutar_engine()

def ejecutar_engine_python():
    if not bridge.state_exists():
        estado = construir_estado_inicial()
        with open(bridge.STATE_PATH, "w") as f:
            json.dump(estado, f, indent=2)
        return

    if not os.path.exists(bridge.INPUT_PATH):
        return

    with open(bridge.STATE_PATH, "r") as f:
        estado = json.load(f)

    with open(bridge.INPUT_PATH, "r") as f:
        entrada = json.load(f)

    accion = entrada.get("action")
    simbolo = entrada.get("species")
    accion_procesada = False

    if accion == "feed":
        accion_procesada = procesar_alimentacion(estado, simbolo)
    elif accion == "migrate":
        accion_procesada = procesar_migracion(estado, simbolo)

    if accion_procesada:
        estado["actions_left"] -= 1

    if estado["actions_left"] <= 0:
        efectos_fin_turno(estado)
        estado["turn"] += 1
        estado["actions_left"] = ACTIONS_PER_TURN

    estado["game_status"] = verificar_estado_juego(estado)

    with open(bridge.STATE_PATH, "w") as f:
        json.dump(estado, f, indent=2)

def ejecutar_engine():
    try:
        engine_path = os.path.join(PROJECT_ROOT, "engine", "game_engine.exe")
        subprocess.run([engine_path], check=True, cwd=PROJECT_ROOT)
    except FileNotFoundError:
        print("Error: game_engine.exe not found in engine/ folder. Using Python fallback.")
        ejecutar_engine_python()
    except subprocess.CalledProcessError as exc:
        print(f"Error: game_engine.exe failed with code {exc.returncode}. Using Python fallback.")
        ejecutar_engine_python()

# Board
def dibujar_tablero(tablero_datos):
    for fila in range(8):
        for col in range(8):
            simbolo = tablero_datos[fila][col]
            x = col * TAMANO_CELDA
            y = fila * TAMANO_CELDA
            
            pygame.draw.rect(pantalla, COLORES["[]"], (x, y, TAMANO_CELDA, TAMANO_CELDA))

            if simbolo in IMAGENES and IMAGENES[simbolo] is not None:
                pantalla.blit(IMAGENES[simbolo], (x, y))
            else:
                color = COLORES.get(simbolo, (0,0,0))
                if simbolo != "[]": 
                    pygame.draw.rect(pantalla, color, (x, y, TAMANO_CELDA, TAMANO_CELDA))
            
            pygame.draw.rect(pantalla, (100, 100, 100), (x, y, TAMANO_CELDA, TAMANO_CELDA), 1)
            
            if simbolo == especie_seleccionada and simbolo in ["R", "F", "T", "D"]:
                pygame.draw.rect(pantalla, (255, 0, 0), (x, y, TAMANO_CELDA, TAMANO_CELDA), 3)

def obtener_rutas_backtracking(estado, simbolo):
    if not estado or not simbolo:
        return [], []

    ruta_completa = backtracking.get_migration_path(simbolo, estado)
    siguiente = backtracking.get_next_steps(ruta_completa)
    return ruta_completa, siguiente

def dibujar_ruta_backtracking(ruta_completa, siguiente):
    if not ruta_completa:
        return

    siguiente_set = {tuple(paso) for paso in siguiente}

    for indice, (fila, col) in enumerate(ruta_completa):
        centro_x = col * TAMANO_CELDA + TAMANO_CELDA // 2
        centro_y = fila * TAMANO_CELDA + TAMANO_CELDA // 2

        if indice > 0:
            fila_ant, col_ant = ruta_completa[indice - 1]
            centro_ant = (
                col_ant * TAMANO_CELDA + TAMANO_CELDA // 2,
                fila_ant * TAMANO_CELDA + TAMANO_CELDA // 2
            )
            pygame.draw.line(pantalla, (0, 120, 255), centro_ant, (centro_x, centro_y), 5)

        color = (255, 230, 0) if (fila, col) in siguiente_set else (0, 120, 255)
        pygame.draw.circle(pantalla, color, (centro_x, centro_y), 9)
        pygame.draw.circle(pantalla, (20, 20, 20), (centro_x, centro_y), 9, 2)

def formatear_ruta(ruta):
    return " -> ".join(f"[{fila},{col}]" for fila, col in ruta)

def dibujar_texto_envuelto(texto, x, y, ancho, color=(230, 230, 230), fuente_texto=None, alto_linea=22):
    fuente_texto = fuente_texto or fuente_pequena
    palabras = texto.split(" ")
    linea = ""

    for palabra in palabras:
        prueba = palabra if not linea else f"{linea} {palabra}"
        if fuente_texto.size(prueba)[0] <= ancho:
            linea = prueba
        else:
            if linea:
                pantalla.blit(fuente_texto.render(linea, True, color), (x, y))
                y += alto_linea
            linea = palabra

    if linea:
        pantalla.blit(fuente_texto.render(linea, True, color), (x, y))
        y += alto_linea

    return y

# HUD
def dibujar_hud(estado, ruta_completa=None, siguiente=None):
    pygame.draw.rect(pantalla, (40, 40, 40), (ANCHO_TABLERO, 0, ANCHO_HUD, ALTO_PANTALLA))
    
    turno = bridge.get_turn(estado)
    acciones = bridge.get_actions_left(estado)
    
    pantalla.blit(fuente.render(f"Current Turn: {turno}", True, (255, 255, 255)), (ANCHO_TABLERO + 20, 20))
    pantalla.blit(fuente.render(f"Actions: {acciones}", True, (255, 255, 255)), (ANCHO_TABLERO + 20, 60))

    recomendado = greedy.get_recommendation(estado)
    if recomendado:
        texto_greedy = fuente.render(f"Suggestion: Attend {recomendado}", True, (255, 255, 0))
        pantalla.blit(texto_greedy, (ANCHO_TABLERO + 20, 100))

    especies = bridge.get_species_list(estado)
    y_offset = 135 
    
    for sp in especies:
        alerta_hambre = " !" if sp["status"] == "active" and sp["hunger"] >= HUNGER_THRESHOLD else ""
        info = f"{sp['name']}: Pop {sp['population']} | Hun {sp['hunger']}{alerta_hambre}"
        color_texto = (255, 90, 90) if alerta_hambre else COLORES.get(sp['symbol'], (255, 255, 255)) 
        pantalla.blit(fuente.render(info, True, color_texto), (ANCHO_TABLERO + 20, y_offset))
        y_offset += 32

    y_offset += 16
    pantalla.blit(fuente.render("Rules:", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset))
    pantalla.blit(fuente_pequena.render(f"Feed: -{FEED_REDUCTION} hunger", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 28))
    pantalla.blit(fuente_pequena.render(f"Turn: +{HUNGER_PER_TURN} hunger", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 52))
    pantalla.blit(fuente_pequena.render(f"Pop loss: hunger >= {HUNGER_THRESHOLD}", True, (255, 170, 170)), (ANCHO_TABLERO + 20, y_offset + 76))

    y_offset += 92
    pantalla.blit(fuente.render("Controls:", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset))
    pantalla.blit(fuente_pequena.render("Click: Select", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 28))
    pantalla.blit(fuente_pequena.render(f"'A': Feed (-{FEED_REDUCTION})", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 52))
    pantalla.blit(fuente_pequena.render("'M': Migrate", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 76))
    pantalla.blit(fuente_pequena.render("'R': Reset", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 100))

    y_offset += 124
    pantalla.blit(fuente.render("Backtracking:", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset))
    y_offset += 28

    if especie_seleccionada:
        if ruta_completa:
            texto_ruta = f"{especie_seleccionada} full path ({len(ruta_completa)}): {formatear_ruta(ruta_completa)}"
            texto_siguiente = f"Next move ({max(0, len(siguiente) - 1)}): {formatear_ruta(siguiente)}"
            y_offset = dibujar_texto_envuelto(texto_ruta, ANCHO_TABLERO + 20, y_offset, ANCHO_HUD - 35, (120, 190, 255))
            y_offset = dibujar_texto_envuelto(texto_siguiente, ANCHO_TABLERO + 20, y_offset + 6, ANCHO_HUD - 35, (255, 230, 0))
        else:
            pantalla.blit(fuente_pequena.render(f"{especie_seleccionada}: no path available", True, (255, 180, 180)), (ANCHO_TABLERO + 20, y_offset))
    else:
        pantalla.blit(fuente_pequena.render("Select a species to preview", True, (180, 180, 180)), (ANCHO_TABLERO + 20, y_offset))

# Startup
if not bridge.state_exists():
    ejecutar_engine()

# Loop
corriendo = True
while corriendo:
    
    estado_actual = {}
    estado_juego = "running"
    
    if bridge.state_exists():
        estado_actual = bridge.read_state()
        matriz_tablero = bridge.get_board(estado_actual)
        estado_juego = bridge.get_game_status(estado_actual)
    else:
        matriz_tablero = [["[]" for _ in range(8)] for _ in range(8)]
    
    rect_boton_reiniciar = pygame.Rect(ANCHO_TABLERO // 2 - 110, ALTO_PANTALLA // 2 + 30, 220, 50)

    # Events
    for evento in pygame.event.get():
        if evento.type == pygame.QUIT:
            corriendo = False
            
        elif evento.type == pygame.MOUSEBUTTONDOWN:
            x_mouse, y_mouse = evento.pos
            
            # Restart
            if estado_juego in ["lost", "won"]:
                if rect_boton_reiniciar.collidepoint(x_mouse, y_mouse):
                    especie_seleccionada = None
                    reiniciar_estado() 
            
            # Selection
            elif estado_juego == "running" and x_mouse < ANCHO_TABLERO:
                col = x_mouse // TAMANO_CELDA
                fila = y_mouse // TAMANO_CELDA
                simbolo_click = matriz_tablero[fila][col]
                
                if simbolo_click in ["R", "F", "T", "D"]:
                    especie_seleccionada = simbolo_click

        # Keyboard
        elif evento.type == pygame.KEYDOWN and estado_juego == "running":
            if evento.key == pygame.K_r:
                especie_seleccionada = None
                reiniciar_estado()

            if especie_seleccionada:
                if evento.key == pygame.K_a:
                    bridge.write_action("feed", especie_seleccionada)
                    ejecutar_engine()
                    especie_seleccionada = None
                    
                elif evento.key == pygame.K_m:
                    pasos = backtracking.get_migration_step(especie_seleccionada, estado_actual)
                    bridge.write_action("migrate", especie_seleccionada, pasos)
                    ejecutar_engine()
                    especie_seleccionada = None

    # Render
    pantalla.fill((255, 255, 255)) 
    dibujar_tablero(matriz_tablero)

    ruta_completa = []
    siguiente = []
    if estado_actual and especie_seleccionada and estado_juego == "running":
        ruta_completa, siguiente = obtener_rutas_backtracking(estado_actual, especie_seleccionada)
        dibujar_ruta_backtracking(ruta_completa, siguiente)
    
    if estado_actual:
        dibujar_hud(estado_actual, ruta_completa, siguiente)
        
    # Ending
    if estado_juego in ["lost", "won"]:
        if estado_juego == "lost":
            texto_fin = fuente_grande.render("GAME OVER!", True, (255, 0, 0))
        else:
            texto_fin = fuente_grande.render("VICTORY!", True, (0, 255, 0))
            
        rect_texto = texto_fin.get_rect(center=(ANCHO_TABLERO // 2, ALTO_PANTALLA // 2 - 30))
        pantalla.blit(texto_fin, rect_texto)
        
        pygame.draw.rect(pantalla, (50, 150, 50), rect_boton_reiniciar) 
        pygame.draw.rect(pantalla, (255, 255, 255), rect_boton_reiniciar, 2) 
        
        texto_boton = fuente.render("Play Again", True, (255, 255, 255))
        rect_texto_boton = texto_boton.get_rect(center=rect_boton_reiniciar.center)
        pantalla.blit(texto_boton, rect_texto_boton)
    
    # Display
    pygame.display.flip()
    reloj.tick(30)

# Quit
pygame.quit()
sys.exit()
