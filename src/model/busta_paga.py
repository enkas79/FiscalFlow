"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Modello dati che rappresenta una singola busta paga mensile e le grandezze
             derivate immediate (retribuzione lorda, imponibili, netto percepito).
"""

from __future__ import annotations

from dataclasses import dataclass

from .enums import LivelloCCNL, Mese


@dataclass(slots=True)
class BustaPaga:
    """Rappresenta i dati fondamentali di un cedolino paga mensile di un dipendente."""

    mese: Mese
    anno: int
    livello: LivelloCCNL

    # Paga base + contingenza + scatti di anzianità + superminimo, ecc.
    totale_elementi_retributivi: float
    ore_ordinarie: float = 0.0
    straordinari: float = 0.0
    fringe_benefit: float = 0.0

    contributi_inps_dipendente: float = 0.0
    contributi_cometa_dipendente: float = 0.0
    contributi_cometa_azienda: float = 0.0

    irpef_pagata: float = 0.0
    addizionale_regionale_pagata: float = 0.0
    addizionale_comunale_pagata: float = 0.0

    # Conguaglio da modello 730 gestito in busta paga: positivo = rimborso al
    # dipendente, negativo = trattenuta.
    conguaglio_730: float = 0.0

    @property
    def retribuzione_lorda(self) -> float:
        """Retribuzione lorda del mese (elementi fissi contrattuali + straordinari)."""
        return self.totale_elementi_retributivi + self.straordinari

    @property
    def imponibile_previdenziale(self) -> float:
        """Imponibile INPS del mese."""
        return self.retribuzione_lorda + self.fringe_benefit

    @property
    def imponibile_fiscale(self) -> float:
        """Imponibile IRPEF del mese: imponibile INPS al netto dei contributi deducibili."""
        contributi_deducibili = self.contributi_inps_dipendente + self.contributi_cometa_dipendente
        return max(0.0, self.imponibile_previdenziale - contributi_deducibili)

    @property
    def totale_tasse_pagate(self) -> float:
        """Somma di IRPEF trattenuta e addizionali regionale/comunale trattenute nel mese."""
        return self.irpef_pagata + self.addizionale_regionale_pagata + self.addizionale_comunale_pagata

    @property
    def netto_percepito(self) -> float:
        """Stima del netto in busta per il mese."""
        return (
            self.retribuzione_lorda
            + self.fringe_benefit
            + self.conguaglio_730
            - self.contributi_inps_dipendente
            - self.contributi_cometa_dipendente
            - self.totale_tasse_pagate
        )

    @property
    def chiave_periodo(self) -> tuple[int, int]:
        """Chiave ordinabile (anno, mese) utile per l'ordinamento cronologico."""
        return self.anno, self.mese.value
