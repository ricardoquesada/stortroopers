# Stortroopers Editor Guide

Stortroopers Editor is a powerful pixel art character creator tool designed to help you build unique characters by combining various assets like bodies, heads, hair, and accessories.

## Table of Contents
1. [Getting Started](#getting-started)
2. [Interface Overview](#interface-overview)
3. [Working with Projects](#working-with-projects)
4. [Creating Characters](#creating-characters)
5. [Exporting](#exporting)
6. [Keyboard Shortcuts](#keyboard-shortcuts)

## Getting Started

To launch the editor, run the following command in your terminal:

```bash
make run
```

This will open the main window where you can start creating characters immediately.

## Interface Overview

The editor interface consists of three main areas:

1.  **Canvas (Center):** This is your workspace where the character is assembled. You can see your changes in real-time.
2.  **Tools Panel (Left/Right):** Contains all the controls for selecting characters, assets, and other utilities.
3.  **Menu Bar (Top):** Provides access to file operations and window management.

### Tools Panel

-   **Character Type:** Dropdown to select the base style of the character (e.g., Boy, Girl, Robot).
-   **Articles File:** Selects the specific data file defining available assets for the chosen character type.
-   **Category Tabs:** Organize assets into groups like Body, Head, Hair, etc.
-   **Asset List:** Displays icons for all available items in the selected category.
-   **Random:** Generates a completely random character.
-   **Zoom Controls:** Buttons to Zoom In (+) and Zoom Out (-) of the canvas.

## Working with Projects

A "Project" (`.stp` or `.json` file) saves the current configuration of your character (which assets are selected and their positions), allowing you to edit them later.

-   **New Project:** Creates a fresh, empty workspace in a new tab.
-   **Open Project:** Loads a previously saved project file.
-   **Open Recent:** Quickly access your most recently opened files.
-   **Save Project:** Saves your current progress. If it's a new project, you will be prompted to choose a file location.
-   **Save Project As:** Save the current project to a ne filew location.

> **Note:** The editor restores your last session automatically when you reopen it.

## Creating Characters

1.  **Select a Character Type:** Use the "Character Type" dropdown in the Tools panel to choose a base.
2.  **Browse Categories:** Click through the tabs (Body, Head, etc.) to view different asset types.
3.  **Add Assets:** Click on an icon in the Asset List to add it to your character on the canvas.
    -   Active assets are highlighted in **Cyan**.
    -   Clicking a different asset in the same layer overrides the previous one.
4.  **Remove Assets:** Right-click an asset in the list to remove it, or simply click a different one to replace it.
5.  **Randomize:** Click the **Random** button to instantly generate a unique character combination.

## Exporting

Once you are happy with your character, you can export it as an image.

1.  Click **Save Character to PNG** in the Tools panel, or select **File > Export to PNG...**.
2.  Choose a destination and filename.
3.  The character will be saved as a transparent PNG image.

## Keyboard Shortcuts

| Action | Shortcut |
| :--- | :--- |
| **New Project** | `Ctrl + N` |
| **Open Project** | `Ctrl + O` |
| **Save Project** | `Ctrl + S` |
| **Save Project As** | `Ctrl + Shift + S` |
| **Export to PNG** | `Ctrl + E` |
| **Close Tab** | `Ctrl + W` |
