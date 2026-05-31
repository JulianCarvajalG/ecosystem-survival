// Ecosystem Survival - Engine principal
// Computer Sciences I - Semestre 2026-I
// Equipo 8: Cristian Castañeda, Julian Carvajal, Juan Pablo Angulo
// Cristian Castañeda - Engine Developer
//
// Compila con: g++ -std=c++17 main.cpp -o game_engine
// Requiere json.hpp de nlohmann en la misma carpeta del main.cpp
//
// Este archivo es el cerebro del juego. Lee lo que el jugador quiere hacer
// (input.json), lo procesa, actualiza las estructuras de datos (AVL y lista
// enlazada), y escribe el nuevo estado (state.json) para que Python lo lea.

#include <iostream>
#include <fstream>
#include <string>
#include <vector>
#include "json.hpp"
#include "linked_list.h"
#include "tree.h"

using json = nlohmann::json;

// Rutas relativas al ejecutable. Hay que correr el engine desde la raíz del proyecto.
const std::string STATE_PATH = "data/state.json";
const std::string INPUT_PATH = "data/input.json";

// Constantes del juego. Si el profesor quiere cambiar la dificultad,
// solo hay que tocar estos números.
const int GRID_SIZE        = 8;
const int ACTIONS_PER_TURN = 2;
const int HUNGER_PER_TURN  = 1;   // cuánta hambre sube al final de cada turno
const int FEED_REDUCTION   = 3;   // cuánta hambre baja al alimentar una especie
const int FOOD_CELL_BONUS  = 2;   // cuánta hambre baja si la especie pasa por una C
const int HUNGER_THRESHOLD = 8;   // a partir de aquí la especie empieza a perder población


// --- Funciones auxiliares del tablero ---

// Revisa si una celda es zona segura
bool esCeldaSegura(const std::string& celda) {
    return celda == "Z";
}

// Revisa si una celda tiene comida
bool esCeldaComida(const std::string& celda) {
    return celda == "C";
}

// Pone un valor en una celda del tablero
void setCell(std::vector<std::vector<std::string>>& board, int r, int c, const std::string& val) {
    board[r][c] = val;
}

// Retorna el contenido de una celda
std::string getCell(const std::vector<std::vector<std::string>>& board, int r, int c) {
    return board[r][c];
}


// --- Funciones de I/O JSON ---

// Lee un archivo JSON y retorna su contenido como objeto json.
// Si no puede abrir el archivo, termina el programa con un mensaje de error.
json leerJSON(const std::string& path) {
    std::ifstream f(path);
    if (!f.is_open()) {
        std::cerr << "Error: no se pudo abrir " << path << std::endl;
        exit(1);
    }
    json data;
    f >> data;
    return data;
}

// Escribe un objeto json en un archivo con formato legible (2 espacios de indentación).
void escribirJSON(const std::string& path, const json& data) {
    std::ofstream f(path);
    if (!f.is_open()) {
        std::cerr << "Error: no se pudo escribir en " << path << std::endl;
        exit(1);
    }
    f << data.dump(2);
}

// Revisa si un archivo existe en disco
bool archivoExiste(const std::string& path) {
    std::ifstream f(path);
    return f.good();
}


// --- Estado inicial del juego ---

