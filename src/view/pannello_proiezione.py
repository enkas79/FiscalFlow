"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Pannello in evidenza con la proiezione di fine anno: RAL stimata, tasse
             totali previste ed esito del conguaglio fiscale (a credito o a debito).
"""

from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel, QWidget

from ..model.calcolatore_fiscale import RisultatoProiezione


class PannelloProiezioneConguaglio(QGroupBox):
    """Riquadro riassuntivo della proiezione fiscale e del conguaglio di fine anno."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Proiezione e Conguaglio di Fine Anno", parent)
        self._costruisci_widget()

    def _costruisci_widget(self) -> None:
        layout = QGridLayout(self)

        self.etichetta_ral = self._crea_valore()
        self.etichetta_tredicesima = self._crea_valore()
        self.etichetta_tasse_dovute = self._crea_valore()
        self.etichetta_tasse_pagate = self._crea_valore()
        self.etichetta_conguaglio = self._crea_valore(font_grande=True)
        self.etichetta_esito = self._crea_valore(font_grande=True)

        layout.addWidget(QLabel("RAL stimata:"), 0, 0)
        layout.addWidget(self.etichetta_ral, 0, 1)
        layout.addWidget(QLabel("Tredicesima stimata:"), 0, 2)
        layout.addWidget(self.etichetta_tredicesima, 0, 3)

        layout.addWidget(QLabel("Totale tasse dovute:"), 1, 0)
        layout.addWidget(self.etichetta_tasse_dovute, 1, 1)
        layout.addWidget(QLabel("Totale tasse pagate:"), 1, 2)
        layout.addWidget(self.etichetta_tasse_pagate, 1, 3)

        layout.addWidget(QLabel("Conguaglio:"), 2, 0)
        layout.addWidget(self.etichetta_conguaglio, 2, 1)
        layout.addWidget(QLabel("Esito:"), 2, 2)
        layout.addWidget(self.etichetta_esito, 2, 3)

    @staticmethod
    def _crea_valore(font_grande: bool = False) -> QLabel:
        etichetta = QLabel("-")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14 if font_grande else 11)
        etichetta.setFont(font)
        return etichetta

    def aggiorna_proiezione(self, risultato: RisultatoProiezione) -> None:
        """Aggiorna le etichette del pannello con l'ultimo risultato calcolato."""
        self.etichetta_ral.setText(f"{risultato.ral_stimata:,.2f} €")
        self.etichetta_tredicesima.setText(f"{risultato.tredicesima_stimata:,.2f} €")
        self.etichetta_tasse_dovute.setText(f"{risultato.totale_tasse_dovute:,.2f} €")
        self.etichetta_tasse_pagate.setText(f"{risultato.totale_tasse_pagate:,.2f} €")
        self.etichetta_conguaglio.setText(f"{risultato.conguaglio:,.2f} €")
        self.etichetta_esito.setText(risultato.esito)

        colore = (
            "#c0392b"
            if risultato.esito == "A DEBITO"
            else "#27ae60"
            if risultato.esito == "A CREDITO"
            else "#7f8c8d"
        )
        self.etichetta_conguaglio.setStyleSheet(f"color: {colore};")
        self.etichetta_esito.setStyleSheet(f"color: {colore};")
