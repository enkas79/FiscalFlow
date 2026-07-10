"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Pannello con il prospetto fiscale/contributivo riepilogativo dei mesi
             consuntivati: tasse pagate con aliquota media effettiva, TFR maturato,
             contributi al fondo Cometa, addizionali, trattenute complessive e netto
             percepito.
"""

from __future__ import annotations

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import QGridLayout, QGroupBox, QLabel, QWidget

from ..model.calcolatore_fiscale import ProspettoFiscaleAnnuale


class PannelloProspettoFiscale(QGroupBox):
    """Riquadro riassuntivo del prospetto fiscale/contributivo dell'anno selezionato."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Prospetto Fiscale", parent)
        self._costruisci_widget()

    def _costruisci_widget(self) -> None:
        layout = QGridLayout(self)

        self.etichetta_retribuzione_lorda = self._crea_valore()
        self.etichetta_imponibile_fiscale = self._crea_valore()
        self.etichetta_tasse_pagate = self._crea_valore(font_grande=True)
        self.etichetta_aliquota_media = self._crea_valore(font_grande=True)
        self.etichetta_irpef = self._crea_valore()
        self.etichetta_add_regionale = self._crea_valore()
        self.etichetta_add_comunale = self._crea_valore()
        self.etichetta_tfr = self._crea_valore()
        self.etichetta_cometa_dipendente = self._crea_valore()
        self.etichetta_cometa_azienda = self._crea_valore()
        self.etichetta_cometa_totale = self._crea_valore()
        self.etichetta_trattenute_totali = self._crea_valore()
        self.etichetta_incidenza_trattenute = self._crea_valore()
        self.etichetta_netto_totale = self._crea_valore(font_grande=True)

        riga = 0
        layout.addWidget(QLabel("Retribuzione lorda totale:"), riga, 0)
        layout.addWidget(self.etichetta_retribuzione_lorda, riga, 1)
        layout.addWidget(QLabel("Imponibile fiscale totale:"), riga, 2)
        layout.addWidget(self.etichetta_imponibile_fiscale, riga, 3)

        riga += 1
        layout.addWidget(QLabel("Totale tasse pagate:"), riga, 0)
        layout.addWidget(self.etichetta_tasse_pagate, riga, 1)
        layout.addWidget(QLabel("Aliquota media effettiva:"), riga, 2)
        layout.addWidget(self.etichetta_aliquota_media, riga, 3)

        riga += 1
        layout.addWidget(QLabel("di cui IRPEF:"), riga, 0)
        layout.addWidget(self.etichetta_irpef, riga, 1)
        layout.addWidget(QLabel("di cui addizionale regionale:"), riga, 2)
        layout.addWidget(self.etichetta_add_regionale, riga, 3)

        riga += 1
        layout.addWidget(QLabel("di cui addizionale comunale:"), riga, 0)
        layout.addWidget(self.etichetta_add_comunale, riga, 1)
        layout.addWidget(QLabel("TFR maturato:"), riga, 2)
        layout.addWidget(self.etichetta_tfr, riga, 3)

        riga += 1
        layout.addWidget(QLabel("Cometa dipendente:"), riga, 0)
        layout.addWidget(self.etichetta_cometa_dipendente, riga, 1)
        layout.addWidget(QLabel("Cometa azienda:"), riga, 2)
        layout.addWidget(self.etichetta_cometa_azienda, riga, 3)

        riga += 1
        layout.addWidget(QLabel("Cometa complessivo:"), riga, 0)
        layout.addWidget(self.etichetta_cometa_totale, riga, 1)
        layout.addWidget(QLabel("Incidenza trattenute su lordo:"), riga, 2)
        layout.addWidget(self.etichetta_incidenza_trattenute, riga, 3)

        riga += 1
        layout.addWidget(QLabel("Trattenute totali (INPS + Cometa dip. + tasse):"), riga, 0)
        layout.addWidget(self.etichetta_trattenute_totali, riga, 1)
        layout.addWidget(QLabel("Netto percepito totale:"), riga, 2)
        layout.addWidget(self.etichetta_netto_totale, riga, 3)

    @staticmethod
    def _crea_valore(font_grande: bool = False) -> QLabel:
        etichetta = QLabel("-")
        font = QFont()
        font.setBold(True)
        font.setPointSize(14 if font_grande else 11)
        etichetta.setFont(font)
        return etichetta

    def aggiorna_prospetto(self, prospetto: ProspettoFiscaleAnnuale) -> None:
        """Aggiorna le etichette del pannello con l'ultimo prospetto calcolato."""
        self.etichetta_retribuzione_lorda.setText(f"{prospetto.retribuzione_lorda_totale:,.2f} €")
        self.etichetta_imponibile_fiscale.setText(f"{prospetto.imponibile_fiscale_totale:,.2f} €")
        self.etichetta_tasse_pagate.setText(f"{prospetto.totale_tasse_pagate:,.2f} €")
        self.etichetta_aliquota_media.setText(f"{prospetto.aliquota_media_effettiva:.2f} %")
        self.etichetta_irpef.setText(f"{prospetto.irpef_pagata_totale:,.2f} €")
        self.etichetta_add_regionale.setText(f"{prospetto.addizionale_regionale_pagata_totale:,.2f} €")
        self.etichetta_add_comunale.setText(f"{prospetto.addizionale_comunale_pagata_totale:,.2f} €")
        self.etichetta_tfr.setText(f"{prospetto.tfr_maturato_totale:,.2f} €")
        self.etichetta_cometa_dipendente.setText(f"{prospetto.contributi_cometa_dipendente_totale:,.2f} €")
        self.etichetta_cometa_azienda.setText(f"{prospetto.contributi_cometa_azienda_totale:,.2f} €")
        self.etichetta_cometa_totale.setText(f"{prospetto.totale_cometa_complessivo:,.2f} €")
        self.etichetta_trattenute_totali.setText(f"{prospetto.trattenute_totali:,.2f} €")
        self.etichetta_incidenza_trattenute.setText(f"{prospetto.incidenza_trattenute_su_lordo:.2f} %")
        self.etichetta_netto_totale.setText(f"{prospetto.netto_percepito_totale:,.2f} €")
