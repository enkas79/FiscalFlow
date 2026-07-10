"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Pannello in evidenza con la proiezione di fine anno: RAL stimata, tasse
             totali previste ed esito del conguaglio fiscale (a credito o a debito).
"""

from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel, QWidget

from ..model import config
from ..model.calcolatore_fiscale import RisultatoProiezione


class PannelloProiezioneConguaglio(QGroupBox):
    """Riquadro riassuntivo della proiezione fiscale e del conguaglio di fine anno."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Proiezione e Conguaglio di Fine Anno", parent)
        self._costruisci_widget()

    def _costruisci_widget(self) -> None:
        # Una coppia etichetta/valore per riga (non due affiancate): il pannello convive con
        # il Prospetto Fiscale in metà larghezza della finestra, e un valore con più decine di
        # caratteri (es. "Addizionali calcolate su: ...") verrebbe troncato con quattro colonne.
        layout = QGridLayout(self)
        layout.setColumnStretch(1, 1)
        layout.setHorizontalSpacing(12)
        layout.setVerticalSpacing(8)

        self.etichetta_ral = self._crea_valore()
        self.etichetta_tredicesima = self._crea_valore()
        self.etichetta_tasse_dovute = self._crea_valore()
        self.etichetta_tasse_pagate = self._crea_valore()
        self.etichetta_conguaglio = self._crea_valore(font_grande=True)
        self.etichetta_esito = self._crea_valore(font_grande=True)
        self.etichetta_territorio = self._crea_valore()
        self.etichetta_territorio.setWordWrap(True)

        righe = (
            ("RAL stimata:", self.etichetta_ral),
            ("Tredicesima stimata:", self.etichetta_tredicesima),
            ("Totale tasse dovute:", self.etichetta_tasse_dovute),
            ("Totale tasse pagate:", self.etichetta_tasse_pagate),
            ("Conguaglio:", self.etichetta_conguaglio),
            ("Esito:", self.etichetta_esito),
            ("Addizionali calcolate su:", self.etichetta_territorio),
        )
        for indice_riga, (testo_etichetta, valore) in enumerate(righe):
            layout.addWidget(QLabel(testo_etichetta), indice_riga, 0)
            layout.addWidget(valore, indice_riga, 1)

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
        regione_mostrata = (
            "aliquota media nazionale"
            if risultato.regione_utilizzata == config.CHIAVE_FALLBACK
            else risultato.regione_utilizzata
        )
        self.etichetta_territorio.setText(
            f"{risultato.comune_utilizzato} ({regione_mostrata}) — "
            f"regionale {risultato.addizionale_regionale_dovuta:,.2f} € · "
            f"comunale {risultato.addizionale_comunale_dovuta:,.2f} €"
        )

        colore = (
            "#c0392b"
            if risultato.esito == "A DEBITO"
            else "#27ae60"
            if risultato.esito == "A CREDITO"
            else "#7f8c8d"
        )
        self.etichetta_conguaglio.setStyleSheet(f"color: {colore};")
        self.etichetta_esito.setStyleSheet(f"color: {colore};")
