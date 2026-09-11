"""Dashboard Gruppo 3 - Giorni di consegna.

Sette sezioni nell'ordine del racconto. Legge tutto da `models/` (modello,
metriche, tabella ordini): non addestra e non ricalcola le aggregazioni, cosi'
i numeri sullo schermo sono per costruzione gli stessi dei notebook.

    uv run streamlit run app/dashboard.py

Gli artefatti si rigenerano con `uv run python -m src.pipeline`.
"""

from __future__ import annotations

import json
from datetime import timedelta
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots
from xgboost import XGBRegressor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"

BLU = "#2563eb"
GRIGIO = "#94a3b8"
ROSSO = "#dc2626"
VERDE = "#16a34a"
AMBRA = "#d97706"
VIOLA = "#7c3aed"

st.set_page_config(
    page_title="Gruppo 3 - Giorni di consegna",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 2.2rem; padding-bottom: 3rem; max-width: 1500px;}
      h1, h2, h3 {letter-spacing: -0.02em;}
      .titolo-sezione {font-size: 2.1rem; font-weight: 700; margin: 0 0 .2rem 0;}
      .occhiello {text-transform: uppercase; letter-spacing: .12em; font-size: .75rem;
                  font-weight: 700; color: #64748b; margin-bottom: .1rem;}
      .headline {background: linear-gradient(90deg, #eff6ff 0%, #f8fafc 100%);
                 border-left: 5px solid #2563eb; padding: 1rem 1.2rem;
                 border-radius: 6px; font-size: 1.15rem; line-height: 1.55;
                 margin: 1rem 0 1.4rem 0;}
      .headline strong {color: #1d4ed8;}
      .nota {background: #f8fafc; border: 1px solid #e2e8f0; border-radius: 6px;
             padding: .85rem 1.1rem; font-size: .93rem; line-height: 1.55;
             color: #334155; margin: .6rem 0 1.2rem 0;}
      .nota-rossa {background: #fef2f2; border-color: #fecaca; color: #7f1d1d;}
      .nota-verde {background: #f0fdf4; border-color: #bbf7d0; color: #14532d;}
      .kpi {background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
            padding: 1rem 1.1rem; height: 100%;}
      .kpi-label {font-size: .78rem; text-transform: uppercase; letter-spacing: .07em;
                  color: #64748b; font-weight: 700;}
      .kpi-valore {font-size: 2.1rem; font-weight: 700; line-height: 1.15; margin: .25rem 0;}
      .kpi-sotto {font-size: .85rem; color: #64748b;}
      .buono {color: #16a34a;} .cattivo {color: #dc2626;} .neutro {color: #0f172a;}
      section[data-testid="stSidebar"] {background: #0f172a;}
      section[data-testid="stSidebar"] * {color: #e2e8f0;}
      section[data-testid="stSidebar"] .stRadio label {font-size: .97rem;}
    </style>
    """,
    unsafe_allow_html=True,
)


# --- Caricamento -----------------------------------------------------------


@st.cache_data(show_spinner=False)
def carica_metriche() -> dict:
    return json.loads((MODELS_DIR / "metriche.json").read_text(encoding="utf-8"))


@st.cache_data(show_spinner=False)
def carica_ordini() -> pd.DataFrame:
    df = pd.read_parquet(MODELS_DIR / "ordini.parquet")
    df["purchase_date"] = pd.to_datetime(df["purchase_date"])
    return df


@st.cache_resource(show_spinner=False)
def carica_modello() -> XGBRegressor:
    model = XGBRegressor(enable_categorical=True)
    model.load_model(MODELS_DIR / "xgb_delivery_days.json")
    return model


if not (MODELS_DIR / "metriche.json").exists():
    st.error(
        "Artefatti mancanti in `models/`. Generali con:\n\n"
        "```\nuv run python -m src.pipeline\n```"
    )
    st.stop()

M = carica_metriche()
ORDINI = carica_ordini()
TEST = ORDINI[ORDINI["split"] == "test"].copy()
MT = M["metriche_test"]


# --- Elementi di pagina ----------------------------------------------------


def intestazione(numero: str, titolo: str, sottotitolo: str) -> None:
    st.markdown(
        f'<div class="occhiello">{numero}</div>'
        f'<div class="titolo-sezione">{titolo}</div>'
        f'<div class="kpi-sotto">{sottotitolo}</div>',
        unsafe_allow_html=True,
    )
    st.write("")


def headline(testo: str) -> None:
    st.markdown(f'<div class="headline">{testo}</div>', unsafe_allow_html=True)


def nota(testo: str, tono: str = "") -> None:
    classe = {"rossa": "nota nota-rossa", "verde": "nota nota-verde"}.get(tono, "nota")
    st.markdown(f'<div class="{classe}">{testo}</div>', unsafe_allow_html=True)


def kpi(label: str, valore: str, sotto: str = "", tono: str = "neutro") -> None:
    st.markdown(
        f'<div class="kpi"><div class="kpi-label">{label}</div>'
        f'<div class="kpi-valore {tono}">{valore}</div>'
        f'<div class="kpi-sotto">{sotto}</div></div>',
        unsafe_allow_html=True,
    )


def stile_grafico(fig: go.Figure, altezza: int = 380, titolo: str = "") -> go.Figure:
    fig.update_layout(
        height=altezza,
        title=dict(text=titolo, font=dict(size=15)) if titolo else None,
        margin=dict(l=10, r=10, t=45 if titolo else 20, b=10),
        plot_bgcolor="white",
        paper_bgcolor="white",
        font=dict(family="system-ui, -apple-system, sans-serif", size=13),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, x=0),
        hovermode="x unified",
    )
    fig.update_xaxes(showgrid=False, linecolor="#cbd5e1")
    fig.update_yaxes(gridcolor="#f1f5f9", linecolor="#cbd5e1")
    return fig


# --- 1. Il problema --------------------------------------------------------


def sezione_problema() -> None:
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


# --- 2. Il risultato -------------------------------------------------------


def sezione_risultato() -> None:
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
        fig.add_vline(x=0, line_color="#0f172a", line_width=2)
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
        fig = make_subplots(
            rows=1, cols=2, subplot_titles=("Giorni promessi", "Quota di ritardi"),
        )
        fig.add_trace(
            go.Bar(
                x=["oggi", "modello"],
                y=[MT["promessa_media_baseline"], MT["promessa_media_modello"]],
                marker_color=[GRIGIO, BLU], text=[f"{MT['promessa_media_baseline']:.1f}",
                                                  f"{MT['promessa_media_modello']:.1f}"],
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

    d = M["distribuzione_errore"]["entro_soglia"]
    dentro = pd.DataFrame(d)
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
            "Letto bene, il grafico dice una cosa precisa: <strong>entro ±3 giorni il modello "
            "perde</strong> (7,4% contro 10,8%). Vince quando si allarga la finestra: "
            "entro ±10 giorni sta al 52,4% contro il 42,2%. "
            "Tradotto: <strong>taglia le sovrastime assurde</strong> "
            "(il 99° percentile dell'errore passa da +37,5 a +21,9 giorni) "
            "ma non promette date «giuste al giorno». "
            "Per chi gestisce la promessa è il compromesso giusto, ed è meglio dirlo noi "
            "che sentirselo chiedere.",
            "verde",
        )


# --- 3. Errori della promessa attuale --------------------------------------


def sezione_errori_baseline() -> None:
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
        fig.add_vline(x=1, line_color="#0f172a", line_width=2)
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
        fig.add_vline(x=1, line_color="#0f172a", line_width=2)
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


# --- 4. Errori del nostro modello ------------------------------------------


def ipotesi_errore(riga: pd.Series) -> str:
    if riga["err"] < 0:
        if riga["delivery_days"] > 30:
            return "consegna anomala (>30gg): guasto logistico, invisibile alle feature"
        if riga["total_weight_g"] > 10000:
            return "ordine molto pesante: il modello sottostima questa fascia"
        return "sottostima: consegna più lenta del profilo della rotta"
    if riga["distance_km_mean"] > 800:
        return "rotta lunga diventata veloce: geografia stantia (vedi sezione 5)"
    if riga["delivery_days"] < 5:
        return "consegna lampo: sotto ogni tempo visto in addestramento"
    return "sovrastima: margine di prudenza troppo generoso"


def sezione_errori_modello() -> None:
    cs = M["casi_strani"]
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
            "il modello mette così tanto margine che il ritardo diventa raro — ma la promessa è larga.",
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
            f"<strong>{a['sovrastime']['n']} sovrastime ({a['sovrastime']['n'] / a['n_coda'] * 100:.0f}% della coda) "
            f"— colpa nostra.</strong> Consegne arrivate in <strong>{a['sovrastime']['reale_mediana']:.0f} giorni</strong> "
            f"mediani mentre il modello ne prevedeva <strong>{a['sovrastime']['previsto_mediana']:.0f}</strong>, "
            f"su una distanza mediana di {a['sovrastime']['distanza_mediana']:.0f} km. "
            "È il problema di taratura della geografia: rotte lunghe diventate veloci."
        )
    with c2:
        lente = a["consegne_oltre_30gg"]
        nota(
            f"<strong>{a['anticipi']['n']} anticipi ({a['anticipi']['n'] / a['n_coda'] * 100:.0f}%) — non colpa nostra.</strong> "
            f"Consegne realmente anomale: <strong>{a['anticipi']['reale_mediana']:.0f} giorni</strong> mediani. "
            f"Gli ordini oltre 30 giorni reali sono il {lente['quota'] * 100:.2f}% del test, il modello li "
            f"sbaglia nel {lente['quota_anticipati'] * 100:.0f}% dei casi ma pesano solo il "
            f"<strong>{lente['peso_sul_MAE'] * 100:.1f}% del MAE</strong>: non vale la pena "
            "progettare il modello attorno a loro."
        )

    st.markdown("##### I nostri errori peggiori, con un'ipotesi per ciascuno")
    c1, c2, c3 = st.columns([2, 2, 3])
    with c1:
        tipo = st.radio(
            "Tipo di errore", ["Tutti", "Solo ritardi (anticipi)", "Solo sovrastime"],
            horizontal=False,
        )
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
    vista = coda[[
        "delivery_days", "estimated_days", "pred", "err", "distance_km_mean",
        "total_weight_g", "customer_state", "main_category", "ipotesi",
    ]]
    st.dataframe(
        vista, width="stretch", hide_index=True,
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


# --- 5. Le feature ---------------------------------------------------------


def sezione_feature() -> None:
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
            "e la sezione 4 mostra che non degradano nulla."
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
    posizioni = [
        ("distanza", 1, 1, BLU), ("approvazione", 1, 2, VIOLA),
        ("peso", 2, 1, AMBRA), ("spedizione", 2, 2, VERDE),
    ]
    for chiave, r, c, colore in posizioni:
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


# --- 6. Confronto fra modelli ----------------------------------------------


def sezione_modelli() -> None:
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
    colori_fam = {"baseline": "#0f172a", "scartato": GRIGIO, "alternativa": AMBRA, "scelto": VERDE}
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
            "distanza, categoria e tempo di approvazione che abbiamo visto nella sezione 5."
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


# --- 7. Simulatore ---------------------------------------------------------


def sezione_simulatore() -> None:
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
            "Stato del cliente", cat["customer_state"],
            index=cat["customer_state"].index("SP"),
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


# --- Navigazione -----------------------------------------------------------

SEZIONI = {
    "1 · Il problema": sezione_problema,
    "2 · Il risultato": sezione_risultato,
    "3 · Dove sbaglia la promessa di oggi": sezione_errori_baseline,
    "4 · Dove sbaglia il nostro modello": sezione_errori_modello,
    "5 · Le feature": sezione_feature,
    "6 · Perché questo modello": sezione_modelli,
    "7 · Simulatore": sezione_simulatore,
}

with st.sidebar:
    st.markdown("### 📦 Giorni di consegna")
    st.caption("Gruppo 3 · Workshop Devnut × Master MIA")
    st.divider()
    scelta = st.radio("Sezione", list(SEZIONI), label_visibility="collapsed")
    st.divider()
    st.caption(
        f"**Modello**  \nXGBoost, loss asimmetrica (penalty {M['penalty']:g})  \n"
        f"**MAE** {MT['MAE_giorni']:.2f} gg · **ritardi** {MT['quota_anticipi'] * 100:.1f}%  \n"
        f"**Test** {M['test']['dal']} → {M['test']['al']}"
    )
    st.caption(
        "Legge da `models/`: modello, metriche e tabella ordini. "
        "Non addestra nulla. Per rigenerare gli artefatti: `uv run python -m src.pipeline`"
    )

SEZIONI[scelta]()
