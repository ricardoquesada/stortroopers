#!/usr/bin/env python3
# Copyright (c) 2025 Ricardo Quesada

import os
import sys

from PySide6.QtWidgets import QApplication

from .ui import MainWindow


def main():
    app = QApplication(sys.argv)

    # Path to resources
    # Assuming this script is run from various locations, let's try to locate src/res
    # Relative to this file: ../res
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    res_path = os.path.join(base_dir, "res")

    if not os.path.exists(res_path):
        print(f"Error: Could not find resource directory at {res_path}")
        return 1

    window = MainWindow(res_path)
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
