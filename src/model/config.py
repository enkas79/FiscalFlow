"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Parametri fiscali normativi (anno d'imposta 2026): scaglioni IRPEF nazionali,
             detrazione da lavoro dipendente, riduzione del cuneo fiscale e aliquote delle
             addizionali regionali/comunali. Il modulo è isolato da CalcolatoreFiscale
             affinché un aggiornamento normativo (es. una nuova Legge di Bilancio) richieda
             di modificare solo questi dati, senza toccare la logica di calcolo.
"""

from __future__ import annotations

from dataclasses import dataclass

# Chiave di fallback usata per regioni/comuni non ancora censiti nelle tabelle sottostanti.
CHIAVE_FALLBACK: str = "_DEFAULT_"

ANNO_FISCALE_RIFERIMENTO: int = 2026


@dataclass(frozen=True, slots=True)
class ScaglioneAliquota:
    """Scaglione generico di un'imposta progressiva (IRPEF nazionale o addizionale regionale)."""

    limite_inferiore: float
    limite_superiore: float | None  # None = nessun limite superiore (ultimo scaglione)
    aliquota: float  # es. 0.23 per il 23%


@dataclass(frozen=True, slots=True)
class ScaglioneDetrazione:
    """
    Scaglione della formula di detrazione da lavoro dipendente (art. 13, c.1, TUIR):

        detrazione = base + numeratore * (limite_superiore - reddito) / denominatore

    Impostare numeratore=0 (denominatore qualsiasi != 0) per un importo fisso, senza
    riduzione all'interno dello scaglione.
    """

    limite_inferiore: float
    limite_superiore: float
    base: float
    numeratore: float
    denominatore: float


@dataclass(frozen=True, slots=True)
class ParametriCuneoFiscale:
    """
    Ulteriore riduzione IRPEF ("cuneo fiscale") riconosciuta in una specifica fascia di
    reddito:

        riduzione = numeratore * (soglia_massima - reddito) / denominatore

    valida solo per soglia_minima <= reddito <= soglia_massima; zero al di fuori.
    """

    soglia_minima: float
    soglia_massima: float
    numeratore: float
    denominatore: float


@dataclass(frozen=True, slots=True)
class DatiFiscaliComune:
    """Regione di appartenenza e aliquota dell'addizionale comunale di un comune."""

    regione: str
    aliquota_addizionale_comunale: float
    soglia_esenzione_comunale: float = 0.0


# ---------------------------------------------------------------------------
# IRPEF nazionale: scaglioni e aliquote (Legge di Bilancio 2026).
# ---------------------------------------------------------------------------
SCAGLIONI_IRPEF: tuple[ScaglioneAliquota, ...] = (
    ScaglioneAliquota(0.0, 28_000.0, 0.23),
    ScaglioneAliquota(28_000.0, 50_000.0, 0.33),
    ScaglioneAliquota(50_000.0, None, 0.43),
)


# ---------------------------------------------------------------------------
# Detrazione da lavoro dipendente (art. 13, c.1, TUIR).
# ---------------------------------------------------------------------------
SCAGLIONI_DETRAZIONE_LAVORO_DIPENDENTE: tuple[ScaglioneDetrazione, ...] = (
    ScaglioneDetrazione(0.0, 15_000.0, base=1_955.0, numeratore=0.0, denominatore=1.0),
    ScaglioneDetrazione(15_000.0, 28_000.0, base=1_910.0, numeratore=1_190.0, denominatore=13_000.0),
    ScaglioneDetrazione(28_000.0, 50_000.0, base=65.0, numeratore=1_910.0, denominatore=22_000.0),
)


# ---------------------------------------------------------------------------
# Riduzione del cuneo fiscale per la fascia di reddito 32.000 - 40.000 €.
# ---------------------------------------------------------------------------
PARAMETRI_CUNEO_FISCALE: ParametriCuneoFiscale = ParametriCuneoFiscale(
    soglia_minima=32_000.0,
    soglia_massima=40_000.0,
    numeratore=1_000.0,
    denominatore=8_000.0,
)


# ---------------------------------------------------------------------------
# Addizionale regionale IRPEF: scaglioni per regione. La chiave CHIAVE_FALLBACK è
# usata come aliquota media nazionale di fallback per le regioni non censite.
# ---------------------------------------------------------------------------
SCAGLIONI_ADDIZIONALE_REGIONALE: dict[str, tuple[ScaglioneAliquota, ...]] = {
    "Lombardia": (ScaglioneAliquota(0.0, None, 0.0123),),
    "Lazio": (
        ScaglioneAliquota(0.0, 15_000.0, 0.0173),
        ScaglioneAliquota(15_000.0, 28_000.0, 0.0273),
        ScaglioneAliquota(28_000.0, 50_000.0, 0.0293),
        ScaglioneAliquota(50_000.0, None, 0.0333),
    ),
    "Piemonte": (ScaglioneAliquota(0.0, None, 0.0162),),
    "Veneto": (ScaglioneAliquota(0.0, None, 0.0123),),
    "Emilia-Romagna": (
        ScaglioneAliquota(0.0, 15_000.0, 0.0133),
        ScaglioneAliquota(15_000.0, 28_000.0, 0.0193),
        ScaglioneAliquota(28_000.0, 50_000.0, 0.0203),
        ScaglioneAliquota(50_000.0, None, 0.0233),
    ),
    CHIAVE_FALLBACK: (ScaglioneAliquota(0.0, None, 0.0173),),
}


# ---------------------------------------------------------------------------
# Addizionale comunale IRPEF: aliquota (ed eventuale soglia di esenzione) per comune,
# con la relativa regione di appartenenza. La chiave CHIAVE_FALLBACK è usata come
# fallback per i comuni non ancora censiti in questa tabella.
# ---------------------------------------------------------------------------
DATI_FISCALI_COMUNI: dict[str, DatiFiscaliComune] = {
    "Milano": DatiFiscaliComune(regione="Lombardia", aliquota_addizionale_comunale=0.008),
    "Brescia": DatiFiscaliComune(regione="Lombardia", aliquota_addizionale_comunale=0.008),
    "Roma": DatiFiscaliComune(regione="Lazio", aliquota_addizionale_comunale=0.009),
    "Torino": DatiFiscaliComune(regione="Piemonte", aliquota_addizionale_comunale=0.008),
    "Bologna": DatiFiscaliComune(regione="Emilia-Romagna", aliquota_addizionale_comunale=0.008),
    "Verona": DatiFiscaliComune(regione="Veneto", aliquota_addizionale_comunale=0.008),
    CHIAVE_FALLBACK: DatiFiscaliComune(regione=CHIAVE_FALLBACK, aliquota_addizionale_comunale=0.008),
}


def get_dati_fiscali_comune(comune: str) -> DatiFiscaliComune:
    """Restituisce i dati fiscali del comune indicato, con fallback sul comune di default."""
    return DATI_FISCALI_COMUNI.get(comune, DATI_FISCALI_COMUNI[CHIAVE_FALLBACK])


def get_scaglioni_addizionale_regionale(regione: str) -> tuple[ScaglioneAliquota, ...]:
    """Restituisce gli scaglioni dell'addizionale regionale per la regione indicata."""
    return SCAGLIONI_ADDIZIONALE_REGIONALE.get(regione, SCAGLIONI_ADDIZIONALE_REGIONALE[CHIAVE_FALLBACK])


def get_comuni_disponibili() -> list[str]:
    """Elenco dei comuni censiti, esclusa la voce di fallback, in ordine alfabetico."""
    return sorted(comune for comune in DATI_FISCALI_COMUNI if comune != CHIAVE_FALLBACK)
