"""Quello che serve a tutte le pagine della dashboard.

Palette, stile, caricamento degli artefatti e i mattoni di layout (kpi, note,
intestazioni). Ogni pagina importa da qui: `from comune import M, kpi, nota`.

Il caricamento e' in cache, quindi metriche, tabella ordini e modello si leggono
una volta sola per sessione e restano disponibili passando da una pagina all'altra.
"""

from __future__ import annotations

import json
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from xgboost import XGBRegressor

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"

BLU = "#2563eb"
GRIGIO = "#94a3b8"
ROSSO = "#dc2626"
VERDE = "#16a34a"
AMBRA = "#d97706"
VIOLA = "#7c3aed"

STILE = """
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
</style>
"""


def applica_stile() -> None:
    """Va chiamata dall'entrypoint: gira a ogni rerun, quindi vale per tutte le pagine."""
    st.markdown(STILE, unsafe_allow_html=True)


# --- Caricamento degli artefatti ------------------------------------------


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
    # st.stop() interrompe il rerun: nessuna pagina arriva a leggere dati che non ci sono.
    st.error(
        "Artefatti mancanti in `models/`. Generali con:\n\n"
        "```\nuv run python -m src.pipeline\n```"
    )
    st.stop()

M = carica_metriche()
MT = M["metriche_test"]
ORDINI = carica_ordini()
TEST = ORDINI[ORDINI["split"] == "test"].copy()


# --- Mattoni di layout -----------------------------------------------------


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
