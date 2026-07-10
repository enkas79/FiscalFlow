"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Form di inserimento dati per una singola busta paga mensile. I campi vengono
             compilati automaticamente caricando il PDF del cedolino (lettura interamente
             locale, nessuna connessione di rete) e restano modificabili con i widget PyQt6
             dedicati per una verifica prima della conferma (QComboBox, QDoubleSpinBox,
             QSpinBox).
"""

from __future__ import annotations

from datetime import date
from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDoubleSpinBox,
    QFileDialog,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from ..model import config
from ..model.busta_paga import BustaPaga
from ..model.enums import LivelloCCNL, Mese
from ..model.importatore_pdf import ErroreImportazionePdf, ImportatorePdfBustaPaga


class FormInserimentoBustaPaga(QWidget):
    """Form per l'inserimento validato dei dati di una busta paga mensile."""

    busta_paga_inserita = pyqtSignal(BustaPaga)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._costruisci_widget()

    def _costruisci_widget(self) -> None:
        gruppo = QGroupBox("Inserimento Busta Paga", self)

        self.pulsante_carica_pdf = QPushButton("Carica da PDF cedolino…", self)
        self.pulsante_carica_pdf.clicked.connect(self._gestisci_click_carica_pdf)

        etichetta_carica_pdf = QLabel(
            "Carica uno o più PDF di cedolino (lettura locale, nessun dato lascia il computer). "
            "Con un solo file i campi sottostanti si compilano per la verifica prima di premere "
            "\"Aggiungi busta paga\"; selezionandone più di uno, dopo conferma vengono aggiunte "
            "tutte insieme.",
            self,
        )
        etichetta_carica_pdf.setWordWrap(True)

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

        # Editabile: l'elenco predefinito copre solo alcuni comuni capoluogo, ma il comune di
        # residenza fiscale può essere uno qualsiasi. Le voci elencate sono un suggerimento
        # rapido, non un vincolo: si può digitare liberamente un comune non presente in elenco.
        self.combo_comune = QComboBox(self)
        self.combo_comune.setEditable(True)
        self.combo_comune.setInsertPolicy(QComboBox.InsertPolicy.NoInsert)
        self.combo_comune.lineEdit().setPlaceholderText("Digita il tuo comune, es. Loria")
        for comune in config.get_comuni_disponibili():
            self.combo_comune.addItem(comune, userData=comune)
        self.combo_comune.setCurrentIndex(-1)
        self.combo_comune.setCurrentText("")

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
        self.spin_quota_tfr = self._crea_spin_valuta()

        form_layout.addRow("Mese", self.combo_mese)
        form_layout.addRow("Anno", self.spin_anno)
        form_layout.addRow("Livello CCNL", self.combo_livello)
        form_layout.addRow("Comune di residenza fiscale", self.combo_comune)
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
        form_layout.addRow("Quota TFR maturata nel mese (€)", self.spin_quota_tfr)

        self.pulsante_aggiungi = QPushButton("Aggiungi busta paga", self)
        self.pulsante_aggiungi.clicked.connect(self._gestisci_click_aggiungi)

        layout_gruppo = QVBoxLayout(gruppo)
        layout_gruppo.addWidget(self.pulsante_carica_pdf)
        layout_gruppo.addWidget(etichetta_carica_pdf)
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

    def _gestisci_click_carica_pdf(self) -> None:
        percorsi_scelti, _ = QFileDialog.getOpenFileNames(
            self, "Seleziona uno o più PDF di cedolino", "", "File PDF (*.pdf)"
        )
        if not percorsi_scelti:
            return

        if len(percorsi_scelti) == 1:
            self._importa_pdf_singolo(Path(percorsi_scelti[0]))
        else:
            self._importa_pdf_multipli([Path(p) for p in percorsi_scelti])

    def _importa_pdf_singolo(self, percorso: Path) -> None:
        self.pulsante_carica_pdf.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            busta = ImportatorePdfBustaPaga().estrai_busta_paga(percorso)
        except ErroreImportazionePdf as errore:
            QMessageBox.critical(self, "Importazione da PDF fallita", str(errore))
            return
        finally:
            QApplication.restoreOverrideCursor()
            self.pulsante_carica_pdf.setEnabled(True)

        self.imposta_valori(busta)
        QMessageBox.information(
            self,
            "Dati importati dal PDF",
            "I campi sono stati compilati automaticamente dal cedolino. Verifica i valori e "
            "premi \"Aggiungi busta paga\" per confermare.",
        )

    def _importa_pdf_multipli(self, percorsi: list[Path]) -> None:
        self.pulsante_carica_pdf.setEnabled(False)
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            importate, errori = ImportatorePdfBustaPaga().estrai_buste_paga(percorsi)
        finally:
            QApplication.restoreOverrideCursor()
            self.pulsante_carica_pdf.setEnabled(True)

        if not importate:
            dettaglio = "\n".join(f"- {percorso.name}: {messaggio}" for percorso, messaggio in errori)
            QMessageBox.critical(
                self,
                "Importazione da PDF fallita",
                f"Nessuno dei {len(percorsi)} PDF selezionati è stato riconosciuto:\n\n{dettaglio}",
            )
            return

        righe_riepilogo = "\n".join(f"- {busta.mese.nome_italiano} {busta.anno}" for busta in importate)
        messaggio = f"Verranno aggiunte {len(importate)} buste paga:\n\n{righe_riepilogo}"
        if errori:
            dettaglio_errori = "\n".join(f"- {percorso.name}: {msg}" for percorso, msg in errori)
            messaggio += (
                f"\n\n{len(errori)} file non riconosciuti (da inserire manualmente):\n{dettaglio_errori}"
            )
        messaggio += "\n\nConfermi l'inserimento?"

        risposta = QMessageBox.question(
            self,
            "Conferma importazione multipla",
            messaggio,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if risposta != QMessageBox.StandardButton.Yes:
            return

        for busta in importate:
            self.busta_paga_inserita.emit(busta)

    def imposta_valori(self, busta: BustaPaga) -> None:
        """Compila i widget del form con i valori della busta paga indicata (es. da PDF)."""
        self._imposta_combo_per_dato(self.combo_mese, busta.mese)
        self.spin_anno.setValue(busta.anno)
        self._imposta_combo_per_dato(self.combo_livello, busta.livello)
        self._imposta_combo_comune(busta.comune_residenza)
        self.spin_totale_elementi.setValue(busta.totale_elementi_retributivi)
        self.spin_ore_ordinarie.setValue(busta.ore_ordinarie)
        self.spin_straordinari.setValue(busta.straordinari)
        self.spin_fringe_benefit.setValue(busta.fringe_benefit)
        self.spin_contributi_inps.setValue(busta.contributi_inps_dipendente)
        self.spin_contributi_cometa_dip.setValue(busta.contributi_cometa_dipendente)
        self.spin_contributi_cometa_azi.setValue(busta.contributi_cometa_azienda)
        self.spin_irpef_pagata.setValue(busta.irpef_pagata)
        self.spin_add_regionale.setValue(busta.addizionale_regionale_pagata)
        self.spin_add_comunale.setValue(busta.addizionale_comunale_pagata)
        self.spin_conguaglio_730.setValue(busta.conguaglio_730)
        self.spin_quota_tfr.setValue(busta.quota_tfr_maturata)

    @staticmethod
    def _imposta_combo_per_dato(combo: QComboBox, valore: object) -> None:
        indice = combo.findData(valore)
        if indice >= 0:
            combo.setCurrentIndex(indice)

    def _imposta_combo_comune(self, comune: str) -> None:
        if comune:
            self.combo_comune.setCurrentText(comune)

    def leggi_busta_paga(self) -> BustaPaga:
        """Costruisce l'oggetto BustaPaga a partire dai valori correnti dei widget."""
        return BustaPaga(
            mese=self.combo_mese.currentData(),
            anno=self.spin_anno.value(),
            livello=self.combo_livello.currentData(),
            totale_elementi_retributivi=self.spin_totale_elementi.value(),
            comune_residenza=self.combo_comune.currentText().strip(),
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
            quota_tfr_maturata=self.spin_quota_tfr.value(),
        )

    def pulisci_campi(self) -> None:
        for spin in self.findChildren(QDoubleSpinBox):
            spin.setValue(0.0)
