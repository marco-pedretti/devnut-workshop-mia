"""1 · Il problema — la promessa di oggi e il margine sprecato."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from comune import AMBRA, BLU, GRIGIO, M, headline, intestazione, kpi, nota, stile_grafico

intestazione(
    "1 · Il problema",
    "La promessa di consegna è tarata bene?",
    "Gruppo 3 · dataset Olist · 96.470 ordini consegnati, da settembre 2016 ad agosto 2018",
)
headline(
    "L'e-commerce promette una data di consegna al checkout. Oggi quella promessa "
    "sbaglia in media di <strong>12,7 giorni</strong> ed è quasi sempre <strong>troppo larga</strong>: "
    "rassicura il cliente al prezzo di sembrare lento. "
    "La domanda è: <strong>di quanti giorni si può accorciare senza superare il 5% di ritardi?</strong>"
)

c = st.columns(4)
with c[0]:
    kpi("Ordini analizzati", "96.470", "solo ordini consegnati")
with c[1]:
    kpi("Consegna reale media", "12,6 gg", "mediana 10,2 gg")
with c[2]:
    kpi("Promessa media", "23,7 gg", "quasi il doppio della realtà")
with c[3]:
    kpi("Errore della promessa", "12,7 gg", "sbagliato in eccesso nel 92% dei casi", "cattivo")

st.write("")
col1, col2 = st.columns([3, 2])

with col1:
    deriva = pd.DataFrame(M["deriva_temporale"])
    deriva["data"] = pd.to_datetime(deriva["mese"])
    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=deriva["data"], y=deriva["consegna_media"], name="consegna reale",
            line=dict(color=BLU, width=3),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=deriva["data"], y=deriva["promessa_media"], name="promessa dell'e-commerce",
            line=dict(color=GRIGIO, width=3), fill="tonexty",
            fillcolor="rgba(148,163,184,0.22)",
        )
    )
    fig.add_vrect(
        x0=pd.Timestamp(M["test"]["dal"]), x1=deriva["data"].iloc[-1],
        fillcolor=AMBRA, opacity=0.10, line_width=0,
        annotation_text="periodo di test", annotation_position="top left",
    )
    fig.update_yaxes(title="giorni")
    st.plotly_chart(
        stile_grafico(fig, 400, "Lo spazio fra le due curve è il margine sprecato"),
        width="stretch",
    )

with col2:
    nota(
        "<strong>Il fatto che regge tutto il resto.</strong> Le consegne accelerano: "
        "da <strong>17,0 giorni medi</strong> a febbraio 2018 a <strong>7,7</strong> ad agosto. "
        "La promessa resta invece inchiodata sui 23-24 giorni per quasi tutto il periodo e "
        "comincia a scendere solo negli ultimi due mesi, quando le consegne si erano già "
        "dimezzate. Il margine non si è ridotto insieme alla logistica: "
        "quello spazio è esattamente ciò che vogliamo recuperare."
    )
    nota(
        "<strong>Come abbiamo diviso i dati.</strong> Split temporale, mai casuale: "
        f"addestramento su {M['addestrato_su']['righe']:,} ordini "
        f"({M['addestrato_su']['dal']} → {M['addestrato_su']['al']}), "
        f"calibrazione su {M['calibrazione']['righe']:,}, "
        f"test sugli ultimi {M['test']['righe']:,} ordini "
        f"({M['test']['dal']} → {M['test']['al']}). "
        "Validare a caso su ordini 'dal futuro' avrebbe gonfiato ogni numero.".replace(",", ".")
    )

st.write("")
st.markdown("##### Le due metriche che useremo, e perché sono due")
c1, c2 = st.columns(2)
with c1:
    nota(
        "<strong>MAE — di quanti giorni sbagliamo.</strong> È la precisione. "
        "Da sola però premia i modelli che tirano a indovinare il giorno tipico, "
        "e a chi gestisce la promessa non basta."
    )
with c2:
    nota(
        "<strong>Quota di ritardi — quante promesse rompiamo.</strong> "
        "Se prevediamo meno giorni di quelli reali, il cliente riceve il pacco "
        "dopo la data promessa. È l'errore che costa davvero. "
        "<strong>Obiettivo: sotto il 5%.</strong>",
        "rossa",
    )
