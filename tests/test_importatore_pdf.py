"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Test unitari per la conversione dei dati estratti da un PDF di cedolino
             (ImportatorePdfBustaPaga) in un oggetto BustaPaga, e per le validazioni di errore
             che non richiedono di contattare l'API di Gemini.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from src.model.enums import LivelloCCNL, Mese
from src.model.importatore_pdf import ErroreImportazionePdf, ImportatorePdfBustaPaga


def _dati_validi(**override: object) -> dict:
    dati = {
        "mese": 3,
        "anno": 2026,
        "livello": "C2",
        "comune_residenza": "Milano",
        "totale_elementi_retributivi": 2_200.0,
        "ore_ordinarie": 168.0,
        "straordinari": 100.0,
        "fringe_benefit": 50.0,
        "contributi_inps_dipendente": 202.18,
        "contributi_cometa_dipendente": 20.0,
        "contributi_cometa_azienda": 30.0,
        "irpef_pagata": 320.0,
        "addizionale_regionale_pagata": 25.0,
        "addizionale_comunale_pagata": 15.0,
        "conguaglio_730": -50.0,
    }
    dati.update(override)
    return dati


def test_costruisci_busta_paga_mappa_tutti_i_campi() -> None:
    busta = ImportatorePdfBustaPaga._costruisci_busta_paga(_dati_validi())

    assert busta.mese == Mese.MARZO
    assert busta.anno == 2026
    assert busta.livello == LivelloCCNL.C2
    assert busta.comune_residenza == "Milano"
    assert busta.totale_elementi_retributivi == 2_200.0
    assert busta.ore_ordinarie == 168.0
    assert busta.straordinari == 100.0
    assert busta.fringe_benefit == 50.0
    assert busta.contributi_inps_dipendente == 202.18
    assert busta.contributi_cometa_dipendente == 20.0
    assert busta.contributi_cometa_azienda == 30.0
    assert busta.irpef_pagata == 320.0
    assert busta.addizionale_regionale_pagata == 25.0
    assert busta.addizionale_comunale_pagata == 15.0
    assert busta.conguaglio_730 == -50.0


def test_costruisci_busta_paga_usa_zero_per_campi_opzionali_assenti() -> None:
    dati_minimi = {
        "mese": 1,
        "anno": 2026,
        "livello": "A1",
        "totale_elementi_retributivi": 1_800.0,
    }

    busta = ImportatorePdfBustaPaga._costruisci_busta_paga(dati_minimi)

    assert busta.comune_residenza == ""
    assert busta.straordinari == 0.0
    assert busta.irpef_pagata == 0.0


def test_costruisci_busta_paga_solleva_errore_su_livello_non_valido() -> None:
    with pytest.raises(ErroreImportazionePdf):
        ImportatorePdfBustaPaga._costruisci_busta_paga(_dati_validi(livello="ZZ"))


def test_costruisci_busta_paga_solleva_errore_su_mese_non_valido() -> None:
    with pytest.raises(ErroreImportazionePdf):
        ImportatorePdfBustaPaga._costruisci_busta_paga(_dati_validi(mese=13))


def test_costruisci_busta_paga_solleva_errore_su_campo_obbligatorio_mancante() -> None:
    dati_incompleti = _dati_validi()
    del dati_incompleti["totale_elementi_retributivi"]

    with pytest.raises(ErroreImportazionePdf):
        ImportatorePdfBustaPaga._costruisci_busta_paga(dati_incompleti)


def test_estrai_busta_paga_richiede_api_key(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)

    percorso_pdf = tmp_path / "cedolino.pdf"
    percorso_pdf.write_bytes(b"%PDF-1.4")

    with pytest.raises(ErroreImportazionePdf, match="API key"):
        ImportatorePdfBustaPaga().estrai_busta_paga(percorso_pdf)


def test_estrai_busta_paga_richiede_file_esistente() -> None:
    with pytest.raises(ErroreImportazionePdf, match="non trovato"):
        ImportatorePdfBustaPaga(api_key="chiave-di-test").estrai_busta_paga(Path("non_esiste.pdf"))
