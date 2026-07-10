"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Entry point dell'applicazione FiscalFlow.
"""

from __future__ import annotations

import sys

from PyQt6.QtWidgets import QApplication

from src.controller.main_controller import MainController
from src.view.main_window import MainWindow


def main() -> int:
    app = QApplication(sys.argv)

    finestra = MainWindow()
    _controller = MainController(finestra)
    finestra.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
