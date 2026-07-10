"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Repository in memoria delle buste paga inserite, organizzate per anno
             solare, con calcolo dei progressivi mensili e persistenza su file JSON.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path

from .busta_paga import BustaPaga
from .calcolatore_fiscale import CalcolatoreFiscale, RisultatoProiezione
from .enums import LivelloCCNL, Mese


@dataclass(frozen=True, slots=True)
class RigaProgressivo:
    """Riga di riepilogo mensile con i progressivi calcolati fino a quel mese incluso."""

    busta: BustaPaga
    imponibile_previdenziale_progressivo: float
    imponibile_fiscale_progressivo: float
    totale_tasse_pagate_progressivo: float


class GestoreBustePaga:
    """Aggrega le buste paga di un dipendente per anno solare e ne calcola i progressivi."""

    def __init__(self) -> None:
        self._buste_per_anno: dict[int, list[BustaPaga]] = {}

    def aggiungi_busta_paga(self, busta: BustaPaga) -> None:
        """Inserisce una busta paga; se il mese era già presente lo sostituisce."""
        buste_anno = self._buste_per_anno.setdefault(busta.anno, [])
        buste_anno[:] = [b for b in buste_anno if b.mese != busta.mese]
        buste_anno.append(busta)
        buste_anno.sort(key=lambda b: b.mese.value)

    def rimuovi_busta_paga(self, anno: int, mese: Mese) -> None:
        if anno in self._buste_per_anno:
            self._buste_per_anno[anno] = [b for b in self._buste_per_anno[anno] if b.mese != mese]

    def get_buste_anno(self, anno: int) -> list[BustaPaga]:
        return list(self._buste_per_anno.get(anno, []))

    def get_anni_disponibili(self) -> list[int]:
        return sorted(self._buste_per_anno.keys())

    def calcola_progressivi(self, anno: int) -> list[RigaProgressivo]:
        """Restituisce, per ciascun mese inserito, i progressivi cumulati fino a quel mese."""
        buste = CalcolatoreFiscale.ordina_cronologicamente(self.get_buste_anno(anno))
        righe: list[RigaProgressivo] = []
        accumulato: list[BustaPaga] = []
        for busta in buste:
            accumulato.append(busta)
            righe.append(
                RigaProgressivo(
                    busta=busta,
                    imponibile_previdenziale_progressivo=(
                        CalcolatoreFiscale.calcola_progressivo_imponibile_previdenziale(accumulato)
                    ),
                    imponibile_fiscale_progressivo=(
                        CalcolatoreFiscale.calcola_progressivo_imponibile_fiscale(accumulato)
                    ),
                    totale_tasse_pagate_progressivo=(
                        CalcolatoreFiscale.calcola_progressivo_tasse_pagate(accumulato)
                    ),
                )
            )
        return righe

    def calcola_proiezione_fine_anno(
        self,
        anno: int,
        retribuzione_mensile_residua: float | None = None,
        comune_residenza: str | None = None,
    ) -> RisultatoProiezione:
        return CalcolatoreFiscale.calcola_proiezione_fine_anno(
            self.get_buste_anno(anno),
            retribuzione_mensile_residua,
            comune_residenza=comune_residenza,
        )

    def salva_su_file(self, percorso: Path) -> None:
        dati = {
            str(anno): [
                {**asdict(b), "mese": b.mese.value, "livello": b.livello.value} for b in buste
            ]
            for anno, buste in self._buste_per_anno.items()
        }
        percorso.write_text(json.dumps(dati, indent=2, ensure_ascii=False), encoding="utf-8")

    def carica_da_file(self, percorso: Path) -> None:
        dati = json.loads(percorso.read_text(encoding="utf-8"))
        self._buste_per_anno.clear()
        for anno_str, buste_dict in dati.items():
            buste = [
                BustaPaga(**{**b, "mese": Mese(b["mese"]), "livello": LivelloCCNL(b["livello"])})
                for b in buste_dict
            ]
            self._buste_per_anno[int(anno_str)] = buste
