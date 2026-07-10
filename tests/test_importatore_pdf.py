"""
Autore: Enrico Martini
Versione: 0.0.1
Descrizione: Test unitari per ImportatorePdfBustaPaga: riconoscimento dei campi dal testo
             del cedolino (regex su diciture comuni) e lettura di un PDF reale generato al
             volo, per verificare l'intera pipeline locale (pypdf + regex) senza alcuna
             chiamata di rete.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

from src.model.enums import LivelloCCNL, Mese
from src.model.importatore_pdf import ErroreImportazionePdf, ImportatorePdfBustaPaga

_TESTO_CEDOLINO_ESEMPIO = """
AZIENDA METALMECCANICA SRL
CEDOLINO PAGA - Competenza: Marzo 2026
Dipendente: Mario Rossi
Livello CCNL: C2          Qualifica: Impiegato
Comune di residenza: Milano (MI)

Ore ordinarie: 168,0       Totale competenze: 2.200,00 €
Straordinari: 100,00
Fringe benefit: 50,00

Contributi INPS dipendente: 202,18
Fondo Cometa dipendente: 20,00
Fondo Cometa azienda: 30,00

IRPEF: 320,00
Addizionale regionale: 25,00
Addizionale comunale: 15,00
TFR maturato nel mese: 169,23