// Construye el JSON del estado inicial con el tablero base y las 3 especies.
// Este estado solo se genera una vez, la primera vez que corre el engine.
// fed_this_turn empieza en false para todas las especies.
json construirEstadoInicial() {
    json estado;
    estado["grid_size"]    = GRID_SIZE;
    estado["turn"]         = 1;
    estado["actions_left"] = ACTIONS_PER_TURN;

    // Tablero inicial con posiciones fijas para cada especie
    // R=Rabbit, F=Fox, T=Turtle, X=peligro, C=comida, Z=zona segura
    estado["board"] = {
        {"[]", "R",  "[]", "[]", "[]", "[]", "[]", "[]"},
        {"[]", "[]", "X",  "[]", "[]", "[]", "[]", "[]"},
        {"[]", "[]", "[]", "[]", "F",  "[]", "[]", "[]"},
        {"[]", "X",  "[]", "[]", "[]", "[]", "[]", "[]"},
        {"[]", "[]", "[]", "[]", "[]", "[]", "T",  "[]"},
        {"[]", "[]", "[]", "[]", "[]", "[]", "[]", "[]"},
        {"[]", "[]", "C",  "[]", "[]", "[]", "[]", "[]"},
        {"Z",  "Z",  "[]", "[]", "[]", "[]", "[]", "[]"}
    };

    // Datos iniciales de cada especie
    // fed_this_turn empieza en false para todos porque es turno nuevo
    estado["species"] = {
        {{"symbol","R"},{"name","Rabbit"},{"population",5},{"hunger",3},
         {"position",{0,1}},{"status","active"},{"fed_this_turn",false}},
        {{"symbol","F"},{"name","Fox"},{"population",7},{"hunger",2},
         {"position",{2,4}},{"status","active"},{"fed_this_turn",false}},
        {{"symbol","T"},{"name","Turtle"},{"population",9},{"hunger",1},
         {"position",{4,6}},{"status","active"},{"fed_this_turn",false}}
    };

    estado["greedy_recommendation"] = "";
    estado["migration_path"]        = json::array();
    estado["game_status"]           = "running";

    return estado;
}


// --- Carga de especies en el AVL ---

// Toma el estado JSON y carga cada especie en el árbol AVL.
// El AVL es nuestra estructura de datos para buscar y actualizar especies rápido.
// También guarda el campo fed_this_turn en cada nodo.
AVLTree cargarEspeciesEnArbol(const json& estado) {
    AVLTree arbol;

    for (const auto& sp : estado["species"]) {
        arbol.insert(
            sp["symbol"].get<std::string>(),
            sp["name"].get<std::string>(),
            sp["population"].get<int>(),
            sp["hunger"].get<int>(),
            sp["position"][0].get<int>(),
            sp["position"][1].get<int>()
        );

        // El insert no maneja status ni fed_this_turn, así que los seteamos aparte
        AVLNode* nodo = arbol.search(sp["symbol"].get<std::string>());
        if (nodo) {
            nodo->status       = sp["status"].get<std::string>();
            nodo->fedThisTurn  = sp.value("fed_this_turn", false);
        }
    }

    return arbol;
}


// --- Verificación del estado del juego ---

// Revisa si alguien ganó o perdió.
// Ganan cuando todas las especies no extintas están en zona segura.
// Pierden si cualquier especie llega a población 0.
std::string verificarEstadoJuego(AVLTree& arbol) {
    auto especies = arbol.getAllSpecies();
    int totalActivas = 0;
    int totalSeguras = 0;

    for (auto* sp : especies) {
        if (sp->status == "extinct") continue;

        // Si alguna especie activa llega a población 0, perdemos inmediatamente
        if (sp->population <= 0) return "lost";

        totalActivas++;
        if (sp->status == "safe") totalSeguras++;
    }

    // Si todas las no extintas están seguras, ganamos
    if (totalActivas > 0 && totalSeguras == totalActivas) return "won";

    return "running";
}


// --- Efectos de fin de turno ---

// Al terminar el turno, todas las especies activas sufren los efectos del tiempo:
// - El hambre sube en 1
// - Si el hambre supera el umbral, baja la población
// - Si la población llega a 0, la especie se extingue y desaparece del tablero
//
// También reiniciamos fed_this_turn para todas las especies porque empieza un turno nuevo.
void efectosFinDeTurno(AVLTree& arbol, std::vector<std::vector<std::string>>& board) {
    auto especies = arbol.getAllSpecies();

    for (auto* sp : especies) {
        if (sp->status != "active") continue;

        // El hambre siempre sube, sin importar qué hizo el jugador este turno
        sp->hunger += HUNGER_PER_TURN;

        // Si tiene demasiada hambre, empieza a perder individuos de la población
        if (sp->hunger >= HUNGER_THRESHOLD) {
            sp->population -= 1;
        }

        // Si la población llega a cero, la especie se extingue y sale del tablero
        if (sp->population <= 0) {
            sp->population = 0;
            sp->status     = "extinct";
            setCell(board, sp->row, sp->col, "[]");
        }

        // Reiniciamos el estado de alimentación cuando termina el día
        // Para el próximo turno, todas las especies pueden comer de nuevo
        sp->fedThisTurn = false;
    }
}


