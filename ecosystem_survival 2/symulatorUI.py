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
from game.algorithms import bridge, backtracking, greedy

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
fuente_grande = pygame.font.SysFont(None, 70) 

# Colors
COLORES = {
    "[]": (240, 240, 240),
    "R": (139, 69, 19),
    "F": (255, 140, 0),
    "T": (34, 139, 34),
    "X": (220, 20, 60),
    "C": (255, 215, 0),
    "Z": (0, 255, 255)
}

# Images
IMAGENES = {}
nombres_archivos = {
    "R": "conejo.png",
    "F": "zorro.png",
    "T": "tortuga.png",
    "C": "comida.png",
    "X": "peligro.png",
    "Z": "zona_segura.png"
}

for simbolo, archivo in nombres_archivos.items():
    ruta = os.path.join("assets", archivo)
    try:
        img = pygame.image.load(ruta).convert_alpha()
        IMAGENES[simbolo] = pygame.transform.scale(img, (TAMANO_CELDA, TAMANO_CELDA))
    except (pygame.error, FileNotFoundError):
        IMAGENES[simbolo] = None

# Variables
especie_seleccionada = None

# Engine
def ejecutar_engine():
    try:
        subprocess.run(["engine/game_engine.exe"], check=True)
    except FileNotFoundError:
        print("Error: game_engine.exe not found in engine/ folder")

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
            
            if simbolo == especie_seleccionada and simbolo in ["R", "F", "T"]:
                pygame.draw.rect(pantalla, (255, 0, 0), (x, y, TAMANO_CELDA, TAMANO_CELDA), 3)

# HUD
def dibujar_hud(estado):
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
    y_offset = 150 
    
    for sp in especies:
        info = f"{sp['name']}: Pop {sp['population']} | Hun {sp['hunger']}"
        color_texto = COLORES.get(sp['symbol'], (255, 255, 255)) 
        pantalla.blit(fuente.render(info, True, color_texto), (ANCHO_TABLERO + 20, y_offset))
        y_offset += 40

    y_offset += 20
    pantalla.blit(fuente.render("Controls:", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset))
    pantalla.blit(fuente.render("Click: Select", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 30))
    pantalla.blit(fuente.render("'A': Feed", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 60))
    pantalla.blit(fuente.render("'M': Migrate", True, (200, 200, 200)), (ANCHO_TABLERO + 20, y_offset + 90))

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
                    ruta_estado = "data/state.json"
                    ruta_input = "data/input.json"
                    
                    if os.path.exists(ruta_estado):
                        os.remove(ruta_estado)
                    if os.path.exists(ruta_input):
                        os.remove(ruta_input)
                    
                    especie_seleccionada = None
                    ejecutar_engine() 
            
            # Selection
            elif estado_juego == "running" and x_mouse < ANCHO_TABLERO:
                col = x_mouse // TAMANO_CELDA
                fila = y_mouse // TAMANO_CELDA
                simbolo_click = matriz_tablero[fila][col]
                
                if simbolo_click in ["R", "F", "T"]:
                    especie_seleccionada = simbolo_click

        # Keyboard
        elif evento.type == pygame.KEYDOWN and estado_juego == "running":
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
    
    if estado_actual:
        dibujar_hud(estado_actual)
        
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