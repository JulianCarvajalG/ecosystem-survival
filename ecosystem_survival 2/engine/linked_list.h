// Ecosystem Survival - Linked List para rutas de migracion
// Computer Sciences I - Semester 2026-I
// Equipo 8: Cristian Castañeda, Julian Carvajal, Juan Pablo Angulo
// Cristian Castañeda - Engine Developer

#ifndef LINKED_LIST_H
#define LINKED_LIST_H

#include <vector>
#include <utility>

struct PathNode {
    int row;
    int col;
    PathNode* next;

    PathNode(int r, int c) : row(r), col(c), next(nullptr) {}
};

class MigrationPath {
private:
    PathNode* head;
    PathNode* tail;
    int size;

public:
    MigrationPath() : head(nullptr), tail(nullptr), size(0) {}

    ~MigrationPath() {
        clear();
    }

    void append(int row, int col) {
        PathNode* node = new PathNode(row, col);
        if (tail == nullptr) {
            head = node;
            tail = node;
        } else {
            tail->next = node;
            tail = node;
        }
        size++;
    }

    void clear() {
        PathNode* current = head;
        while (current != nullptr) {
            PathNode* next = current->next;
            delete current;
            current = next;
        }
        head = nullptr;
        tail = nullptr;
        size = 0;
    }

    int getSize() const {
        return size;
    }

    bool isEmpty() const {
        return head == nullptr;
    }

    // devuelve el path como vector de pares para serializar a JSON
    std::vector<std::pair<int,int>> toVector() const {
        std::vector<std::pair<int,int>> result;
        PathNode* current = head;
        while (current != nullptr) {
            result.push_back({current->row, current->col});
            current = current->next;
        }
        return result;
    }

    PathNode* getHead() const {
        return head;
    }
};

#endif
