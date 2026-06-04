# 🌿 Ecosystem Survival

## 📌 Project Overview

**Ecosystem Survival** is a grid-based strategy and simulation game developed as part of the *Computer Science I* course. The project transforms fundamental computer science concepts—such as algorithms and data structures—into interactive gameplay mechanics.

In this game, the player is responsible for maintaining the balance of a small ecosystem. Different species coexist on a board, each with its own needs, risks, and survival conditions. The player must make strategic decisions to ensure that no species becomes extinct while guiding them toward safe zones.

What makes the game especially interesting is that every decision is driven by algorithmic logic:

- A **greedy algorithm** prioritizes which species should be handled first based on risk.
- A **backtracking algorithm** finds safe migration paths across the board.
- An **AVL Tree** is used to efficiently store and manage species data in real time.

This creates a hybrid system where strategy, simulation, and data structures work together dynamically.

---

## 🎮 Why is the game interesting?

Ecosystem Survival is more than a game—it is an applied simulation of computer science concepts.

- It introduces **strategic decision-making under constraints**
- It simulates **dynamic system behavior over time**
- It connects theory (algorithms & data structures) with real execution logic
- It forces the player to adapt to a constantly changing environment

Each turn feels dynamic, since species conditions and board states evolve continuously.

---

## 🧠 System Architecture

The project is implemented as a modular multi-layer system:

- **Python (AI Layer):** Handles decision-making using Greedy and Backtracking algorithms  
- **C++ (Engine Layer):** Executes game rules, validates movements, and processes turns  
- **AVL Tree (Data Structure):** Stores and manages all species efficiently  
- **JSON (Communication Layer):** Synchronizes state between Python and C++  

All components interact through a shared JSON state file, ensuring consistency across the system.

---

## 📂 Repository Structure

At this stage (Checkpoint 1), the repository focuses on design and system planning rather than full implementation.

### 📁 `documentation/`

Contains all technical and conceptual design work:

- Checkpoint report (PDF)
- Algorithm design (Greedy & Backtracking pseudocode)
- Data structure design (AVL Tree and others)
- JSON input/output specification
- Game rules and system behavior
- System architecture diagrams

👉 This folder defines how the system is intended to work before implementation.

---

### 📁 `video_demo/`

Contains the checkpoint demonstration video:

- Game concept explanation
- Rules and mechanics overview
- Design decisions
- Visual representation of system behavior

👉 It complements the documentation with a visual explanation of the project.

---

## 🎯 Main Objective of the Project

The goal of Ecosystem Survival is to design and implement a system where:

- Algorithms are part of the gameplay logic
- Data structures manage a dynamic ecosystem efficiently
- The system behaves like a real-time simulation engine

At this checkpoint, the focus is on building a solid theoretical and structural foundation:

- Rule definition
- Algorithm design
- Data structure modeling
- System architecture planning

---

## 🚧 Current Status

This repository corresponds to **Milestone 1 (Checkpoint)**.

✔️ System design completed  
✔️ Algorithms defined (Greedy + Backtracking)  
✔️ AVL Tree concept designed  
✔️ JSON communication structure defined  
✔️ Architecture designed  
❌ Full gameplay implementation pending  

---

## 👥 Team

- Cristian Esteban Castañeda Vargas  
- Julian Carvajal Garnica  
- Juan Pablo Angulo Guerrero  

---

## 📎 Note

This repository represents a **design-stage project**. The implementation will be developed and integrated in later milestones.
