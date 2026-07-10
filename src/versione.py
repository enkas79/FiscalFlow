"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Espone il numero di versione dell'applicazione letto da VERSION.txt, fonte
             unica di verità condivisa tra il codice sorgente, la pipeline CI/CD e i
             metadati degli installer generati per Windows, Ubuntu e macOS.
"""

from __future__ import annotations

import sys
from pathlib import Path

_NOME_FILE_VERSIONE = "VERSION.txt"


def get_versione() -> str:
    """
    Restituisce il numero di versione corrente dell'applicazione.

    Funziona sia in esecuzione da sorgente (VERSION.txt nella radice del progetto) sia
    da bundle PyInstaller (VERSION.txt incluso tra i dati dell'eseguibile/app).
    """
    directory_base = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent.parent))
    return (directory_base / _NOME_FILE_VERSIONE).read_text(encoding="utf-8").strip()
