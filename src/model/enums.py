"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Enumerazioni di dominio per i mesi dell'anno e i livelli di inquadramento
             del CCNL Metalmeccanico Industria (Confindustria).
"""

from __future__ import annotations

from enum import Enum, IntEnum


class Mese(IntEnum):
    """Mese di competenza di una busta paga (valore = numero del mese, 1-12)."""

    GENNAIO = 1
    FEBBRAIO = 2
    MARZO = 3
    APRILE = 4
    MAGGIO = 5
    GIUGNO = 6
    LUGLIO = 7
    AGOSTO = 8
    SETTEMBRE = 9
    OTTOBRE = 10
    NOVEMBRE = 11
    DICEMBRE = 12

    @property
    def nome_italiano(self) -> str:
        return _NOMI_MESI[self]


_NOMI_MESI: dict[Mese, str] = {
    Mese.GENNAIO: "Gennaio",
    Mese.FEBBRAIO: "Febbraio",
    Mese.MARZO: "Marzo",
    Mese.APRILE: "Aprile",
    Mese.MAGGIO: "Maggio",
    Mese.GIUGNO: "Giugno",
    Mese.LUGLIO: "Luglio",
    Mese.AGOSTO: "Agosto",
    Mese.SETTEMBRE: "Settembre",
    Mese.OTTOBRE: "Ottobre",
    Mese.NOVEMBRE: "Novembre",
    Mese.DICEMBRE: "Dicembre",
}


class LivelloCCNL(Enum):
    """Livelli di inquadramento previsti dal CCNL Metalmeccanico Industria."""

    D3 = "D3"
    D2 = "D2"
    D1 = "D1"
    C3 = "C3"
    C2 = "C2"
    C1 = "C1"
    B3 = "B3"
    B2 = "B2"
    B1 = "B1"
    A3 = "A3"
    A2 = "A2"
    A1 = "A1"

    def __str__(self) -> str:
        return self.value
