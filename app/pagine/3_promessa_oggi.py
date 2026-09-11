"""3 · Dove sbaglia la promessa di oggi — il decile peggiore della baseline."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from comune import (
    ASSE, BLU, GRIGIO, M, ROSSO, VERDE,
    headline, intestazione, nota, stile_grafico,
)

eb = M["errori_baseline"]

intestazione(
    "3 · Dove sbaglia la promessa di oggi",
    "Il decile peggiore: chi sono e cosa li accomuna",
    f"I {eb['n_ordini']:,} ordini con errore oltre {eb['soglia_giorni']} giorni".replace(",", "."),
)
headline(
    f"Gli ordini che la promessa attuale sbaglia di più sono <strong>lontani</strong> "
    f"(distanza 1,5× più alta) e concentrati in <strong>Rio de Janeiro</strong> "
    f"(3,2× sovra-rappresentato). Nel <strong>{eb['quota_ritardi']}% dei casi</strong> "
    "la promessa era troppo <em>ottimista</em>: non è un problema di margine, "
    "è un problema di <em>dove</em> mettere il margine."
)

col1, col2 = st.columns(2)
with col1:
    feat = pd.DataFrame(eb["feature"]).sort_values("rapporto")
    colori = [ROSSO if r > 1.2 else (VERDE if r < 0.95 else GRIGIO) for r in feat["rapporto"]]
    fig = go.Figure(
        go.Bar(x=feat["rapporto"], y=feat["feature"], orientation="h",
               marker_color=colori, text=[f"{r:.2f}×" for r in feat["rapporto"]],
               textposition="outside")
    )
    fig.add_vline(x=1, line_color=ASSE, line_width=2)
    fig.update_xaxes(title="rapporto fra gruppo difficile e resto del test", range=[0, 1.9])
    fig.update_layout(hovermode=False)
    st.plotly_chart(
        stile_grafico(fig, 420, "Quali caratteristiche distinguono gli ordini difficili"),
        width="stretch",
    )

with col2:
    stati = pd.DataFrame(eb["stati"]).dropna(subset=["rapporto"]).sort_values("rapporto")
    colori = [ROSSO if r > 1.5 else (VERDE if r < 0.7 else GRIGIO) for r in stati["rapporto"]]
    fig = go.Figure(
        go.Bar(x=stati["rapporto"], y=stati["stato"], orientation="h",
               marker_color=colori, text=[f"{r:.2f}×" for r in stati["rapporto"]],
               textposition="outside")
    )
    fig.add_vline(x=1, line_color=ASSE, line_width=2)
    fig.update_xaxes(title="sovra/sotto-rappresentazione nel gruppo difficile", range=[0, 4])
    fig.update_layout(hovermode=False)
    st.plotly_chart(
        stile_grafico(fig, 420, "Lo stato del cliente conta più della categoria di prodotto"),
        width="stretch",
    )

c1, c2 = st.columns(2)
with c1:
    nota(
        "<strong>Il carico del venditore non c'entra.</strong> È la prima ipotesi che viene "
        "in mente — «il venditore è sommerso di ordini» — e i dati la smentiscono: nel gruppo "
        "difficile il carico è perfino <em>più basso</em> (0,88-0,90×). Anche la categoria di "
        "prodotto non discrimina (nessun rapporto sopra 1,5×)."
    )
with c2:
    nota(
        "<strong>RJ va oltre la distanza.</strong> Rio è il 30% degli ordini difficili contro "
        "il 9% del resto, e San Paolo — il più vicino agli hub — è sotto-rappresentato "
        "(21% contro 49%). La distanza in linea d'aria da sola non lo spiega: ci sono "
        "<strong>fattori logistici di rotta</strong> che il modello dovrà imparare dai dati."
    )

st.markdown("##### E il nostro modello, su quegli stessi ordini?")
conf = pd.DataFrame(eb["confronto"])
fig = make_subplots(rows=1, cols=2, subplot_titles=("Errore medio (MAE)", "Quota di ritardi"))
fig.add_trace(
    go.Bar(x=conf["gruppo"], y=conf["MAE_baseline"], name="promessa di oggi",
           marker_color=GRIGIO, text=conf["MAE_baseline"], textposition="outside"),
    row=1, col=1,
)
fig.add_trace(
    go.Bar(x=conf["gruppo"], y=conf["MAE_modello"], name="modello",
           marker_color=BLU, text=conf["MAE_modello"], textposition="outside"),
    row=1, col=1,
)
fig.add_trace(
    go.Bar(x=conf["gruppo"], y=conf["anticipi_baseline"], marker_color=GRIGIO,
           showlegend=False, text=[f"{v}%" for v in conf["anticipi_baseline"]],
           textposition="outside"),
    row=1, col=2,
)
fig.add_trace(
    go.Bar(x=conf["gruppo"], y=conf["anticipi_modello"], marker_color=BLU,
           showlegend=False, text=[f"{v}%" for v in conf["anticipi_modello"]],
           textposition="outside"),
    row=1, col=2,
)
fig.add_hline(y=5, line_color=ROSSO, line_dash="dash", row=1, col=2)
fig.update_yaxes(range=[0, 37], row=1, col=1)
fig.update_yaxes(range=[0, 7.5], row=1, col=2)
fig.update_layout(barmode="group", hovermode=False)
st.plotly_chart(stile_grafico(fig, 380, ""), width="stretch")

c1, c2 = st.columns(2)
with c1:
    nota(
        "<strong>Il modello aggredisce proprio i casi peggiori.</strong> Sul decile difficile "
        "l'errore crolla da <strong>31,4 a 13,2 giorni (−58%)</strong>, contro un −13% sul "
        "resto del test. Non migliora la media spalmando: corregge dove la promessa di oggi "
        "faceva più danno.",
        "verde",
    )
with c2:
    nota(
        f"<strong>Il prezzo, detto onestamente.</strong> Su questo gruppo la quota di ritardi "
        f"<em>sale</em> (1,6% → 2,5%) mentre sul resto scende (5,7% → 4,6%). "
        f"La correlazione fra i due errori è {eb['correlazione_errori']}: gli ordini "
        "logisticamente complessi restano relativamente più difficili anche per noi. "
        "In produzione vanno monitorati a parte."
    )