// --- Serialización del estado ---

// Convierte el AVL y el tablero a formato JSON para escribir en state.json.
// Python lee este archivo para mostrar la UI y calcular los algoritmos.
json serializarEstado(AVLTree& arbol,
                      const std::vector<std::vector<std::string>>& board,
                      int turno, int accionesRestantes,
                      const std::string& estadoJuego) {
    json estado;
    estado["grid_size"]    = GRID_SIZE;
    estado["turn"]         = turno;
    estado["actions_left"] = accionesRestantes;

    // Serializar el tablero fila por fila
    json boardJson = json::array();
    for (const auto& fila : board) {
        json filaJson = json::array();
        for (const auto& celda : fila) filaJson.push_back(celda);
        boardJson.push_back(filaJson);
    }
    estado["board"] = boardJson;

    // Serializar las especies desde el AVL en orden (inorder da orden alfabético por símbolo)
    json especiesJson = json::array();
    for (auto* sp : arbol.getAllSpecies()) {
        especiesJson.push_back({
            {"symbol",        sp->symbol},
            {"name",          sp->name},
            {"population",    sp->population},
            {"hunger",        sp->hunger},
            {"position",      {sp->row, sp->col}},
            {"status",        sp->status},
            {"fed_this_turn", sp->fedThisTurn}   // Python necesita saber esto
        });
    }
    estado["species"] = especiesJson;

    // Python calcula el greedy y el path, el engine los deja vacíos
    estado["greedy_recommendation"] = "";
    estado["migration_path"]        = json::array();
    estado["game_status"]           = estadoJuego;

    return estado;
}


// --- Procesamiento de acciones ---

// Esta función recibe la acción del jugador y actualiza las estructuras de datos.
// Si la acción es "feed", baja el hambre. Pero solo si la especie no ha comido hoy.
// Si la acción es "migrate", mueve la especie al final del segmento de pasos recibido.
//
// El segmento de pasos viene de Python (backtracking) y tiene máximo 2 casillas.
// El engine no calcula rutas, solo aplica el movimiento que Python ya calculó.
void procesarAccion(const std::string& accion, const std::string& simbolo,
                    AVLTree& arbol,
                    std::vector<std::vector<std::string>>& board,
                    const json& segmentoPasos) {

    AVLNode* sp = arbol.search(simbolo);

    // Si la especie no existe o no está activa, no hacemos nada
    if (sp == nullptr || sp->status != "active") {
        std::cerr << "Especie no encontrada o no activa: " << simbolo << std::endl;
        return;
    }

    if (accion == "feed") {
        // Esta validación evita que una especie se alimente dos veces en el mismo turno
        if (sp->fedThisTurn) {
            std::cerr << simbolo << " ya fue alimentada este turno." << std::endl;
            return;
        }

        sp->hunger -= FEED_REDUCTION;
        if (sp->hunger < 0) sp->hunger = 0;

        // Marcamos que ya comió para que no pueda comer de nuevo este turno
        sp->fedThisTurn = true;

    } else if (accion == "migrate") {
        // Si no nos mandaron un segmento de ruta, no podemos mover nada
        if (segmentoPasos.empty()) {
            std::cerr << "No hay segmento de migración para " << simbolo << std::endl;
            return;
        }

        // Limpiamos la celda donde estaba la especie
        setCell(board, sp->row, sp->col, "[]");

        // La especie se mueve a la ÚLTIMA posición del segmento recibido
        // (que es máximo la posición actual + 2 casillas)
        auto ultimoPaso = segmentoPasos.back();
        int nuevaFila   = ultimoPaso[0].get<int>();
        int nuevaCol    = ultimoPaso[1].get<int>();

        std::string celdaDestino = getCell(board, nuevaFila, nuevaCol);

        // Si pasa por comida, se beneficia aunque no sea el destino final
        // Nota: con el segmento de 2 pasos, revisamos si alguna celda intermedia tiene C
        for (const auto& paso : segmentoPasos) {
            int pr = paso[0].get<int>();
            int pc = paso[1].get<int>();
            if (esCeldaComida(getCell(board, pr, pc))) {
                sp->hunger -= FOOD_CELL_BONUS;
                if (sp->hunger < 0) sp->hunger = 0;
                setCell(board, pr, pc, "[]");   // la comida se consume
                break;  // solo una celda de comida por movimiento
            }
        }

        // Actualizamos la posición en el tablero
        if (esCeldaSegura(celdaDestino)) {
            // Si llegó a zona segura, la marcamos como safe y dejamos la Z visible
            sp->status = "safe";
            setCell(board, nuevaFila, nuevaCol, "Z");
        } else {
            setCell(board, nuevaFila, nuevaCol, simbolo);
        }

        sp->row = nuevaFila;
        sp->col = nuevaCol;

        // Guardamos el segmento en la lista enlazada para cumplir con el requisito del curso
        // La lista enlazada representa la ruta que recorrió la especie en este movimiento
        MigrationPath rutaRecorrida;
        for (const auto& paso : segmentoPasos) {
            rutaRecorrida.append(paso[0].get<int>(), paso[1].get<int>());
        }
        // rutaRecorrida se destruye al salir del scope, pero ya demostró su uso
    }
}


