"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Pannello di caricamento busta paga: l'unico modo per inserire una busta paga è
             importarla da uno o più PDF di cedolino (lettura interamente locale, nessuna
             connessione di rete). Non sono previsti campi di compilazione manuale; prima
             dell'inserimento viene sempre mostrato un riepilogo di conferma con i dati
             riconosciuti.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QWidget,
)

from ..model.busta_paga import BustaPaga
from ..model.importatore_pdf import ErroreImportazionePdf, ImportatorePdfBustaPaga


class FormInserimentoBustaPaga(QWidget):
    """Pannello per il caricamento di una o più buste paga a partire dai PDF dei cedolini."""

    busta_paga_inserita = pyqtSignal(BustaPaga)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._costruisci_widget()

    def _costruisci_widget(self) -> None:
        gruppo = QGroupBox("Caricamento Busta Paga da PDF", self)

        self.pulsante_carica_pdf = QPushButton("Carica da PDF cedolino…", self)
        self.pulsante_carica_pdf.clicked.connect(self._gestisci_click_carica_pdf)

        etichetta_carica_pdf = QLabel(
            "Seleziona uno o più PDF di cedolino (lettura locale, nessun dato lascia il "
            "computer). Dopo un riepilogo di conferma, le buste paga riconosciute vengono "
            "aggiunte automaticamente; i file non riconosciuti vengono segnalati e vanno "
            "controllati sul PDF originale.",
            self,
        )
        etichetta_carica_pdf.setWordWrap(True)

        # Barra orizzontale compatta (pulsante + spiegazione) invece di un blocco verticale:
        # occupa poco spazio in alto, lasciando la maggior parte della finestra alla tabella.
        layout_gruppo = QHBoxLayout(gruppo)
        layout_gruppo.setSpacing(16)
        layout_gruppo.addWidget(self.pulsante_carica_pdf, stretch=0)
        layout_gruppo.addWidget(etichetta_carica_pdf, stretch=1)

        layout_esterno = QHBoxLayout(self)
        layout_esterno.setContentsMargins(0, 0, 0, 0)
        layout_esterno.addWidget(gruppo)

    def _gestisci_click_carica_pdf(self) -> None:
        percorsi_scelti, _ = QFileDialog.getOpenFileNames(
            self, "Seleziona uno o più PDF di cedolino", "", "File PDF (*.pdf)"
        )
        if not percorsi_scelti:
            return
        self._importa_pdf([Path(percorso) for percorso in percorsi_scelti])

    def _importa_pdf(self, percorsi: list[Path]) -> None:
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

        righe_riepilogo = "\n".join(
            f"- {busta.mese.nome_italiano} {busta.anno}: livello {busta.livello.value}, "
            f"retribuzione {busta.totale_elementi_retributivi:,.2f} €"
            for busta in importate
        )
        messaggio = f"Verranno aggiunte {len(importate)} buste paga:\n\n{righe_riepilogo}"
        if errori:
            dettaglio_errori = "\n".join(f"- {percorso.name}: {msg}" for percorso, msg in errori)
            messaggio += (
                f"\n\n{len(errori)} file non riconosciuti (non verranno inseriti):\n{dettaglio_errori}"
            )
        messaggio += "\n\nConfermi l'inserimento?"

        risposta = QMessageBox.question(
            self,
            "Conferma importazione",
            messaggio,
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )
        if risposta != QMessageBox.StandardButton.Yes:
            return

        for busta in importate:
            self.busta_paga_inserita.emit(busta)
