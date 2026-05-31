// Ecosystem Survival - AVL Tree para datos de especies
// Computer Sciences I - Semester 2026-I
// Equipo 8: Cristian Castañeda, Julian Carvajal, Juan Pablo Angulo
// Cristian Castañeda - Engine Developer

#ifndef TREE_H
#define TREE_H

#include <string>
#include <vector>
#include <algorithm>

struct AVLNode {
    std::string symbol;
    std::string name;
    int population;
    int hunger;
    int row;
    int col;
    std::string status;   // "active", "safe", "extinct"
    bool fedThisTurn;     // true si ya fue alimentada en el turno actual
    int height;
    AVLNode* left;
    AVLNode* right;

    AVLNode(std::string sym, std::string nm, int pop, int hun, int r, int c)
        : symbol(sym), name(nm), population(pop), hunger(hun),
          row(r), col(c), status("active"), fedThisTurn(false), height(1),
          left(nullptr), right(nullptr) {}
};

class AVLTree {
private:
    AVLNode* root;

    int height(AVLNode* node) {
        if (node == nullptr) return 0;
        return node->height;
    }

    int balanceFactor(AVLNode* node) {
        if (node == nullptr) return 0;
        return height(node->left) - height(node->right);
    }

    void updateHeight(AVLNode* node) {
        if (node != nullptr)
            node->height = 1 + std::max(height(node->left), height(node->right));
    }

    AVLNode* rotateRight(AVLNode* y) {
        AVLNode* x  = y->left;
        AVLNode* t2 = x->right;

        x->right = y;
        y->left  = t2;

        updateHeight(y);
        updateHeight(x);

        return x;
    }

    AVLNode* rotateLeft(AVLNode* x) {
        AVLNode* y  = x->right;
        AVLNode* t2 = y->left;

        y->left  = x;
        x->right = t2;

        updateHeight(x);
        updateHeight(y);

        return y;
    }

    AVLNode* balance(AVLNode* node) {
        updateHeight(node);
        int bf = balanceFactor(node);

        // left heavy
        if (bf > 1) {
            if (balanceFactor(node->left) < 0)
                node->left = rotateLeft(node->left);
            return rotateRight(node);
        }

        // right heavy
        if (bf < -1) {
            if (balanceFactor(node->right) > 0)
                node->right = rotateRight(node->right);
            return rotateLeft(node);
        }

        return node;
    }

    AVLNode* insert(AVLNode* node, AVLNode* newNode) {
        if (node == nullptr) return newNode;

        if (newNode->symbol < node->symbol)
            node->left  = insert(node->left,  newNode);
        else if (newNode->symbol > node->symbol)
            node->right = insert(node->right, newNode);
        else {
            // simbolo ya existe, actualiza datos
            node->population = newNode->population;
            node->hunger     = newNode->hunger;
            node->row        = newNode->row;
            node->col        = newNode->col;
            node->status     = newNode->status;
            delete newNode;
            return node;
        }

        return balance(node);
    }

    AVLNode* search(AVLNode* node, const std::string& symbol) {
        if (node == nullptr)           return nullptr;
        if (symbol == node->symbol)    return node;
        if (symbol  < node->symbol)    return search(node->left,  symbol);
        return search(node->right, symbol);
    }

    void inorder(AVLNode* node, std::vector<AVLNode*>& result) {
        if (node == nullptr) return;
        inorder(node->left, result);
        result.push_back(node);
        inorder(node->right, result);
    }

    void destroy(AVLNode* node) {
        if (node == nullptr) return;
        destroy(node->left);
        destroy(node->right);
        delete node;
    }

public:
    AVLTree() : root(nullptr) {}

    ~AVLTree() {
        destroy(root);
    }

    void insert(const std::string& symbol, const std::string& name,
                int population, int hunger, int row, int col) {
        AVLNode* node = new AVLNode(symbol, name, population, hunger, row, col);
        root = insert(root, node);
    }

    AVLNode* search(const std::string& symbol) {
        return search(root, symbol);
    }

    void update(const std::string& symbol, int population, int hunger,
                const std::string& status, int row, int col) {
        AVLNode* node = search(symbol);
        if (node != nullptr) {
            node->population = population;
            node->hunger     = hunger;
            node->status     = status;
            node->row        = row;
            node->col        = col;
        }
    }

    // para serializar todas las especies al JSON
    std::vector<AVLNode*> getAllSpecies() {
        std::vector<AVLNode*> result;
        inorder(root, result);
        return result;
    }

    bool isEmpty() const {
        return root == nullptr;
    }
};

#endif
