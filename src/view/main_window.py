"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Finestra principale dell'applicazione: assembla il form di inserimento,
             la tabella dei progressivi mensili e il pannello di proiezione/conguaglio.
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QMainWindow, QSplitter, QVBoxLayout, QWidget

from ..versione import get_versione
from .form_inserimento import FormInserimentoBustaPaga
from .pannello_proiezione import PannelloProiezioneConguaglio
from .prospetto_fiscale import PannelloProspettoFiscale
from .tabella_riepilogo import TabellaRiepilogoBustePaga


class MainWindow(QMainWindow):
    """Finestra principale dell'applicazione FiscalFlow."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"FiscalFlow v{get_versione()} - Proiezione Fiscale Buste Paga")
        self.resize(1200, 800)

        self.form_inserimento = FormInserimentoBustaPaga(self)
        self.tabella_riepilogo = TabellaRiepilogoBustePaga(self)
        self.pannello_proiezione = PannelloProiezioneConguaglio(self)
        self.pannello_prospetto = PannelloProspettoFiscale(self)

        self._costruisci_layout()

    def _costruisci_layout(self) -> None:
        contenitore_centrale = QWidget(self)
        layout_principale = QVBoxLayout(contenitore_centrale)

        self.form_inserimento.setMinimumWidth(360)

        splitter = QSplitter(Qt.Orientation.Horizontal, self)
        splitter.addWidget(self.form_inserimento)
        splitter.addWidget(self.tabella_riepilogo)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)

        layout_principale.addWidget(splitter, stretch=1)
        layout_principale.addWidget(self.pannello_proiezione, stretch=0)
        layout_principale.addWidget(self.pannello_prospetto, stretch=0)

        self.setCentralWidget(contenitore_centrale)
