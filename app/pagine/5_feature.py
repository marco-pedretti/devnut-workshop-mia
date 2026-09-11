"""5 · Le feature — perché queste sette, e la geografia che invecchia."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from comune import (
    AMBRA, BLU, GRIGIO, M, ROSSO, VERDE, VIOLA,
    headline, intestazione, kpi, nota, stile_grafico,
)

af = M["analisi_feature"]

intestazione(
    "5 · Le feature",
    "Sette variabili, tutte note al momento del checkout",
    "Nessuna informazione sulla consegna effettiva: il vincolo che rende il modello utilizzabile davvero",
)
headline(
    "La <strong>distanza venditore-cliente</strong> è il driver dominante (Spearman 0,54); "
    "tutto il resto è segnale secondario che solo un modello ad alberi sa sfruttare, "
    "grazie a effetti <strong>a soglia</strong> che la correlazione lineare non vede."
)

col1, col2 = st.columns([2, 3])
with col1:
    sp = pd.DataFrame(af["spearman"]).sort_values("spearman")
    fig = go.Figure(
        go.Bar(x=sp["spearman"], y=sp["feature"], orientation="h",
               marker_color=[BLU if abs(v) > 0.3 else GRIGIO for v in sp["spearman"]],
               text=[f"{v:.3f}" for v in sp["spearman"]], textposition="outside")
    )
    fig.update_xaxes(title="correlazione di Spearman col target", range=[0, 0.65])
    fig.update_layout(hovermode=False)
    st.plotly_chart(
        stile_grafico(fig, 360, "Forza della relazione, feature per feature"), width="stretch"
    )
with col2:
    nota(
        "<strong>Attenzione a leggere solo questa colonna.</strong> Peso, ore di approvazione e "
        "carico del venditore hanno Spearman fra 0,05 e 0,09 e sembrano inutili. "
        "Ma la correlazione monotona misura una cosa sola: se salgono insieme <em>sempre</em>. "
        "Il segnale reale di queste variabili è a gradino, e si vede solo guardandole a fasce."
    )
    nota(
        f"<strong>Copertura.</strong> La distanza manca sullo "
        f"{af['nulli'].get('distance_km_mean', 0):.2f}% degli ordini "
        "(coordinate di geolocalizzazione assenti) e la categoria sull'"
        f"{af['nulli'].get('main_category', 0):.2f}%. "
        "Abbiamo lasciato i buchi: XGBoost impara da solo da che parte mandarli, "
        "e la pagina 4 mostra che non degradano nulla."
    )

st.markdown("##### L'effetto a fasce: dove si vede il segnale che Spearman nasconde")
fasce = af["fasce"]
fig = make_subplots(
    rows=2, cols=2,
    subplot_titles=(
        "Distanza — il driver forte (Spearman 0,54)",
        "Ore di approvazione del pagamento (Spearman 0,09)",
        "Peso totale (Spearman 0,09)",
        "Costo di spedizione (proxy di distanza e ingombro)",
    ),
    vertical_spacing=0.18,
)
for chiave, r, c, colore in [
    ("distanza", 1, 1, BLU), ("approvazione", 1, 2, VIOLA),
    ("peso", 2, 1, AMBRA), ("spedizione", 2, 2, VERDE),
]:
    d = pd.DataFrame(fasce[chiave])
    fig.add_trace(
        go.Bar(x=d["fascia"], y=d["media"], marker_color=colore, showlegend=False,
               text=[f"{v:.1f}" for v in d["media"]], textposition="outside",
               customdata=d["n_ordini"],
               hovertemplate="%{x}<br>%{y:.1f} gg medi<br>%{customdata:,} ordini<extra></extra>"),
        row=r, col=c,
    )
    fig.update_yaxes(title="giorni medi", row=r, col=c)
fig.update_layout(hovermode="closest")
st.plotly_chart(stile_grafico(fig, 640, ""), width="stretch")

c1, c2 = st.columns(2)
with c1:
    nota(
        "<strong>Le ore di approvazione sono la feature «debole» più interessante.</strong> "
        "Spearman 0,09 solo perché quasi tutti pagano con carta e vengono approvati in meno "
        "di un'ora: la variabile è quasi costante. A fasce l'effetto è netto — 12 giorni se "
        "approvato in meno di un'ora contro 15 se oltre tre giorni. È l'effetto del "
        "<em>boleto</em>, il bollettino bancario brasiliano. "
        "Ed è nota al checkout, quindi si può usare senza leakage."
    )
with c2:
    veloci = pd.DataFrame(af["categorie"]["veloci"])
    lente = pd.DataFrame(af["categorie"]["lente"])
    nota(
        "<strong>La categoria sposta parecchio.</strong> Fra le categorie con almeno 300 ordini "
        f"si va da <strong>{veloci.iloc[0]['categoria']}</strong> "
        f"({veloci.iloc[0]['media']:.1f} giorni) a "
        f"<strong>{lente.iloc[-1]['categoria']}</strong> "
        f"({lente.iloc[-1]['media']:.1f} giorni): "
        "mobili e arredo per ufficio viaggiano su tutt'altra filiera rispetto al cibo "
        "o ai piccoli elettrodomestici."
    )

st.markdown("##### Perché teniamo *sia* la distanza media *sia* la massima")
mvm = af["mean_vs_max"]
c = st.columns(4)
with c[0]:
    kpi("Correlazione fra le due", f"{mvm['correlazione']:.3f}", "quasi la stessa variabile")
with c[1]:
    kpi("Ordini multi-venditore", f"{mvm['quota_ordini_multi_venditore']:.1f}%",
        "solo qui le due possono differire")
with c[2]:
    kpi("Ordini dove differiscono", f"{mvm['quota_ordini_con_distanze_diverse']:.1f}%",
        f"ma lì il divario medio è {mvm['delta_medio_quando_diverse']:.0f} km")
with c[3]:
    kpi("Spearman media / max", f"{mvm['spearman_mean']:.3f} / {mvm['spearman_max']:.3f}",
        "indistinguibili sul target")

nota(
    "<strong>La ragione è il target, non la statistica.</strong> «Giorni di consegna» significa "
    "l'arrivo dell'<em>ultimo</em> articolo: se un ordine ha due venditori, uno a 50 km e uno a "
    "1.500 km, è il secondo a decidere quando l'ordine è chiuso. La distanza <em>massima</em> è "
    "quindi la variabile concettualmente corretta, la <em>media</em> descrive lo sforzo logistico "
    f"complessivo. Nei fatti coincidono sul {100 - mvm['quota_ordini_con_distanze_diverse']:.1f}% "
    f"degli ordini, ma sull'{mvm['quota_ordini_con_distanze_diverse']:.1f}% in cui differiscono "
    f"il divario medio è di {mvm['delta_medio_quando_diverse']:.0f} km — ed è proprio lì che la "
    "distinzione conta. Le abbiamo tenute entrambe perché il costo è nullo e la permutation "
    "importance (sotto) dice che il modello usa davvero solo la media: "
    "<strong>il massimo è un'assicurazione, non un pilastro.</strong>"
)

st.markdown("##### Feature importance: quanto il modello *usa* una feature e quanto gli *serve*")
imp = pd.DataFrame(M["importanza"]["righe"])
col1, col2 = st.columns(2)
with col1:
    g = imp.sort_values("gain")
    fig = go.Figure(
        go.Bar(x=g["gain"], y=g["feature"], orientation="h", marker_color=BLU,
               text=[f"{v:,.0f}".replace(",", ".") for v in g["gain"]], textposition="outside")
    )
    fig.update_xaxes(title="gain totale (quanto il modello la usa)")
    fig.update_layout(hovermode=False)
    st.plotly_chart(stile_grafico(fig, 380, "In addestramento"), width="stretch")
with col2:
    o = imp.sort_values("gain")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=o["utilita_calib"], y=o["feature"], orientation="h",
                         name="aprile-maggio", marker_color=BLU))
    fig.add_trace(go.Bar(x=o["utilita_test"], y=o["feature"], orientation="h",
                         name="giugno-agosto", marker_color=ROSSO))
    fig.add_vline(x=0, line_color="#0f172a", line_width=2)
    fig.update_xaxes(title="quanto serve davvero (positivo = utile)")
    fig.update_layout(barmode="group", hovermode="y")
    st.plotly_chart(stile_grafico(fig, 380, "Su due periodi diversi"), width="stretch")

nota(
    "<strong>Nota metodologica, e non è un dettaglio.</strong> Questo modello non stima il "
    "giorno tipico: con penalità 5× stima un livello prudente. Misurare la permutation "
    "importance con il MAE darebbe importanze <em>negative</em> su quasi tutte le feature, "
    "perché il MAE premia la mediana e mescolare una feature che alza le previsioni "
    "«migliora» il MAE peggiorando il modello. Abbiamo usato la loss asimmetrica stessa, "
    "cioè quella che il modello ottimizza davvero. È un errore in cui siamo caduti una volta "
    "e vale la pena raccontarlo."
)

st.markdown("##### Il risultato più interessante: la geografia si è fatta stantia")
col1, col2 = st.columns([2, 3])
with col1:
    d = pd.DataFrame(M["importanza"]["errore_per_fascia"])
    fig = go.Figure()
    fig.add_trace(go.Bar(x=d["fascia"], y=d["calib"], name="aprile-maggio",
                         marker_color=BLU, text=d["calib"], textposition="outside"))
    fig.add_trace(go.Bar(x=d["fascia"], y=d["test"], name="giugno-agosto",
                         marker_color=ROSSO, text=d["test"], textposition="outside"))
    fig.update_yaxes(title="errore medio (giorni di sovrastima)", range=[0, 15])
    fig.update_layout(barmode="group", hovermode="x")
    st.plotly_chart(stile_grafico(fig, 360, "Errore medio per fascia di distanza"),
                    width="stretch")
with col2:
    nota(
        "Le tre viste <strong>non concordano, e la discordanza è il risultato</strong>. "
        "In addestramento il modello si appoggia soprattutto a <code>customer_state</code> e "
        "alle distanze. Sul periodo di calibrazione (aprile-maggio, subito dopo il training) "
        "quelle stesse feature sono le più utili: +20,2 e +17,8. "
        "Sul test (giugno-agosto) diventano <strong>negative</strong>: −4,6 e −6,5. "
        "Mescolarle <em>migliora</em> il modello.",
        "rossa",
    )
    nota(
        "<strong>Non è un artefatto di misura: è la geografia che invecchia.</strong> "
        "In calibrazione il modello sbaglia in modo abbastanza uniforme (+5,1 / +7,9 / +6,6 giorni); "
        "sul test l'errore esplode proprio sulle lunghe distanze (+5,6 / +10,6 / <strong>+12,6</strong>). "
        "Il modello ha imparato dal 2016-17 che «lontano = lento», ma nel frattempo le rotte "
        "lunghe sono diventate molto più veloci e lui continua a gonfiare la previsione. "
        "<strong>È l'argomento tecnico per il riaddestramento periodico</strong>, ed è il primo "
        "numero da mettere sotto monitoraggio in produzione.",
        "verde",
    )
