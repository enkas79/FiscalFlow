"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Test unitari di base per la logica di calcolo fiscale di CalcolatoreFiscale
             e per i parametri normativi definiti in config.py.
"""

from __future__ import annotations

from src.model import config
from src.model.busta_paga import BustaPaga
from src.model.calcolatore_fiscale import CalcolatoreFiscale
from src.model.enums import LivelloCCNL, Mese


def _crea_busta(mese: Mese, totale_elementi: float = 2_000.0, comune: str = "Milano") -> BustaPaga:
    return BustaPaga(
        mese=mese,
        anno=2026,
        livello=LivelloCCNL.C3,
        totale_elementi_retributivi=totale_elementi,
        comune_residenza=comune,
        contributi_inps_dipendente=round(totale_elementi * 0.0919, 2),
        irpef_pagata=300.0,
    )


def test_irpef_lorda_primo_scaglione() -> None:
    assert CalcolatoreFiscale.calcola_irpef_lorda(20_000) == 4_600.0


def test_irpef_lorda_scaglioni_multipli_con_aliquota_33_percento() -> None:
    attesa = 28_000 * 0.23 + 2_000 * 0.33
    assert CalcolatoreFiscale.calcola_irpef_lorda(30_000) == round(attesa, 2)


def test_irpef_lorda_terzo_scaglione_43_percento() -> None:
    attesa = 28_000 * 0.23 + 22_000 * 0.33 + 5_000 * 0.43
    assert CalcolatoreFiscale.calcola_irpef_lorda(55_000) == round(attesa, 2)


def test_detrazione_decresce_con_reddito() -> None:
    detrazione_bassa = CalcolatoreFiscale.calcola_detrazione_lavoro_dipendente(14_000)
    detrazione_alta = CalcolatoreFiscale.calcola_detrazione_lavoro_dipendente(40_000)
    assert detrazione_bassa > detrazione_alta > 0


def test_detrazione_fascia_28k_50k_include_i_65_euro_aggiuntivi() -> None:
    # 1910 * (50000 - 35000) / 22000 + 65
    attesa = 1_910.0 * (50_000 - 35_000) / 22_000 + 65.0
    assert CalcolatoreFiscale.calcola_detrazione_lavoro_dipendente(35_000) == round(attesa, 2)


def test_detrazione_nulla_oltre_soglia() -> None:
    assert CalcolatoreFiscale.calcola_detrazione_lavoro_dipendente(60_000) == 0.0


def test_cuneo_fiscale_nullo_fuori_fascia() -> None:
    assert CalcolatoreFiscale.calcola_riduzione_cuneo_fiscale(20_000) == 0.0
    assert CalcolatoreFiscale.calcola_riduzione_cuneo_fiscale(45_000) == 0.0


def test_cuneo_fiscale_dentro_fascia_32k_40k() -> None:
    # 1000 * (40000 - 36000) / 8000 = 500
    assert CalcolatoreFiscale.calcola_riduzione_cuneo_fiscale(36_000) == 500.0


def test_cuneo_fiscale_estremi_fascia() -> None:
    assert CalcolatoreFiscale.calcola_riduzione_cuneo_fiscale(32_000) == 1_000.0
    assert CalcolatoreFiscale.calcola_riduzione_cuneo_fiscale(40_000) == 0.0


def test_addizionale_comunale_usa_aliquota_del_comune() -> None:
    dovuta = CalcolatoreFiscale.calcola_addizionale_comunale_dovuta(30_000, "Roma")
    assert dovuta == round(30_000 * 0.009, 2)


def test_addizionale_comunale_fallback_su_comune_non_censito() -> None:
    dovuta_comune_ignoto = CalcolatoreFiscale.calcola_addizionale_comunale_dovuta(30_000, "Comune Inesistente")
    dovuta_fallback = CalcolatoreFiscale.calcola_addizionale_comunale_dovuta(
        30_000, config.CHIAVE_FALLBACK
    )
    assert dovuta_comune_ignoto == dovuta_fallback


def test_addizionale_regionale_usa_scaglioni_della_regione() -> None:
    dovuta = CalcolatoreFiscale.calcola_addizionale_regionale_dovuta(30_000, "Lazio")
    attesa = 15_000 * 0.0173 + 13_000 * 0.0273 + 2_000 * 0.0293
    assert dovuta == round(attesa, 2)


def test_ral_proiettata_include_tredicesima_su_annualita_completa() -> None:
    buste = [_crea_busta(Mese(m)) for m in range(1, 13)]
    ral = CalcolatoreFiscale.calcola_ral_proiettata(buste)
    assert ral == round(2_000 * 12 + 2_000, 2)


def test_proiezione_fine_anno_usa_automaticamente_il_comune_dell_ultima_busta() -> None:
    buste = [_crea_busta(Mese(m), comune="Roma") for m in range(1, 7)]
    risultato = CalcolatoreFiscale.calcola_proiezione_fine_anno(buste)

    assert risultato.comune_utilizzato == "Roma"
    assert risultato.regione_utilizzata == "Lazio"
    assert risultato.ral_stimata > 0
    assert risultato.esito in {"A CREDITO", "A DEBITO", "PARI"}
    assert risultato.conguaglio == round(risultato.totale_tasse_dovute - risultato.totale_tasse_pagate, 2)


def test_proiezione_fine_anno_rispetta_override_comune() -> None:
    buste = [_crea_busta(Mese(m), comune="Roma") for m in range(1, 4)]
    risultato = CalcolatoreFiscale.calcola_proiezione_fine_anno(buste, comune_residenza="Torino")
    assert risultato.comune_utilizzato == "Torino"
    assert risultato.regione_utilizzata == "Piemonte"


def test_proiezione_senza_buste_e_neutra() -> None:
    risultato = CalcolatoreFiscale.calcola_proiezione_fine_anno([])
    assert risultato.ral_stimata == 0.0
    assert risultato.esito == "PARI"
