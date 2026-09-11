"""7 · Simulatore — la previsione su un caso, con gli avvisi sui segmenti fragili."""

from datetime import timedelta

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from comune import (
    AMBRA, BLU, M, VERDE,
    carica_modello, headline, intestazione, kpi, nota, stile_grafico,
)

intestazione(
    "7 · Simulatore",
    "Che data prometteremmo a questo cliente?",
    "Il modello vero, caricato da models/xgb_delivery_days.json",
)
headline(
    "Muovi un parametro alla volta e guarda la previsione. "
    "Gli avvisi sotto la data non sono decorativi: dicono se l'ordine cade in un segmento "
    "dove il modello è <strong>affidabile</strong> o in uno dove sappiamo che <strong>sbaglia</strong>."
)

model = carica_modello()
intervalli = M["intervalli_input"]
cat = M["categorie"]

col_input, col_out = st.columns([2, 3])

with col_input:
    st.markdown("##### Caratteristiche dell'ordine")
    d = intervalli["distance_km_mean"]
    distanza = st.slider(
        "Distanza venditore-cliente (km)", 0.0, 3000.0, float(d["mediana"]), 10.0,
        help=f"nel test: da {d['p1']:.0f} a {d['p99']:.0f} km, mediana {d['mediana']:.0f}",
    )
    f = intervalli["total_freight"]
    spedizione = st.slider(
        "Costo di spedizione (R$)", 0.0, 150.0, float(f["mediana"]), 0.5,
        help=f"nel test: da {f['p1']:.1f} a {f['p99']:.1f} R$, mediana {f['mediana']:.1f}",
    )
    p = intervalli["total_weight_g"]
    peso = st.slider(
        "Peso totale (g)", 0.0, 25000.0, float(p["mediana"]), 50.0,
        help=f"nel test: da {p['p1']:.0f} g a {p['p99'] / 1000:.1f} kg, mediana {p['mediana']:.0f} g",
    )
    a = intervalli["approval_hours"]
    approvazione = st.slider(
        "Ore per l'approvazione del pagamento", 0.0, 120.0, float(a["mediana"]), 0.5,
        help="sotto l'ora è carta di credito, sopra i giorni è tipicamente boleto",
    )
    stato = st.selectbox(
        "Stato del cliente", cat["customer_state"], index=cat["customer_state"].index("SP")
    )
    categoria = st.selectbox(
        "Categoria del prodotto", cat["main_category"],
        index=cat["main_category"].index("health_beauty"),
    )
    multi = st.checkbox(
        "Ordine da più venditori (distanza massima diversa dalla media)", value=False
    )
    distanza_max = distanza
    if multi:
        # Scarto invece di un secondo valore assoluto: con la distanza media al
        # massimo uno slider da `distanza` a 3000 sarebbe degenere.
        extra = st.slider(
            "Quanto più lontano è il venditore più distante (km)", 0.0, 1500.0, 500.0, 50.0,
            help="il target è l'arrivo dell'ultimo articolo: decide il venditore più lontano",
        )
        distanza_max = distanza + extra
        st.caption(f"Distanza massima: **{distanza_max:,.0f} km**".replace(",", "."))

riga = pd.DataFrame([{
    "distance_km_mean": distanza,
    "total_freight": spedizione,
    "distance_km_max": distanza_max,
    "customer_state": stato,
    "approval_hours": approvazione,
    "total_weight_g": peso,
    "main_category": categoria,
}])[M["features"]]
for c, valori in cat.items():
    riga[c] = pd.Categorical(riga[c], categories=valori)
giorni = float(model.predict(riga)[0])

