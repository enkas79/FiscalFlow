"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Test unitari di base per la logica di calcolo fiscale di CalcolatoreFiscale.
"""

from __future__ import annotations

from src.model.busta_paga import BustaPaga
from src.model.calcolatore_fiscale import CalcolatoreFiscale
from src.model.enums import LivelloCCNL, Mese


def _crea_busta(mese: Mese, totale_elementi: float = 2_000.0) -> BustaPaga:
    return BustaPaga(
        mese=mese,
        anno=2026,
        livello=LivelloCCNL.C3,
        totale_elementi_retributivi=totale_elementi,
        contributi_inps_dipendente=round(totale_elementi * 0.0919, 2),
        irpef_pagata=300.0,
    )


def test_irpef_lorda_primo_scaglione() -> None:
    assert CalcolatoreFiscale.calcola_irpef_lorda(20_000) == 4_600.0


def test_irpef_lorda_scaglioni_multipli() -> None:
    attesa = 28_000 * 0.23 + 2_000 * 0.35
    assert CalcolatoreFiscale.calcola_irpef_lorda(30_000) == round(attesa, 2)


def test_detrazione_decresce_con_reddito() -> None:
    detrazione_bassa = CalcolatoreFiscale.calcola_detrazione_lavoro_dipendente(14_000)
    detrazione_alta = CalcolatoreFiscale.calcola_detrazione_lavoro_dipendente(40_000)
    assert detrazione_bassa > detrazione_alta > 0


def test_detrazione_nulla_oltre_soglia() -> None:
    assert CalcolatoreFiscale.calcola_detrazione_lavoro_dipendente(60_000) == 0.0


def test_ral_proiettata_include_tredicesima_su_annualita_completa() -> None:
    buste = [_crea_busta(Mese(m)) for m in range(1, 13)]
    ral = CalcolatoreFiscale.calcola_ral_proiettata(buste)
    assert ral == round(2_000 * 12 + 2_000, 2)


def test_proiezione_fine_anno_restituisce_esito_coerente() -> None:
    buste = [_crea_busta(Mese(m)) for m in range(1, 7)]
    risultato = CalcolatoreFiscale.calcola_proiezione_fine_anno(buste)

    assert risultato.ral_stimata > 0
    assert risultato.esito in {"A CREDITO", "A DEBITO", "PARI"}
    assert risultato.conguaglio == round(risultato.totale_tasse_dovute - risultato.totale_tasse_pagate, 2)


def test_proiezione_senza_buste_e_neutra() -> None:
    risultato = CalcolatoreFiscale.calcola_proiezione_fine_anno([])
    assert risultato.ral_stimata == 0.0
    assert risultato.esito == "PARI"
