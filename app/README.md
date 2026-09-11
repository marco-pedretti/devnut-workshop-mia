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

## Cosa contiene

Sette sezioni navigabili dalla barra laterale, nell'ordine del racconto:

1. **Il problema** — la promessa attuale e il margine sprecato
2. **Il risultato** — quanto si accorcia la promessa e cosa vuol dire davvero «MAE 10 giorni»
3. **Dove sbaglia la promessa di oggi** — il decile peggiore e come lo risolve il modello
4. **Dove sbaglia il nostro modello** — segmenti, casi strani, coda degli errori
5. **Le feature** — perché queste sette, e la geografia che invecchia
6. **Perché questo modello** — le quattro strade provate e la frontiera della penalità
7. **Simulatore** — la previsione su un caso, con gli avvisi sui segmenti fragili

`traccia_presentazione.md` è il copione per raccontarla a voce: una sezione per blocco,
con i tempi, le frasi che devono passare e le risposte alle domande prevedibili.
