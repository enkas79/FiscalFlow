"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Motore di calcolo fiscale: progressivi mensili, scaglioni IRPEF, detrazione
             teorica da lavoro dipendente, proiezione della RAL di fine anno (con gestione
             dei cambi di livello contrattuale), stima della tredicesima e calcolo del
             conguaglio fiscale finale.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from .busta_paga import BustaPaga


@dataclass(frozen=True, slots=True)
class ScaglioneIRPEF:
    """Rappresenta uno scaglione della tassazione IRPEF progressiva per scaglioni."""

    limite_inferiore: float
    limite_superiore: float | None  # None = nessun limite superiore (ultimo scaglione)
    aliquota: float  # es. 0.23 per il 23%


@dataclass(frozen=True, slots=True)
class RisultatoProiezione:
    """Esito della proiezione fiscale di fine anno per un dipendente."""

    ral_stimata: float
    tredicesima_stimata: float
    imponibile_fiscale_annuo: float
    irpef_lorda_dovuta: float
    detrazioni_lavoro_dipendente: float
    irpef_netta_dovuta: float
    addizionale_regionale_dovuta: float
    addizionale_comunale_dovuta: float
    totale_tasse_dovute: float
    totale_tasse_pagate: float
    # totale_tasse_dovute - totale_tasse_pagate:
    #   positivo -> il dipendente deve versare la differenza (conguaglio A DEBITO)
    #   negativo -> il dipendente ha già versato più del dovuto (conguaglio A CREDITO)
    conguaglio: float

    @property
    def esito(self) -> str:
        if self.conguaglio > 0.005:
            return "A DEBITO"
        if self.conguaglio < -0.005:
            return "A CREDITO"
        return "PARI"


