"""4 · Dove sbaglia il nostro modello — segmenti, casi strani, coda degli errori."""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

from comune import (
    BLU, M, ROSSO, TEST,
    headline, intestazione, kpi, nota, stile_grafico,
)

cs = M["casi_strani"]


def ipotesi_errore(riga: pd.Series) -> str:
    """Regola di lettura applicata ai dati della riga: non e' un output del modello."""
    if riga["err"] < 0:
        if riga["delivery_days"] > 30:
            return "consegna anomala (>30gg): guasto logistico, invisibile alle feature"
        if riga["total_weight_g"] > 10000:
            return "ordine molto pesante: il modello sottostima questa fascia"
        return "sottostima: consegna più lenta del profilo della rotta"
    if riga["distance_km_mean"] > 800:
        return "rotta lunga diventata veloce: geografia stantia (vedi pagina 5)"
    if riga["delivery_days"] < 5:
        return "consegna lampo: sotto ogni tempo visto in addestramento"
    return "sovrastima: margine di prudenza troppo generoso"


intestazione(
    "4 · Dove sbaglia il nostro modello",
    "Casi normali, casi strani e la coda",
    "Gli stessi 19.294 ordini di test, letti dal lato dei nostri errori",
)
headline(
    "Il segmento a rischio <strong>non è quello che ci si aspetta</strong>: "
    "il MAE cresce con la distanza, ma i ritardi fanno l'opposto. "
    "Il 5% è sforato proprio <strong>sotto i 50 km</strong>, dove il modello sembra più preciso."
)

seg_dist = pd.DataFrame(M["segmenti"]["distanza"])
fig = make_subplots(specs=[[{"secondary_y": True}]])
fig.add_trace(
    go.Bar(x=seg_dist["fascia"], y=seg_dist["MAE"], name="MAE (giorni)",
           marker_color=BLU, opacity=0.85),
    secondary_y=False,
)
fig.add_trace(
    go.Scatter(x=seg_dist["fascia"], y=seg_dist["anticipi_pct"], name="quota ritardi (%)",
               line=dict(color=ROSSO, width=3), mode="lines+markers", marker=dict(size=10)),
    secondary_y=True,
)
fig.add_hline(y=5, line_color=ROSSO, line_dash="dash", secondary_y=True)
fig.update_yaxes(title="MAE (giorni)", secondary_y=False, range=[0, 16])
fig.update_yaxes(title="quota ritardi (%)", secondary_y=True, range=[0, 10],
                 gridcolor="rgba(0,0,0,0)")
col1, col2 = st.columns([3, 2])
with col1:
    st.plotly_chart(
        stile_grafico(fig, 400, "MAE e rischio di ritardo vanno in direzioni opposte"),
        width="stretch",
    )
with col2:
    nota(
        "<strong>Perché succede.</strong> Sulle consegne vicine il margine di prudenza in "
        "giorni è piccolo in valore assoluto: basta poco per bucarlo. Sulle lunghe distanze "
        "il modello mette così tanto margine che il ritardo diventa raro — ma la promessa è larga."
    )
    nota(
        "<strong>Segmenti sopra il 5%:</strong> distanza &lt; 50 km (8,5%), peso &gt; 10 kg (6,9%), "
        "stato BA (8,0%), stato SP (5,4%, e SP pesa il 46% del test). "
        "All'opposto RJ e CE hanno MAE altissimo (14,7 e 16,8 giorni) ma ritardi al 2,9% e 1,4%: "
        "lì la promessa è ancora troppo larga e c'è margine da recuperare.",
        "rossa",
    )

st.markdown("##### Affidabilità per segmento")
tab1, tab2, tab3, tab4 = st.tabs(["Distanza", "Peso", "Stato del cliente", "Categoria"])
for tab, chiave, nome in [
    (tab1, "distanza", "fascia"), (tab2, "peso", "fascia"),
    (tab3, "stato", "stato"), (tab4, "categoria", "categoria"),
]:
    with tab:
        d = pd.DataFrame(M["segmenti"][chiave])
        st.dataframe(
            d, width="stretch", hide_index=True,
            column_config={
                nome: st.column_config.TextColumn(nome.capitalize()),
                "n_ordini": st.column_config.NumberColumn("ordini", format="%d"),
                "MAE": st.column_config.NumberColumn("MAE (gg)", format="%.2f"),
                "anticipi_pct": st.column_config.ProgressColumn(
                    "quota ritardi %", format="%.2f%%", min_value=0, max_value=10
                ),
                "errore_medio": st.column_config.NumberColumn("errore medio (gg)", format="%.2f"),
            },
        )

st.markdown("##### I casi strani")
c = st.columns(4)
with c[0]:
    m = cs["mancanti"]
    kpi("Dati mancanti", f"{m['con_mancanti']['n']}",
        f"MAE {m['con_mancanti']['MAE']} vs {m['completi']['MAE']} · nessun degrado", "buono")
with c[1]:
    r = cs["rarita"]
    kpi("Categorie rare", f"{r['rare']['n']}",
        f"MAE {r['rare']['MAE']} · meglio della media", "buono")