Conguaglio 730: -50,00
"""


def _crea_pdf_di_prova(percorso: Path, righe: list[str]) -> None:
    c = canvas.Canvas(str(percorso), pagesize=A4)
    y = 800
    for riga in righe:
        c.drawString(50, y, riga)
        y -= 20
    c.save()


def test_estrai_dati_da_testo_riconosce_tutti_i_campi() -> None:
    dati = ImportatorePdfBustaPaga._estrai_dati_da_testo(_TESTO_CEDOLINO_ESEMPIO)

    assert dati["mese"] == Mese.MARZO
    assert dati["anno"] == 2026
    assert dati["livello"] == LivelloCCNL.C2
    assert dati["comune_residenza"] == "Milano"
    assert dati["totale_elementi_retributivi"] == 2_200.0
    assert dati["ore_ordinarie"] == 168.0
    assert dati["straordinari"] == 100.0
    assert dati["fringe_benefit"] == 50.0
    assert dati["contributi_inps_dipendente"] == 202.18
    assert dati["contributi_cometa_dipendente"] == 20.0
    assert dati["contributi_cometa_azienda"] == 30.0
    assert dati["irpef_pagata"] == 320.0
    assert dati["addizionale_regionale_pagata"] == 25.0
    assert dati["addizionale_comunale_pagata"] == 15.0
    assert dati["quota_tfr_maturata"] == 169.23
    assert dati["conguaglio_730"] == -50.0


def test_costruisci_busta_paga_mappa_i_dati_estratti() -> None:
    dati = ImportatorePdfBustaPaga._estrai_dati_da_testo(_TESTO_CEDOLINO_ESEMPIO)
    busta = ImportatorePdfBustaPaga._costruisci_busta_paga(dati)

    assert busta.mese == Mese.MARZO
    assert busta.anno == 2026
    assert busta.livello == LivelloCCNL.C2
    assert busta.totale_elementi_retributivi == 2_200.0
    assert busta.quota_tfr_maturata == 169.23
    assert busta.conguaglio_730 == -50.0


def test_converti_numero_italiano_gestisce_migliaia_decimali_e_segno() -> None:
    convertitore = ImportatorePdfBustaPaga._converti_numero_italiano
    assert convertitore("1.234,56") == 1_234.56
    assert convertitore("234,56") == 234.56
    assert convertitore("-50,00") == -50.0
    assert convertitore("(50,00)") == -50.0


def test_estrai_busta_paga_da_pdf_reale(tmp_path: Path) -> None:
    percorso_pdf = tmp_path / "cedolino.pdf"
    _crea_pdf_di_prova(percorso_pdf, _TESTO_CEDOLINO_ESEMPIO.strip().splitlines())

    busta = ImportatorePdfBustaPaga().estrai_busta_paga(percorso_pdf)

    assert busta.mese == Mese.MARZO
    assert busta.anno == 2026
    assert busta.livello == LivelloCCNL.C2
    assert busta.comune_residenza == "Milano"
    assert busta.totale_elementi_retributivi == 2_200.0
    assert busta.quota_tfr_maturata == 169.23


def test_estrai_busta_paga_richiede_file_esistente() -> None:
    with pytest.raises(ErroreImportazionePdf, match="non trovato"):
        ImportatorePdfBustaPaga().estrai_busta_paga(Path("non_esiste.pdf"))


def test_estrai_busta_paga_solleva_errore_su_pdf_senza_testo(tmp_path: Path) -> None:
    percorso_pdf = tmp_path / "cedolino_vuoto.pdf"
    _crea_pdf_di_prova(percorso_pdf, [])

    with pytest.raises(ErroreImportazionePdf, match="scansione immagine"):
        ImportatorePdfBustaPaga().estrai_busta_paga(percorso_pdf)


def test_estrai_busta_paga_solleva_errore_su_campi_obbligatori_mancanti(tmp_path: Path) -> None:
    percorso_pdf = tmp_path / "cedolino_incompleto.pdf"
    _crea_pdf_di_prova(percorso_pdf, ["Documento senza i dati richiesti dal cedolino."])

    with pytest.raises(ErroreImportazionePdf, match="dati obbligatori"):
        ImportatorePdfBustaPaga().estrai_busta_paga(percorso_pdf)


def test_cerca_livello_ignora_falsi_positivi_lontani_dall_etichetta() -> None:
    testo = "Riferimento pratica A1B2. Livello CCNL: D2. Comune: Torino."
    assert ImportatorePdfBustaPaga._cerca_livello(testo) == LivelloCCNL.D2


def test_somma_righe_aggrega_piu_rate_della_stessa_voce() -> None:
    # Caso reale: l'addizionale comunale può comparire su più righe nello stesso mese
    # (saldo anno precedente + acconto anno corrente) e vanno sommate, non solo la prima.
    testo = (
        "002    Addizionale comunale         2025       8,25        66,06                    8,25\n"
        "002    Addizionale comunale         2026       3,88        31,07                    3,88\n"
    )
    dati = ImportatorePdfBustaPaga._estrai_dati_da_testo(testo + "Livello: C3\nMarzo 2026\n2000,00")
    assert dati["addizionale_comunale_pagata"] == 12.13


def test_numero_a_quattro_cifre_senza_punto_delle_migliaia_non_si_spezza() -> None:
    # Regressione: "2158,26" non deve essere interpretato come "215" + "8,26".
    riga = "F39    COMETA             -c/DIP            2158,26        1,200                   25,90"
    dati = ImportatorePdfBustaPaga._estrai_dati_da_testo(riga + "\nLivello: C3\nMarzo 2026\n2000,00")
    assert dati["contributi_cometa_dipendente"] == 25.90


def test_numero_con_tre_decimali_viene_interpretato_correttamente() -> None:
    # Regressione: "43,170" deve valere 43.17, non spezzarsi in "43,17" + "0".
    riga = "F40    COMETA             -c/AZI            2158,26       43,170"
    dati = ImportatorePdfBustaPaga._estrai_dati_da_testo(riga + "\nLivello: C3\nMarzo 2026\n2000,00")
    assert dati["contributi_cometa_azienda"] == 43.17


def test_estrai_buste_paga_multiplo_separa_riuscite_e_fallite(tmp_path: Path) -> None:
    percorso_valido = tmp_path / "cedolino_marzo.pdf"
    _crea_pdf_di_prova(percorso_valido, _TESTO_CEDOLINO_ESEMPIO.strip().splitlines())

    testo_febbraio = _TESTO_CEDOLINO_ESEMPIO.replace("Marzo 2026", "Febbraio 2026")
    percorso_valido_2 = tmp_path / "cedolino_febbraio.pdf"
    _crea_pdf_di_prova(percorso_valido_2, testo_febbraio.strip().splitlines())

    percorso_non_valido = tmp_path / "documento_estraneo.pdf"
    _crea_pdf_di_prova(percorso_non_valido, ["Documento senza i dati richiesti dal cedolino."])

    importate, errori = ImportatorePdfBustaPaga().estrai_buste_paga(
        [percorso_valido, percorso_valido_2, percorso_non_valido]
    )

    assert [b.mese for b in importate] == [Mese.FEBBRAIO, Mese.MARZO]
    assert len(errori) == 1
    assert errori[0][0] == percorso_non_valido
