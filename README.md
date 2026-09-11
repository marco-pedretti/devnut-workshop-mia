# Workshop Devnut × Master MIA

**Dai dati grezzi al modello, in una giornata.**
Applied Machine Learning · Dataset E-Commerce
17 studenti · 4 gruppi · 1 dataset

---

## Obiettivo

Analizzare i dati di un e-commerce reale e risolvere quattro use case che si incontrano davvero nel lavoro quotidiano.

Non è un esercizio di scikit-learn: è un project work in miniatura, con vincoli veri, dati sporchi e un pubblico da convincere alle 17:00.

Quattro squadre, lo stesso dataset, quattro domande di business diverse. Alla fine della giornata i risultati non si sovrappongono: messi insieme, danno il quadro completo.

---


## Deliverable

Due artefatti, tutti alle 16:00.

**1. Codice Python** — script o notebook eseguibile end-to-end, dal caricamento dei CSV al modello salvato. Pipeline riproducibile, split temporale esplicito, note sulle scelte fatte.

**2. Dashboard Streamlit** — una pagina che mostra i risultati a chi non ha visto il codice: metriche del modello, driver principali, simulazione su un caso.


---

## Cosa contiene questa cartella

```
devnut-workshop-mia/
├── README.md          questo file
├── pyproject.toml     le librerie disponibili nell'ambiente
├── uv.lock            le versioni esatte, uguali per tutti
├── data/
│   ├── raw/           i nove CSV originali — non si modificano mai
│   └── processed/     la tabella ordine e i dataset derivati che costruite voi
├── notebooks/         esplorazione, modelli, grafici
├── src/               le funzioni che servono sia al notebook sia alla dashboard
├── models/            modello addestrato e metriche salvate
└── app/               la dashboard Streamlit
```

Trovate una descrizione più estesa dentro ogni cartella.

Nella cartella c'è la struttura, non il codice: caricamento, aggregazioni, feature e modelli li scrivete voi. È esattamente la parte che valutiamo.

**Sul `pyproject.toml`:** elenca le librerie installate, non quelle da usare. È una cassetta degli attrezzi tenuta larga apposta, così nessuno perde tempo a installare qualcosa alle tre del pomeriggio. Quali strumenti servano al vostro use case è una decisione vostra, e va motivata nel documento.

Il setup dell'ambiente è descritto nel documento **Setup ambiente di lavoro**, inviato a parte. Va completato **prima** della giornata: la mattina si parte dai dati, non dai `pip install`.

---

*Devnut · AI Happens Everywhere.*
