# Workshop Devnut × Master MIA

**Dai dati grezzi al modello, in una giornata.**
Applied Machine Learning · Dataset E-Commerce
17 studenti · 4 gruppi · 1 dataset

---

## Il contesto

Workshop **Devnut** per il **Master MIA (Master in Intelligenza Artificiale)** dell'Università Cattolica, svolto in una singola giornata, dalle **10:00 alle 16:00**.

Al termine, ogni gruppo presenta il proprio lavoro alla classe, agli ospiti e ai conduttori del workshop Devnut: non è un esercizio consegnato e basta, è una presentazione dal vivo davanti a un pubblico che valuta sia il ragionamento sia il risultato.

---

## Obiettivo

Analizzare i dati di un e-commerce reale e risolvere quattro use case che si incontrano davvero nel lavoro quotidiano.

Non è un esercizio di scikit-learn: è un project work in miniatura, con vincoli veri, dati sporchi e un pubblico da convincere alle 16:00.

Quattro squadre, lo stesso dataset, quattro domande di business diverse. Alla fine della giornata i risultati non si sovrappongono: messi insieme, danno il quadro completo.

---

## La consegna del Gruppo 3 — Giorni di consegna

Questa cartella è il lavoro del **Gruppo 3**. Use case: **la promessa di consegna è tarata bene?** — un problema di **regressione**.

**Problema.** La data stimata mostrata al cliente è molto conservativa: gli ordini arrivano spesso giorni prima. Una data sbagliata può costare in termini di conversione.

**Perché conta.** Qui esiste una baseline aziendale da battere: la stima ufficiale dell'e-commerce (`estimated_delivery_date`). Se il modello fa meglio, il risultato è vendibile.

**Target.** Numero di giorni tra acquisto e consegna effettiva.

**Piste sulle feature.** Distanza venditore–cliente, peso e volume del pacco, tempo di approvazione del pagamento, categoria prodotto, carico del venditore nel periodo.

**Le nostre scelte.** Famiglia di modelli e motivazione, con la stima ufficiale dell'e-commerce come baseline di riferimento.

**Come ci misuriamo.** Una metrica di errore confrontabile con quella della stima ufficiale, scelta e motivata nel notebook.

**Domanda da portare in plenaria.** Di quanti giorni si può accorciare la promessa senza superare il 5% di ritardi?

Per il dataset, lo schema relazionale, l'agenda della giornata e le altre tre use case (Gruppo 1: ritardo di consegna, Gruppo 2: punteggio recensione, Gruppo 4: performance venditore), vedi le slide del workshop: [Devnut_Workshop_MIA.pptx](Devnut_Workshop_MIA.pptx).

---


## Deliverable

Due artefatti, tutti alle 16:00, pronti per la presentazione finale.

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
