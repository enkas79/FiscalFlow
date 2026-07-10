"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Controller applicativo che collega gli eventi della View al Model,
             orchestrando l'inserimento delle buste paga, il salvataggio/apertura
             dell'archivio e l'aggiornamento dei calcoli.
"""

from __future__ import annotations

from pathlib import Path

from PyQt6.QtWidgets import QMessageBox

from ..model.archivio import GestoreBustePaga
from ..model.busta_paga import BustaPaga
from ..view.main_window import MainWindow


class MainController:
    """Coordina il flusso dati tra GestoreBustePaga (Model) e MainWindow (View)."""

    def __init__(self, finestra: MainWindow, gestore: GestoreBustePaga | None = None) -> None:
        self._finestra = finestra
        self._gestore = gestore if gestore is not None else GestoreBustePaga()
        self._anno_corrente: int | None = None

        self._finestra.form_inserimento.busta_paga_inserita.connect(self._gestisci_nuova_busta_paga)
        self._finestra.richiesta_salvataggio_archivio.connect(self._gestisci_salvataggio_archivio)
        self._finestra.richiesta_apertura_archivio.connect(self._gestisci_apertura_archivio)

    def _gestisci_nuova_busta_paga(self, busta: BustaPaga) -> None:
        self._gestore.aggiungi_busta_paga(busta)
        self._anno_corrente = busta.anno
        self._aggiorna_vista()

    def _gestisci_salvataggio_archivio(self, percorso: Path) -> None:
        try:
            self._gestore.salva_su_file(percorso)
        except OSError as errore:
            QMessageBox.critical(self._finestra, "Salvataggio fallito", f"Impossibile salvare l'archivio: {errore}")
            return
        QMessageBox.information(self._finestra, "Archivio salvato", f"Archivio salvato in:\n{percorso}")

    def _gestisci_apertura_archivio(self, percorso: Path) -> None:
        try:
            self._gestore.carica_da_file(percorso)
        except (OSError, ValueError, KeyError, TypeError) as errore:
            QMessageBox.critical(self._finestra, "Apertura fallita", f"Impossibile aprire l'archivio: {errore}")
            return

        anni_disponibili = self._gestore.get_anni_disponibili()
        self._anno_corrente = max(anni_disponibili) if anni_disponibili else None
        self._aggiorna_vista()

    def _aggiorna_vista(self) -> None:
        if self._anno_corrente is None:
            return

        righe_progressivo = self._gestore.calcola_progressivi(self._anno_corrente)
        self._finestra.tabella_riepilogo.aggiorna_righe(righe_progressivo)

        risultato_proiezione = self._gestore.calcola_proiezione_fine_anno(self._anno_corrente)
        self._finestra.pannello_proiezione.aggiorna_proiezione(risultato_proiezione)

        prospetto = self._gestore.calcola_prospetto_annuale(self._anno_corrente)
        self._finestra.pannello_prospetto.aggiorna_prospetto(prospetto)
