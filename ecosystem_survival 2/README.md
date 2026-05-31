# Ecosystem Survival
**Computer Sciences I — Equipo 8 — Semestre 2026-I**
Universidad Distrital Francisco José de Caldas

Cristian Esteban Castañeda Vargas · Julian Carvajal Garnica · Juan Pablo Angulo Guerrero

---

## Estructura del proyecto

```
project/
├── engine/
│   ├── linked_list.h     # lista enlazada para rutas de migracion
│   ├── tree.h            # AVL tree para datos de especies
│   ├── main.cpp          # engine principal
│   └── json.hpp          # nlohmann/json (ver instrucciones abajo)
├── game/
│   ├── algorithms/
│   │   ├── greedy.py         # algoritmo greedy
│   │   ├── backtracking.py   # algoritmo backtracking
│   │   ├── bridge.py         # I/O JSON entre Python y C++
│   │   └── test_algorithms.py
│   └── ui/
│       └── main.py           # UI Pygame
├── data/
│   ├── state.json        # estado del juego (escrito por C++)
│   └── input.json        # accion del jugador (escrito por Python)
├── simulator.py          # simulador de consola sin UI
└── README.md
```

---

## Setup

### 1. Descargar json.hpp (solo una vez)

```bash
curl -o engine/json.hpp https://raw.githubusercontent.com/nlohmann/json/develop/single_include/nlohmann/json.hpp
```

### 2. Compilar el engine C++

```bash
cd engine
g++ -std=c++17 main.cpp -o game_engine
cd ..
```

### 3. Instalar pygame

```bash
pip install pygame
```

---

## Correr el juego

```bash
# Generar estado inicial
./engine/game_engine

# Arrancar la UI
python game/ui/main.py
```

## Correr el simulador de consola (sin UI, para pruebas)

```bash
python simulator.py
```

Comandos disponibles en el simulador:
- `feed R` — alimenta la especie R
- `migrate F` — migra la especie F a zona segura
- `skip` — saltar turno
- `quit` — salir

---

## Correr los tests de algoritmos

```bash
python game/algorithms/test_algorithms.py
```

---

## Controles en el juego (UI Pygame)

- **Click** sobre una especie → seleccionarla y ver su ruta de migración
- **F** → alimentar especie seleccionada
- **M** → migrar especie seleccionada
- **ESC** → deseleccionar
