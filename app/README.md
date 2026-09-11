# app

La dashboard Streamlit.

La dashboard importa le funzioni da `src/` e carica il modello da `models/`.
Non ricostruisce la pipeline e non riaddestra.

---

## Come si avvia

```bash
uv run python -m src.pipeline      # solo la prima volta: genera gli artefatti in models/
uv run streamlit run app/dashboard.py
```

`src.pipeline` fa il giro completo — carica i nove CSV, costruisce le feature a grana-ordine,
applica lo split temporale, addestra il modello scelto e salva tre file in `models/`:

| file | cosa contiene |
|---|---|
| `xgb_delivery_days.json` | il modello serializzato, in formato nativo XGBoost |
| `metriche.json` | metriche, segmenti, importanze, intervalli degli input, categorie ammesse |
| `ordini.parquet` | la tabella ordine con le previsioni sul test |

La dashboard legge solo questi tre. Nessuna aggregazione viene ricalcolata a runtime, quindi
i numeri sullo schermo sono per costruzione gli stessi dei notebook e l'app parte in un istante.

> Il modello si salva in formato nativo XGBoost e non con pickle: l'obiettivo custom
> `asymmetric_mse` è una funzione Python, serve solo in addestramento e non è serializzabile
> in modo affidabile.

## Com'è organizzata

Multipagina nativo (`st.navigation`): una pagina per file, nell'ordine del racconto.
Ogni pagina ha un URL proprio, quindi si può aprire direttamente una sezione durante
la presentazione e il tasto «indietro» del browser funziona.

```
app/
├── dashboard.py              entrypoint: configurazione, stile, navigazione
├── comune.py                 palette, caricamento in cache, mattoni di layout
├── traccia_presentazione.md  il copione per raccontarla a voce
└── pagine/
    ├── 1_problema.py         /problema       la promessa attuale e il margine sprecato
    ├── 2_risultato.py        /risultato      quanto si accorcia, e cosa vuol dire «MAE 10 giorni»
    ├── 3_promessa_oggi.py    /promessa-oggi  il decile peggiore e come lo risolve il modello
    ├── 4_nostri_errori.py    /nostri-errori  segmenti, casi strani, coda degli errori
    ├── 5_feature.py          /feature        perché queste sette, e la geografia che invecchia
    ├── 6_modelli.py          /modelli        le quattro strade provate e la frontiera della penalità
    └── 7_simulatore.py       /simulatore     la previsione su un caso, con gli avvisi
```

Una pagina nuova sono due righe: il file in `pagine/` e la sua `st.Page` in `dashboard.py`.

`comune.py` tiene quello che tutte le pagine condividono — palette, CSS, i tre artefatti
caricati in cache (`M`, `TEST`, `carica_modello()`) e i mattoni di layout (`intestazione`,
`headline`, `nota`, `kpi`, `stile_grafico`). Se manca `models/`, è lì che l'app si ferma
con l'istruzione per rigenerarlo, prima che una pagina provi a leggere dati inesistenti.

> `st.set_page_config` in `dashboard.py` viene prima dell'import di `comune`: dev'essere
> la prima chiamata Streamlit della sessione.

`traccia_presentazione.md` è il copione per raccontarla a voce: un blocco per pagina,
con i tempi, le frasi che devono passare e le risposte alle domande prevedibili.
