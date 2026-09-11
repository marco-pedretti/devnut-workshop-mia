"""6 · Perché questo modello — le quattro strade provate e la frontiera della penalità."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from comune import (
    AMBRA, BLU, GRIGIO, M, ROSSO, VERDE,
    headline, intestazione, nota, stile_grafico,
)

intestazione(
    "6 · Perché questo modello",
    "Quattro strade provate, una sola regge il vincolo",
    "Tutte misurate sullo stesso split temporale: i numeri sono confrontabili fra loro",
)
headline(
    "Il MAE da solo sceglie il modello sbagliato. La Random Forest ha un errore di "
    "<strong>6,0 giorni</strong> — quasi la metà del nostro — ma rompe la promessa nel "
    "<strong>12,7%</strong> dei casi, più del doppio di oggi. "
    "Il vincolo di business cambia il vincitore."
)

conf = pd.DataFrame(M["confronto_modelli"])
colori_fam = {"baseline": "#e2e8f0", "scartato": GRIGIO, "alternativa": AMBRA, "scelto": VERDE}
fig = go.Figure()
for fam, gruppo in conf.groupby("famiglia", sort=False):
    fig.add_trace(
        go.Scatter(
            x=gruppo["anticipi"], y=gruppo["mae"], mode="markers+text",
            name=fam, text=gruppo["modello"], textposition="top center",
            marker=dict(size=16 if fam == "scelto" else 12, color=colori_fam[fam],
                        line=dict(width=2, color="white")),
            customdata=gruppo["nota"],
            hovertemplate="<b>%{text}</b><br>MAE %{y:.2f} gg<br>ritardi %{x:.1f}%"
                          "<br><i>%{customdata}</i><extra></extra>",
        )
    )
fig.add_vrect(x0=0, x1=5, fillcolor=VERDE, opacity=0.07, line_width=0,
              annotation_text="zona accettabile (≤ 5% di ritardi)",
              annotation_position="top left")
fig.add_vline(x=5, line_color=ROSSO, line_dash="dash")
fig.update_xaxes(title="quota di ritardi (%) — più a sinistra è meglio", range=[0, 15])
fig.update_yaxes(title="MAE (giorni) — più in basso è meglio", range=[0, 30])
fig.update_layout(hovermode="closest")
st.plotly_chart(
    stile_grafico(fig, 470, "Il piano in cui si decide: precisione contro promesse rotte"),
    width="stretch",
)

st.dataframe(
    conf[["modello", "mae", "anticipi", "nota"]], width="stretch", hide_index=True,
    column_config={
        "modello": st.column_config.TextColumn("modello", width="medium"),
        "mae": st.column_config.NumberColumn("MAE (gg)", format="%.2f"),
        "anticipi": st.column_config.NumberColumn("quota ritardi", format="%.1f%%"),
        "nota": st.column_config.TextColumn("perché", width="large"),
    },
)

c1, c2 = st.columns(2)
with c1:
    nota(
        "<strong>Perché la calibrazione post-hoc fallisce.</strong> Alla Random Forest abbiamo "
        "aggiunto un margine fisso stimato sui residui di aprile-maggio: +9 giorni. "
        "Sul test (giugno-agosto, molto più veloce) è troppo prudente — i ritardi crollano "
        "all'1,8% ma il MAE sale a 14,1 giorni, <strong>peggio della promessa attuale</strong>. "
        "Causa: il fenomeno non è stazionario, e un margine storico non regge un futuro più veloce.",
        "rossa",
    )
with c2:
    nota(
        "<strong>Perché la regressione logistica non basta.</strong> L'idea era elegante: "
        "stimare P(consegna ≤ d giorni) e prendere il primo giorno con probabilità ≥ 95%, "
        "calibrato per costruzione. Centra il vincolo (2,2% di ritardi) ma con un MAE di "
        "27,5 giorni: un confine lineare per bucket giornaliero non cattura le soglie su "
        "distanza, categoria e tempo di approvazione che abbiamo visto nella pagina 5."
    )

st.markdown("##### La penalità è una scelta di business, e la mostriamo come tale")
col1, col2 = st.columns([3, 2])
with col1:
    gd = pd.DataFrame(M["grid_penalty"]["default"])
    gt = pd.DataFrame(M["grid_penalty"]["tunata"])
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=gd["anticipi_test"], y=gd["mae_test"], mode="lines+markers",
        name="architettura di partenza", line=dict(color=GRIGIO, width=2),
        text=[f"penalty {p:g}" for p in gd["penalty"]],
        hovertemplate="%{text}<br>MAE %{y:.2f} · ritardi %{x:.1f}%<extra></extra>",
    ))
    fig.add_trace(go.Scatter(
        x=gt["anticipi_test"], y=gt["mae_test"], mode="lines+markers",
        name="architettura tunata", line=dict(color=BLU, width=3),
        text=[f"penalty {p:g}" for p in gt["penalty"]],
        hovertemplate="%{text}<br>MAE %{y:.2f} · ritardi %{x:.1f}%<extra></extra>",
    ))
    scelto = gt[gt["penalty"] == 5].iloc[0]
    fig.add_trace(go.Scatter(
        x=[scelto["anticipi_test"]], y=[scelto["mae_test"]], mode="markers+text",
        name="scelto (penalty = 5)", text=["penalty 5"], textposition="bottom right",
        marker=dict(size=18, color=VERDE, line=dict(width=2, color="white")),
    ))
    fig.add_vline(x=5, line_color=ROSSO, line_dash="dash")
    fig.update_xaxes(title="quota di ritardi (%)", range=[0, 14])
    fig.update_yaxes(title="MAE (giorni)", range=[4, 14])
    fig.update_layout(hovermode="closest")
    st.plotly_chart(
        stile_grafico(fig, 420, "La frontiera: ogni punto è un valore della penalità"),
        width="stretch",
    )
with col2:
    nota(
        "<strong>Come si legge.</strong> Ogni punto è lo stesso modello con una penalità diversa "
        "sugli anticipi. Muoversi lungo la curva significa comprare meno promesse rotte pagando "
        "in precisione. <strong>Non esiste un valore «giusto» statisticamente</strong>: è la "
        "soglia del 5% a dire dove fermarsi."
    )
    nota(
        "<strong>Perché due curve.</strong> Quella blu è l'architettura scelta con "
        "<code>RandomizedSearchCV</code> e <code>TimeSeriesSplit</code>, quella grigia i "
        "parametri di partenza. La blu <strong>domina</strong>: a parità di penalità ha MAE "
        "più basso <em>e</em> meno ritardi. Abbiamo tunato l'architettura con loss simmetrica "
        "e scelto la penalità <em>dopo</em>: mescolarle avrebbe prodotto architetture storte "
        "per compensare la penalità.",
        "verde",
    )
    nota(
        "<strong>La scelta finale.</strong> Penalità 5 → MAE 10,00 e 4,4% di ritardi, "
        "sotto il 5% con margine. Penalità 4 guadagna 0,7 giorni di MAE ma sale al 5,1%: "
        "sfora. Abbiamo preferito il margine."
    )
