"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Controller applicativo che collega gli eventi della View al Model,
             orchestrando l'inserimento delle buste paga e l'aggiornamento dei calcoli.
"""

from __future__ import annotations

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

    def _gestisci_nuova_busta_paga(self, busta: BustaPaga) -> None:
        self._gestore.aggiungi_busta_paga(busta)
        self._anno_corrente = busta.anno
        self._aggiorna_vista()

    def _aggiorna_vista(self) -> None:
        if self._anno_corrente is None:
            return

        righe_progressivo = self._gestore.calcola_progressivi(self._anno_corrente)
        self._finestra.tabella_riepilogo.aggiorna_righe(righe_progressivo)

        risultato_proiezione = self._gestore.calcola_proiezione_fine_anno(self._anno_corrente)
        self._finestra.pannello_proiezione.aggiorna_proiezione(risultato_proiezione)
