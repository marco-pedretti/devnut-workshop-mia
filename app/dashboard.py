"""Dashboard Gruppo 3 - Giorni di consegna.

Entrypoint: configura la pagina, applica lo stile, monta la navigazione.
Il contenuto sta in `pagine/`, un file per sezione, nell'ordine del racconto.
Quello che condividono - palette, caricamento degli artefatti, mattoni di
layout - sta in `comune.py`.

    uv run streamlit run app/dashboard.py

Legge tutto da `models/` (modello, metriche, tabella ordini): non addestra e non
ricalcola le aggregazioni, cosi' i numeri sullo schermo sono per costruzione gli
stessi dei notebook. Gli artefatti si rigenerano con `uv run python -m src.pipeline`.
"""

import streamlit as st

# set_page_config deve essere la prima chiamata Streamlit della sessione, quindi
# viene prima dell'import di `comune` (che ne fa a sua volta, se mancano i dati).
st.set_page_config(
    page_title="Gruppo 3 - Giorni di consegna",
    page_icon="📦",
    layout="wide",
    initial_sidebar_state="expanded",
)

from comune import M, MT, applica_stile  # noqa: E402

applica_stile()

PAGINE = [
    st.Page("pagine/1_problema.py", title="1 · Il problema",
            url_path="problema", default=True),
    st.Page("pagine/2_risultato.py", title="2 · Il risultato",
            url_path="risultato"),
    st.Page("pagine/3_promessa_oggi.py", title="3 · La promessa di oggi",
            url_path="promessa-oggi"),
    st.Page("pagine/4_nostri_errori.py", title="4 · I nostri errori",
            url_path="nostri-errori"),
    st.Page("pagine/5_feature.py", title="5 · Le feature",
            url_path="feature"),
    st.Page("pagine/6_modelli.py", title="6 · Perché questo modello",
            url_path="modelli"),
    st.Page("pagine/7_simulatore.py", title="7 · Simulatore",
            url_path="simulatore"),
]

with st.sidebar:
    st.markdown("### 📦 Giorni di consegna")
    st.caption("Gruppo 3 · Workshop Devnut × Master MIA")
    st.divider()

pagina = st.navigation(PAGINE)

with st.sidebar:
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

pagina.run()