with col_out:
    oggi = pd.Timestamp.today().normalize()
    data = oggi + timedelta(days=float(giorni))
    c = st.columns(2)
    with c[0]:
        kpi("Giorni previsti", f"{giorni:.1f}", "il livello prudente che prometteremmo")
    with c[1]:
        kpi("Data da promettere", data.strftime("%d/%m/%Y"),
            f"se l'ordine fosse fatto oggi ({oggi.strftime('%d/%m')})")

    st.write("")
    st.markdown("##### Avvisi su questo ordine")
    avvisi = []
    if distanza < 50:
        avvisi.append(("rossa", "<strong>Distanza sotto i 50 km</strong> — è il segmento con il "
                                "rischio di ritardo più alto (8,5%), nonostante il MAE più basso."))
    if peso > 10000:
        avvisi.append(("rossa", "<strong>Oltre 10 kg</strong> — su questa fascia il modello "
                                "tende a sottostimare: 6,9% di ritardi, 9,3% oltre il 99° percentile."))
    if distanza > 1000:
        avvisi.append(("", "<strong>Rotta lunga (&gt; 1.000 km)</strong> — previsione prudente ma "
                           "fuori taratura: su questo segmento il modello sovrastima in media di "
                           "12,6 giorni sul periodo più recente. Da rivedere al prossimo riaddestramento."))
    if stato in ("BA", "SP"):
        avvisi.append(("rossa", f"<strong>Stato {stato}</strong> — sopra l'obiettivo del 5% "
                                f"({'8,0' if stato == 'BA' else '5,4'}% di ritardi)."))
    if approvazione > 24:
        avvisi.append(("", "<strong>Pagamento approvato dopo più di 24 ore</strong> — tipico del "
                           "boleto: la consegna slitta di 2-3 giorni in media."))
    if distanza > intervalli["distance_km_mean"]["p99"] or peso > intervalli["total_weight_g"]["p99"]:
        avvisi.append(("", "<strong>Input oltre il 99° percentile</strong> — il modello estrapola: "
                           "trattare la previsione come un ordine di grandezza."))
    if not avvisi:
        avvisi.append(("verde", "<strong>Nessun segnale di rischio.</strong> Questo ordine cade "
                                "in una zona dove il modello è affidabile: né segmento fragile, "
                                "né input estremo."))
    for tono, testo in avvisi:
        nota(testo, tono)

st.markdown("##### Come risponde il modello se muovi una sola leva")
sens = M["sensitivita"]
etichette = {
    "distance_km_mean": ("Distanza (km)", distanza),
    "total_freight": ("Spedizione (R$)", spedizione),
    "total_weight_g": ("Peso (g)", peso),
    "approval_hours": ("Ore di approvazione", approvazione),
}
fig = make_subplots(rows=1, cols=4, subplot_titles=[v[0] for v in etichette.values()])
for i, (feat, (nome, valore)) in enumerate(etichette.items(), start=1):
    s = sens[feat]
    fig.add_trace(
        go.Scatter(x=s["x"], y=s["y"], mode="lines", line=dict(color=BLU, width=3),
                   showlegend=False,
                   hovertemplate=f"{nome} %{{x:.0f}}<br>%{{y:.1f}} gg previsti<extra></extra>"),
        row=1, col=i,
    )
    fig.add_vrect(x0=s["p1"], x1=s["p99"], fillcolor=VERDE, opacity=0.07, line_width=0,
                  row=1, col=i)
    fig.add_vline(x=valore, line_color=AMBRA, line_dash="dash", line_width=2, row=1, col=i)
    fig.update_yaxes(title="giorni previsti" if i == 1 else None, row=1, col=i)
fig.update_layout(hovermode="closest")
st.plotly_chart(stile_grafico(fig, 330, ""), width="stretch")
nota(
    "Ogni curva fissa il test set reale, forza una feature su una griglia di valori e media la "
    "previsione (è la <em>partial dependence</em>, calcolata a mano perché l'obiettivo custom "
    "confonde scikit-learn). In verde l'intervallo fra 1° e 99° percentile reale, "
    "in arancione dove ti trovi adesso. "
    "<strong>Le curve sono monotone</strong>: il simulatore non zigzaga, e questo è il motivo "
    "per cui ci si può fidare di quello che mostra."
)