with c[2]:
    peso = [e for e in cs["estremi"] if e["caso"].startswith("peso")][0]
    kpi("Ordini oltre 10 kg (p99)", f"{peso['anticipi_pct']:.1f}%",
        "quota ritardi, più del doppio della media", "cattivo")
with c[3]:
    a = cs["anatomia_coda"]
    kpi("Errori oltre 20 giorni", f"{a['quota_coda'] * 100:.1f}%",
        f"{a['n_coda']} ordini, due famiglie diverse", "neutro")

c1, c2 = st.columns(2)
with c1:
    nota(
        "<strong>Cosa NON serve gestire.</strong> I valori mancanti sono lo 0,9% degli ordini "
        "e XGBoost li tratta nativamente (MAE 10,42 contro 9,99, ritardi perfino più bassi). "
        "Le categorie viste meno di 100 volte in addestramento hanno MAE 9,07, <em>migliore</em> "
        "della media, e nessuna categoria del test era sconosciuta. Niente ramo di fallback.",
        "verde",
    )
with c2:
    nota(
        "<strong>Cosa invece serve gestire.</strong> Gli input estremi contano, e in modo "
        "asimmetrico: gli ordini oltre il 99° percentile di <em>peso</em> hanno il "
        "<strong>9,3% di ritardi</strong>. Le distanze estreme invece alzano il MAE (14,9) "
        "ma non il rischio. È la fragilità vera del modello.",
        "rossa",
    )

st.markdown("##### Le due famiglie della coda")
a = cs["anatomia_coda"]
c1, c2 = st.columns(2)
with c1:
    nota(
        f"<strong>{a['sovrastime']['n']} sovrastime "
        f"({a['sovrastime']['n'] / a['n_coda'] * 100:.0f}% della coda) — colpa nostra.</strong> "
        f"Consegne arrivate in <strong>{a['sovrastime']['reale_mediana']:.0f} giorni</strong> "
        f"mediani mentre il modello ne prevedeva <strong>{a['sovrastime']['previsto_mediana']:.0f}</strong>, "
        f"su una distanza mediana di {a['sovrastime']['distanza_mediana']:.0f} km. "
        "È il problema di taratura della geografia: rotte lunghe diventate veloci."
    )
with c2:
    lente = a["consegne_oltre_30gg"]
    nota(
        f"<strong>{a['anticipi']['n']} anticipi "
        f"({a['anticipi']['n'] / a['n_coda'] * 100:.0f}%) — non colpa nostra.</strong> "
        f"Consegne realmente anomale: <strong>{a['anticipi']['reale_mediana']:.0f} giorni</strong> mediani. "
        f"Gli ordini oltre 30 giorni reali sono il {lente['quota'] * 100:.2f}% del test, il modello li "
        f"sbaglia nel {lente['quota_anticipati'] * 100:.0f}% dei casi ma pesano solo il "
        f"<strong>{lente['peso_sul_MAE'] * 100:.1f}% del MAE</strong>: non vale la pena "
        "progettare il modello attorno a loro."
    )

st.markdown("##### I nostri errori peggiori, con un'ipotesi per ciascuno")
c1, c2, c3 = st.columns([2, 2, 3])
with c1:
    tipo = st.radio("Tipo di errore", ["Tutti", "Solo ritardi (anticipi)", "Solo sovrastime"])
with c2:
    quanti = st.slider("Quanti ordini mostrare", 5, 50, 15, step=5)
with c3:
    st.write("")
    nota(
        "La colonna <em>ipotesi</em> applica una regola di lettura ai dati della riga: "
        "non è un output del modello, è il nostro modo di classificare le cause."
    )

coda = TEST.copy()
if tipo.startswith("Solo ritardi"):
    coda = coda[coda["err"] < 0]
elif tipo.startswith("Solo sovra"):
    coda = coda[coda["err"] > 0]
coda = coda.reindex(coda["err"].abs().sort_values(ascending=False).index).head(quanti)
coda["ipotesi"] = coda.apply(ipotesi_errore, axis=1)
st.dataframe(
    coda[[
        "delivery_days", "estimated_days", "pred", "err", "distance_km_mean",
        "total_weight_g", "customer_state", "main_category", "ipotesi",
    ]],
    width="stretch", hide_index=True,
    column_config={
        "delivery_days": st.column_config.NumberColumn("consegna reale", format="%.1f gg"),
        "estimated_days": st.column_config.NumberColumn("promessa oggi", format="%.1f gg"),
        "pred": st.column_config.NumberColumn("nostra previsione", format="%.1f gg"),
        "err": st.column_config.NumberColumn("errore", format="%.1f gg"),
        "distance_km_mean": st.column_config.NumberColumn("distanza", format="%.0f km"),
        "total_weight_g": st.column_config.NumberColumn("peso", format="%.0f g"),
        "customer_state": st.column_config.TextColumn("stato"),
        "main_category": st.column_config.TextColumn("categoria"),
        "ipotesi": st.column_config.TextColumn("ipotesi", width="large"),
    },
)
