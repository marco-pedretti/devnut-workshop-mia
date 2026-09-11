"""2 · Il risultato — quanto si accorcia la promessa, e cosa vuol dire «MAE 10 giorni»."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from comune import (
    ASSE, BLU, GRIGIO, M, MT, ROSSO, TEST, VERDE,
    headline, intestazione, kpi, nota, stile_grafico,
)

intestazione(
    "2 · Il risultato",
    "Si accorcia la promessa e si rompe meno spesso",
    "XGBoost con loss asimmetrica · misurato sugli ultimi 19.294 ordini, mai visti in addestramento",
)
risp_media = MT["giorni_promessa_risparmiati_media"]
headline(
    f"La promessa si può accorciare di <strong>{risp_media:.1f} giorni in media</strong> "
    f"(da {MT['promessa_media_baseline']} a {MT['promessa_media_modello']} giorni) "
    f"e allo stesso tempo i ritardi <strong>scendono</strong> dal "
    f"{MT['quota_anticipi_baseline'] * 100:.1f}% al {MT['quota_anticipi'] * 100:.1f}%. "
    "Non è un compromesso: si guadagna su entrambi i fronti."
)

c = st.columns(4)
with c[0]:
    kpi(
        "Giorni di promessa recuperati",
        f"−{risp_media:.1f} gg",
        f"mediana −{MT['giorni_promessa_risparmiati_mediana']:.1f} gg", "buono",
    )
with c[1]:
    kpi(
        "Quota di ritardi",
        f"{MT['quota_anticipi'] * 100:.1f}%",
        f"oggi {MT['quota_anticipi_baseline'] * 100:.1f}% · obiettivo ≤ 5%", "buono",
    )
with c[2]:
    delta = (1 - MT["MAE_giorni"] / MT["MAE_baseline_giorni"]) * 100
    kpi(
        "Errore medio (MAE)",
        f"{MT['MAE_giorni']:.2f} gg",
        f"oggi {MT['MAE_baseline_giorni']:.2f} gg · −{delta:.0f}%", "buono",
    )
with c[3]:
    kpi(
        "Ordini con data più vicina",
        f"{MT['quota_ordini_con_promessa_piu_corta'] * 100:.0f}%",
        "sul resto la promessa resta o si allarga",
    )

st.write("")
col1, col2 = st.columns([3, 2])

with col1:
    risparmio = TEST["estimated_days"] - TEST["pred"]
    fig = go.Figure()
    fig.add_trace(
        go.Histogram(
            x=risparmio.clip(-15, 30), xbins=dict(start=-15, end=30, size=1),
            marker_color=VERDE, opacity=0.85, name="ordini",
        )
    )
    fig.add_vline(x=0, line_color=ASSE, line_width=2)
    fig.add_vline(
        x=risparmio.mean(), line_color="#7f1d1d", line_dash="dash",
        annotation_text=f"media {risparmio.mean():.1f} gg", annotation_position="top right",
    )
    fig.update_xaxes(title="giorni di promessa recuperati (a destra = data più vicina)")
    fig.update_yaxes(title="ordini")
    fig.update_layout(hovermode="x")
    st.plotly_chart(
        stile_grafico(fig, 400, "Di quanto si accorcia la promessa, ordine per ordine"),
        width="stretch",
    )

with col2:
    fig = make_subplots(rows=1, cols=2, subplot_titles=("Giorni promessi", "Quota di ritardi"))
    fig.add_trace(
        go.Bar(
            x=["oggi", "modello"],
            y=[MT["promessa_media_baseline"], MT["promessa_media_modello"]],
            marker_color=[GRIGIO, BLU],
            text=[f"{MT['promessa_media_baseline']:.1f}", f"{MT['promessa_media_modello']:.1f}"],
            textposition="outside", showlegend=False,
        ),
        row=1, col=1,
    )
    fig.add_trace(
        go.Bar(
            x=["oggi", "modello"],
            y=[MT["quota_anticipi_baseline"] * 100, MT["quota_anticipi"] * 100],
            marker_color=[GRIGIO, VERDE],
            text=[f"{MT['quota_anticipi_baseline'] * 100:.1f}%",
                  f"{MT['quota_anticipi'] * 100:.1f}%"],
            textposition="outside", showlegend=False,
        ),
        row=1, col=2,
    )
    fig.add_hline(y=5, line_color=ROSSO, line_dash="dash", row=1, col=2)
    fig.update_yaxes(range=[0, 26], row=1, col=1)
    fig.update_yaxes(range=[0, 7], row=1, col=2)
    fig.update_layout(hovermode=False)
    st.plotly_chart(stile_grafico(fig, 400, ""), width="stretch")

st.markdown("##### Che cosa vuol dire davvero «MAE 10 giorni»")
nota(
    f"Il modello <strong>non è più preciso</strong> della promessa attuale: è più "
    f"<strong>prudente in modo controllato</strong>. Il "
    f"<strong>{MT['quota_sovrastime'] * 100:.1f}% delle previsioni sovrastima</strong> "
    f"e l'errore mediano è <strong>+{MT['errore_mediano']:.1f} giorni</strong>. "
    "Con una penalità 5× sugli anticipi il modello non stima il giorno tipico: "
    "stima un livello prudente (in gergo un <em>expectile</em> all'83%). "
    "Dire «MAE 10 giorni» senza questa riga fa sembrare impreciso un modello che invece è tarato."
)

dentro = pd.DataFrame(M["distribuzione_errore"]["entro_soglia"])
fig = go.Figure()
fig.add_trace(
    go.Bar(x=[f"±{s} gg" for s in dentro["soglia"]], y=dentro["baseline"],
           name="promessa di oggi", marker_color=GRIGIO)
)
fig.add_trace(
    go.Bar(x=[f"±{s} gg" for s in dentro["soglia"]], y=dentro["modello"],
           name="modello", marker_color=BLU)
)
fig.update_yaxes(title="% di ordini dentro la soglia")
fig.update_layout(barmode="group", hovermode="x")
col1, col2 = st.columns([3, 2])
with col1:
    st.plotly_chart(
        stile_grafico(fig, 340, "Quanti ordini cadono dentro una certa tolleranza"),
        width="stretch",
    )
with col2:
    nota(
        "Letto bene, il grafico dice:"
        "<ul style='margin:.4rem 0 .6rem 0; padding-left: 1.2rem;'>"
        "<li><strong>Entro ±3 giorni il modello perde:</strong> 7,4% contro 10,8%</li>"
        "<li><strong>Entro ±10 giorni vince:</strong> 52,4% contro 42,2%</li>"
        "<li><strong>Taglia le sovrastime assurde:</strong> il 99° percentile dell'errore "
        "passa da +37,5 a +21,9 giorni</li>"
        "</ul>"
        "Non promette date «giuste al giorno», ma per chi gestisce la promessa è il "
        "compromesso giusto — ed è meglio dirlo noi che sentirselo chiedere.",
        "verde",
    )
