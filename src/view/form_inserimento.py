"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Form di inserimento dati per una singola busta paga mensile, con validazione
             tramite widget PyQt6 dedicati (QComboBox, QDoubleSpinBox, QSpinBox).
"""

from __future__ import annotations

from datetime import date

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..model.busta_paga import BustaPaga
from ..model.enums import LivelloCCNL, Mese


class FormInserimentoBustaPaga(QWidget):
    """Form per l'inserimento validato dei dati di una busta paga mensile."""

    busta_paga_inserita = pyqtSignal(BustaPaga)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._costruisci_widget()

    def _costruisci_widget(self) -> None:
        gruppo = QGroupBox("Inserimento Busta Paga", self)
        form_layout = QFormLayout()

        self.combo_mese = QComboBox(self)
        for mese in Mese:
            self.combo_mese.addItem(mese.nome_italiano, userData=mese)

        self.spin_anno = QSpinBox(self)
        self.spin_anno.setRange(2000, 2100)
        self.spin_anno.setValue(date.today().year)

        self.combo_livello = QComboBox(self)
        for livello in LivelloCCNL:
            self.combo_livello.addItem(livello.value, userData=livello)

        self.spin_totale_elementi = self._crea_spin_valuta()
        self.spin_ore_ordinarie = self._crea_spin_ore()
        self.spin_straordinari = self._crea_spin_valuta()
        self.spin_fringe_benefit = self._crea_spin_valuta()
        self.spin_contributi_inps = self._crea_spin_valuta()
        self.spin_contributi_cometa_dip = self._crea_spin_valuta()
        self.spin_contributi_cometa_azi = self._crea_spin_valuta()
        self.spin_irpef_pagata = self._crea_spin_valuta()
        self.spin_add_regionale = self._crea_spin_valuta()
        self.spin_add_comunale = self._crea_spin_valuta()
        self.spin_conguaglio_730 = self._crea_spin_valuta(minimo=-99_999.0)

        form_layout.addRow("Mese", self.combo_mese)
        form_layout.addRow("Anno", self.spin_anno)
        form_layout.addRow("Livello CCNL", self.combo_livello)
        form_layout.addRow("Totale elementi retributivi (€)", self.spin_totale_elementi)
        form_layout.addRow("Ore ordinarie", self.spin_ore_ordinarie)
        form_layout.addRow("Straordinari (€)", self.spin_straordinari)
        form_layout.addRow("Fringe benefit (€)", self.spin_fringe_benefit)
        form_layout.addRow("Contributi INPS c/dipendente (€)", self.spin_contributi_inps)
        form_layout.addRow("Fondo Cometa c/dipendente (€)", self.spin_contributi_cometa_dip)
        form_layout.addRow("Fondo Cometa c/azienda (€)", self.spin_contributi_cometa_azi)
        form_layout.addRow("IRPEF pagata (€)", self.spin_irpef_pagata)
        form_layout.addRow("Addizionale regionale pagata (€)", self.spin_add_regionale)
        form_layout.addRow("Addizionale comunale pagata (€)", self.spin_add_comunale)
        form_layout.addRow("Conguaglio 730 (€, +rimborso/-trattenuta)", self.spin_conguaglio_730)

        self.pulsante_aggiungi = QPushButton("Aggiungi busta paga", self)
        self.pulsante_aggiungi.clicked.connect(self._gestisci_click_aggiungi)

        layout_gruppo = QVBoxLayout(gruppo)
        layout_gruppo.addLayout(form_layout)
        layout_gruppo.addWidget(self.pulsante_aggiungi)

        layout_esterno = QVBoxLayout(self)
        layout_esterno.addWidget(gruppo)

    @staticmethod
    def _crea_spin_valuta(minimo: float = 0.0, massimo: float = 999_999.0) -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(minimo, massimo)
        spin.setDecimals(2)
        spin.setSuffix(" €")
        spin.setSingleStep(50.0)
        return spin

    @staticmethod
    def _crea_spin_ore() -> QDoubleSpinBox:
        spin = QDoubleSpinBox()
        spin.setRange(0.0, 744.0)
        spin.setDecimals(1)
        spin.setSingleStep(1.0)
        return spin

    def _gestisci_click_aggiungi(self) -> None:
        busta = self.leggi_busta_paga()
        self.busta_paga_inserita.emit(busta)
        self.pulisci_campi()

    def leggi_busta_paga(self) -> BustaPaga:
        """Costruisce l'oggetto BustaPaga a partire dai valori correnti dei widget."""
        return BustaPaga(
            mese=self.combo_mese.currentData(),
            anno=self.spin_anno.value(),
            livello=self.combo_livello.currentData(),
            totale_elementi_retributivi=self.spin_totale_elementi.value(),
            ore_ordinarie=self.spin_ore_ordinarie.value(),
            straordinari=self.spin_straordinari.value(),
            fringe_benefit=self.spin_fringe_benefit.value(),
            contributi_inps_dipendente=self.spin_contributi_inps.value(),
            contributi_cometa_dipendente=self.spin_contributi_cometa_dip.value(),
            contributi_cometa_azienda=self.spin_contributi_cometa_azi.value(),
            irpef_pagata=self.spin_irpef_pagata.value(),
            addizionale_regionale_pagata=self.spin_add_regionale.value(),
            addizionale_comunale_pagata=self.spin_add_comunale.value(),
            conguaglio_730=self.spin_conguaglio_730.value(),
        )

    def pulisci_campi(self) -> None:
        for spin in self.findChildren(QDoubleSpinBox):
            spin.setValue(0.0)