class CalcolatoreFiscale:
    """Incapsula la logica di calcolo fiscale e previdenziale, priva di stato mutabile."""

    # Scaglioni IRPEF nazionali correnti (tre aliquote, D.Lgs. 216/2023 e succ.).
    SCAGLIONI_IRPEF: tuple[ScaglioneIRPEF, ...] = (
        ScaglioneIRPEF(0.0, 28_000.0, 0.23),
        ScaglioneIRPEF(28_000.0, 50_000.0, 0.35),
        ScaglioneIRPEF(50_000.0, None, 0.43),
    )

    # Aliquote medie di riferimento: vanno sostituite con quelle reali di
    # residenza/domicilio fiscale del dipendente (variano per comune/regione).
    ALIQUOTA_ADDIZIONALE_REGIONALE_DEFAULT: float = 0.0173
    ALIQUOTA_ADDIZIONALE_COMUNALE_DEFAULT: float = 0.008

    # ------------------------------------------------------------------
    # Utilità e progressivi
    # ------------------------------------------------------------------

    @staticmethod
    def ordina_cronologicamente(buste: Sequence[BustaPaga]) -> list[BustaPaga]:
        return sorted(buste, key=lambda b: b.chiave_periodo)

    @classmethod
    def calcola_progressivo_imponibile_previdenziale(cls, buste: Sequence[BustaPaga]) -> float:
        return round(sum(b.imponibile_previdenziale for b in buste), 2)

    @classmethod
    def calcola_progressivo_imponibile_fiscale(cls, buste: Sequence[BustaPaga]) -> float:
        return round(sum(b.imponibile_fiscale for b in buste), 2)

    @classmethod
    def calcola_progressivo_tasse_pagate(cls, buste: Sequence[BustaPaga]) -> float:
        return round(sum(b.totale_tasse_pagate for b in buste), 2)

    # ------------------------------------------------------------------
    # IRPEF: scaglioni e detrazioni
    # ------------------------------------------------------------------

    @classmethod
    def calcola_irpef_lorda(cls, imponibile_annuo: float) -> float:
        """Applica gli scaglioni IRPEF in modo progressivo (non una singola aliquota marginale)."""
        if imponibile_annuo <= 0:
            return 0.0

        irpef = 0.0
        for scaglione in cls.SCAGLIONI_IRPEF:
            if imponibile_annuo <= scaglione.limite_inferiore:
                break
            limite_sup = (
                scaglione.limite_superiore if scaglione.limite_superiore is not None else imponibile_annuo
            )
            imponibile_nello_scaglione = min(imponibile_annuo, limite_sup) - scaglione.limite_inferiore
            irpef += imponibile_nello_scaglione * scaglione.aliquota
        return round(irpef, 2)

    @classmethod
    def calcola_detrazione_lavoro_dipendente(
        cls, imponibile_annuo: float, giorni_lavorati: int = 365
    ) -> float:
        """
        Detrazione teorica per redditi da lavoro dipendente (art. 13, comma 1, TUIR),
        rapportata ai giorni di lavoro nell'anno (365 per un rapporto sull'intero anno).
        """
        if imponibile_annuo <= 0:
            return 0.0

        if imponibile_annuo <= 15_000:
            detrazione = 1_955.0
        elif imponibile_annuo <= 28_000:
            detrazione = 1_910.0 + 1_190.0 * (28_000 - imponibile_annuo) / 13_000
        elif imponibile_annuo <= 50_000:
            detrazione = 1_910.0 * (50_000 - imponibile_annuo) / 22_000
        else:
            detrazione = 0.0

        rapporto_giorni = giorni_lavorati / 365
        return round(max(0.0, detrazione) * rapporto_giorni, 2)

    @classmethod
    def calcola_irpef_netta_annua(cls, imponibile_annuo: float, giorni_lavorati: int = 365) -> float:
        irpef_lorda = cls.calcola_irpef_lorda(imponibile_annuo)
        detrazione = cls.calcola_detrazione_lavoro_dipendente(imponibile_annuo, giorni_lavorati)
        return round(max(0.0, irpef_lorda - detrazione), 2)

    # ------------------------------------------------------------------
    # Proiezione RAL, tredicesima e conguaglio
    # ------------------------------------------------------------------

    @classmethod
    def stima_tredicesima_fine_anno(
        cls,
        buste_consuntivate: Sequence[BustaPaga],
        retribuzione_mensile_residua: float,
        numero_mesi_mancanti: int,
    ) -> float:
        """
        Tredicesima mensilità = rateo di 1/12 della retribuzione contrattuale per ogni
        mese di anzianità maturato nell'anno (mesi già consuntivati + mesi residui
        proiettati all'ultima retribuzione nota, che riflette eventuali passaggi di livello).
        """
        rateo_consuntivato = sum(b.totale_elementi_retributivi for b in buste_consuntivate) / 12
        rateo_proiettato = (retribuzione_mensile_residua * numero_mesi_mancanti) / 12
        return round(rateo_consuntivato + rateo_proiettato, 2)

    @classmethod
    def calcola_ral_proiettata(
        cls,
        buste_consuntivate: Sequence[BustaPaga],
        retribuzione_mensile_residua: float | None = None,
    ) -> float:
        """
        Proietta la Retribuzione Annua Lorda di fine anno.

        I mesi già consuntivati riflettono automaticamente eventuali variazioni di
        livello contrattuale avvenute in corso d'anno (es. passaggio da C3 a B1), perché
        ogni ``BustaPaga`` porta con sé la propria retribuzione effettiva. Per i mesi
        mancanti fino a dicembre si applica ``retribuzione_mensile_residua`` (di norma
        la retribuzione dell'ultimo livello raggiunto), o in sua assenza l'ultima
        retribuzione mensile nota. Include la tredicesima stimata.
        """
        buste = cls.ordina_cronologicamente(buste_consuntivate)
        if not buste:
            return 0.0

        mesi_consuntivati = {b.mese.value for b in buste}
        numero_mesi_mancanti = 12 - len(mesi_consuntivati)

        retribuzione_proiezione = (
            retribuzione_mensile_residua
            if retribuzione_mensile_residua is not None
            else buste[-1].totale_elementi_retributivi
        )

        totale_retribuzioni_ordinarie = sum(b.retribuzione_lorda for b in buste) + (
            retribuzione_proiezione * numero_mesi_mancanti
        )
        tredicesima_stimata = cls.stima_tredicesima_fine_anno(
            buste, retribuzione_proiezione, numero_mesi_mancanti
        )
        return round(totale_retribuzioni_ordinarie + tredicesima_stimata, 2)

    @classmethod
    def calcola_proiezione_fine_anno(
        cls,
        buste_consuntivate: Sequence[BustaPaga],
        retribuzione_mensile_residua: float | None = None,
        giorni_lavorati_anno: int = 365,
        aliquota_addizionale_regionale: float = ALIQUOTA_ADDIZIONALE_REGIONALE_DEFAULT,
        aliquota_addizionale_comunale: float = ALIQUOTA_ADDIZIONALE_COMUNALE_DEFAULT,
    ) -> RisultatoProiezione:
        """Calcola la proiezione fiscale completa di fine anno, incluso il conguaglio finale."""
        buste = cls.ordina_cronologicamente(buste_consuntivate)

        if not buste:
            return RisultatoProiezione(
                ral_stimata=0.0,
                tredicesima_stimata=0.0,
                imponibile_fiscale_annuo=0.0,
                irpef_lorda_dovuta=0.0,
                detrazioni_lavoro_dipendente=0.0,
                irpef_netta_dovuta=0.0,
                addizionale_regionale_dovuta=0.0,
                addizionale_comunale_dovuta=0.0,
                totale_tasse_dovute=0.0,
                totale_tasse_pagate=0.0,
                conguaglio=0.0,
            )

        numero_mesi_mancanti = 12 - len({b.mese.value for b in buste})
        retribuzione_proiezione = (
            retribuzione_mensile_residua
            if retribuzione_mensile_residua is not None
            else buste[-1].totale_elementi_retributivi
        )

        ral_stimata = cls.calcola_ral_proiettata(buste, retribuzione_proiezione)
        tredicesima_stimata = cls.stima_tredicesima_fine_anno(
            buste, retribuzione_proiezione, numero_mesi_mancanti
        )

        imponibile_fiscale_consuntivato = cls.calcola_progressivo_imponibile_fiscale(buste)
        # Approssimazione: per i mesi non ancora consuntivati si stima l'imponibile
        # fiscale residuo pari alla retribuzione lorda proiettata (senza dettaglio dei
        # contributi non ancora noti).
        imponibile_fiscale_residuo = retribuzione_proiezione * numero_mesi_mancanti
        imponibile_fiscale_annuo = round(
            imponibile_fiscale_consuntivato + imponibile_fiscale_residuo + tredicesima_stimata, 2
        )

        irpef_lorda = cls.calcola_irpef_lorda(imponibile_fiscale_annuo)
        detrazioni = cls.calcola_detrazione_lavoro_dipendente(imponibile_fiscale_annuo, giorni_lavorati_anno)
        irpef_netta_dovuta = round(max(0.0, irpef_lorda - detrazioni), 2)

        addizionale_regionale_dovuta = round(imponibile_fiscale_annuo * aliquota_addizionale_regionale, 2)
        addizionale_comunale_dovuta = round(imponibile_fiscale_annuo * aliquota_addizionale_comunale, 2)

        totale_tasse_dovute = round(
            irpef_netta_dovuta + addizionale_regionale_dovuta + addizionale_comunale_dovuta, 2
        )
        totale_tasse_pagate = cls.calcola_progressivo_tasse_pagate(buste)

        conguaglio = round(totale_tasse_dovute - totale_tasse_pagate, 2)

        return RisultatoProiezione(
            ral_stimata=ral_stimata,
            tredicesima_stimata=tredicesima_stimata,
            imponibile_fiscale_annuo=imponibile_fiscale_annuo,
            irpef_lorda_dovuta=irpef_lorda,
            detrazioni_lavoro_dipendente=detrazioni,
            irpef_netta_dovuta=irpef_netta_dovuta,
            addizionale_regionale_dovuta=addizionale_regionale_dovuta,
            addizionale_comunale_dovuta=addizionale_comunale_dovuta,
            totale_tasse_dovute=totale_tasse_dovute,
            totale_tasse_pagate=totale_tasse_pagate,
            conguaglio=conguaglio,
        )
