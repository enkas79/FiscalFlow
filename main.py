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
from src.view.stile import FOGLIO_STILE


def main() -> int:
    app = QApplication(sys.argv)
    app.setStyleSheet(FOGLIO_STILE)

    finestra = MainWindow()
    _controller = MainController(finestra)
    finestra.show()

    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