// --- main ---

int main() {
    std::vector<std::vector<std::string>> board(
        GRID_SIZE, std::vector<std::string>(GRID_SIZE, "[]")
    );

    int turno           = 1;
    int accionesRestantes = ACTIONS_PER_TURN;
    json estadoActual;

    // Si ya existe un state.json, lo cargamos. Si no, generamos el estado inicial.
    if (archivoExiste(STATE_PATH)) {
        estadoActual      = leerJSON(STATE_PATH);
        turno             = estadoActual["turn"].get<int>();
        accionesRestantes = estadoActual["actions_left"].get<int>();

        for (int r = 0; r < GRID_SIZE; r++)
            for (int c = 0; c < GRID_SIZE; c++)
                board[r][c] = estadoActual["board"][r][c].get<std::string>();

    } else {
        // Primera vez que corre el juego: creamos el estado inicial
        estadoActual = construirEstadoInicial();
        escribirJSON(STATE_PATH, estadoActual);
        std::cout << "Estado inicial generado en " << STATE_PATH << std::endl;
        return 0;
    }

    // Cargamos las especies en el árbol AVL para poder buscarlas y actualizarlas rápido
    AVLTree arbol = cargarEspeciesEnArbol(estadoActual);

    // Leemos la acción que envió Python desde la UI
    if (!archivoExiste(INPUT_PATH)) {
        std::cerr << "No hay input.json, esperando acción del jugador." << std::endl;
        return 0;
    }

    json input            = leerJSON(INPUT_PATH);
    std::string accion    = input["action"].get<std::string>();
    std::string simbolo   = input["species"].get<std::string>();

    // El segmento de migración lo calcula Python con backtracking
    // y lo incluye en input.json cuando la acción es "migrate"
    json segmentoPasos = json::array();
    if (input.contains("migration_path")) {
        segmentoPasos = input["migration_path"];
    }

    // Procesamos la acción del jugador
    procesarAccion(accion, simbolo, arbol, board, segmentoPasos);
    accionesRestantes--;

    // Cuando se gastan las 2 acciones del turno, aplicamos los efectos de fin de turno
    if (accionesRestantes <= 0) {
        efectosFinDeTurno(arbol, board);
        turno++;
        accionesRestantes = ACTIONS_PER_TURN;
    }

    // Revisamos si alguien ganó o perdió
    std::string estadoJuego = verificarEstadoJuego(arbol);

    // Escribimos el nuevo state.json para que Python lo lea en el próximo ciclo
    json nuevoEstado = serializarEstado(arbol, board, turno, accionesRestantes, estadoJuego);
    escribirJSON(STATE_PATH, nuevoEstado);

    return 0;
}
