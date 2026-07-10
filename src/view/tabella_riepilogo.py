"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Tabella riassuntiva delle buste paga inserite con i relativi progressivi
             mensili (imponibile INPS, imponibile fiscale, tasse pagate, netto).
"""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QAbstractItemView, QTableWidget, QTableWidgetItem, QWidget

from ..model.archivio import RigaProgressivo

INTESTAZIONI: tuple[str, ...] = (
    "Mese",
    "Livello",
    "Retribuzione lorda (€)",
    "Imp. INPS progr. (€)",
    "Imp. fiscale progr. (€)",
    "Tasse pagate progr. (€)",
    "TFR maturato progr. (€)",
    "Netto percepito (€)",
)


class TabellaRiepilogoBustePaga(QTableWidget):
    """Vista tabellare dei mesi inseriti con i relativi progressivi cumulati."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(0, len(INTESTAZIONI), parent)
        self.setHorizontalHeaderLabels(INTESTAZIONI)
        self.setEditTriggers(QAbstractItemView.EditTrigger.NoEditTriggers)
        self.setSelectionBehavior(QAbstractItemView.SelectionBehavior.SelectRows)
        self.horizontalHeader().setStretchLastSection(True)

    def aggiorna_righe(self, righe_progressivo: list[RigaProgressivo]) -> None:
        """Ripopola la tabella con le righe di progressivo fornite dal controller."""
        self.setRowCount(len(righe_progressivo))
        for indice_riga, riga in enumerate(righe_progressivo):
            busta = riga.busta
            valori = (
                f"{busta.mese.nome_italiano} {busta.anno}",
                busta.livello.value,
                f"{busta.retribuzione_lorda:,.2f}",
                f"{riga.imponibile_previdenziale_progressivo:,.2f}",
                f"{riga.imponibile_fiscale_progressivo:,.2f}",
                f"{riga.totale_tasse_pagate_progressivo:,.2f}",
                f"{riga.tfr_maturato_progressivo:,.2f}",
                f"{busta.netto_percepito:,.2f}",
            )
            for indice_colonna, valore in enumerate(valori):
                item = QTableWidgetItem(valore)
                item.setTextAlignment(Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter)
                self.setItem(indice_riga, indice_colonna, item)
