"""Pipeline end-to-end: dai CSV grezzi al modello salvato e ai dati della dashboard.

Esegue in un colpo solo quello che i notebook fanno a pezzi:

    uv run python -m src.pipeline

1. costruisce la tabella feature a grana-ordine (`src.features`);
2. applica lo split temporale usato in tutti i notebook (fit / calib / test);
3. addestra il modello scelto - XGBoost con MSE asimmetrica `penalty=5`,
   architettura tunata nella Sezione 9 di `01_eda.ipynb`;
4. calcola tutte le aggregazioni che la dashboard mostra;
5. salva in `models/` il modello, le metriche e la tabella degli ordini.

La dashboard **non addestra e non aggrega**: legge questi tre file. Cosi' i numeri
sullo schermo sono per costruzione gli stessi dei notebook, e l'app parte in un
istante anche su un proiettore.
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.inspection import permutation_importance
from sklearn.metrics import make_scorer
from xgboost import XGBRegressor

from src import features

PROJECT_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = PROJECT_ROOT / "models"

# --- Il modello scelto (Sezione 9 di 01_eda.ipynb) -------------------------

TOP_FEATURES = [
    "distance_km_mean",
    "total_freight",
    "distance_km_max",
    "customer_state",
    "approval_hours",
    "total_weight_g",
    "main_category",
]
CAT_FEATURES = ["customer_state", "main_category"]
ARCH = dict(
    subsample=0.7,
    n_estimators=300,
    min_child_weight=3,
    max_depth=5,
    learning_rate=0.013707256063767185,
    colsample_bytree=0.6,
)
PENALTY = 5.0
SEED = 42

# Colonne tenute nel parquet oltre alle feature del modello: servono alle
# analisi della dashboard (segmenti, errori peggiori, distribuzioni), non al
# modello.
EXTRA_COLS = [
    "total_volume_cm3",
    "total_price",
    "n_items",
    "n_sellers",
    "seller_load_max",
]

# --- Risultati misurati nei notebook, non ricalcolati qui ------------------
# Servono al pannello "confronto fra modelli". Rimetterli in piedi (Random
# Forest, regressione logistica per soglia, due grid di penalty) costerebbe
# minuti di addestramento a ogni export per numeri gia' validati.

# 01_eda.ipynb, Sezione 8: architettura di default (max_depth=5, lr=0.05).
GRID_PENALTY_DEFAULT = [
    # penalty, MAE_calib, anticipi_calib, MAE_test, anticipi_test
    (1.0, 5.49, 26.2, 6.04, 12.5),
    (1.5, 6.07, 22.0, 6.94, 10.0),
    (2.0, 6.60, 19.1, 7.68, 8.4),
    (2.5, 7.06, 17.0, 8.28, 7.3),
    (3.0, 7.47, 15.4, 8.82, 6.5),
    (4.0, 8.19, 13.2, 9.70, 5.4),
    (5.0, 8.84, 11.1, 10.43, 4.7),
    (7.0, 9.88, 9.2, 11.63, 3.8),
    (10.0, 11.11, 7.1, 12.94, 3.1),
]

# 01_eda.ipynb, Sezione 9: architettura scelta da RandomizedSearchCV.
GRID_PENALTY_TUNATA = [
    (1.0, 5.26, 27.0, 5.74, 12.9),
    (1.5, 5.80, 22.7, 6.61, 9.9),
    (2.0, 6.28, 19.4, 7.32, 8.1),
    (2.5, 6.70, 17.1, 7.91, 7.0),
    (3.0, 7.10, 15.2, 8.42, 6.2),
    (4.0, 7.79, 12.7, 9.28, 5.1),
    (5.0, 8.37, 11.1, 10.00, 4.4),
    (6.0, 8.89, 9.8, 10.61, 3.9),
    (7.0, 9.35, 9.0, 11.13, 3.5),
    (8.0, 9.76, 8.2, 11.61, 3.2),
    (10.0, 10.50, 7.0, 12.44, 2.7),
]

# 01_eda.ipynb, Sezioni 7-9 e 02_analisi_feature_gruppo3.ipynb, Sezione 9.
ALTRI_MODELLI = [
    dict(
        modello="Baseline (promessa attuale)",
        mae=13.13,
        anticipi=5.3,
        famiglia="baseline",
        nota="la stima ufficiale dell'e-commerce: il metro di paragone",
    ),
    dict(
        modello="Random Forest (loss simmetrica)",
        mae=5.99,
        anticipi=12.7,
        famiglia="scartato",
        nota="MAE bassissimo, ma rompe la promessa 2.4 volte piu' di oggi",
    ),
    dict(
        modello="Random Forest + margine calibrato (+9gg)",
        mae=14.10,
        anticipi=1.8,
        famiglia="scartato",
        nota="margine tarato su apr-mag: sul test e' peggio della baseline",
    ),
    dict(
        modello="Regressione logistica (95o percentile)",
        mae=27.46,
        anticipi=2.2,
        famiglia="scartato",
        nota="centra il vincolo ma con un MAE inaccettabile",
    ),
    dict(
        modello="XGBoost simmetrico (penalty=1)",
        mae=5.74,
        anticipi=12.9,
        famiglia="scartato",
        nota="stesso problema della Random Forest: ottimizza la metrica sbagliata",
    ),
    dict(
        modello="XGBoost asimmetrico penalty=4",
        mae=9.28,
        anticipi=5.1,
        famiglia="alternativa",
        nota="0.7 giorni di MAE in meno, ma sfiora il 5%",
    ),
    dict(
        modello="XGBoost asimmetrico penalty=5",
        mae=10.00,
        anticipi=4.4,
        famiglia="scelto",
        nota="il modello che presentiamo: sotto il 5% con margine",
    ),
]


def asymmetric_mse(y_true, y_pred):
    """Obiettivo custom: gli anticipi (pred < reale) pesano PENALTY volte tanto."""
    residual = y_pred - y_true
    weight = np.where(residual < 0, PENALTY, 1.0)
    return 2 * weight * residual, 2 * weight


def perdita_asimmetrica(y_true, y_pred) -> float:
    """La loss che il modello ottimizza davvero: serve per la permutation importance."""
    residual = np.asarray(y_pred) - np.asarray(y_true)
    weight = np.where(residual < 0, PENALTY, 1.0)
    return float(np.mean(weight * residual**2))


# --- Dati e split ----------------------------------------------------------


def prepara_dati() -> pd.DataFrame:
    """Tabella ordine + feature, ordinata per data e con l'etichetta di split.

    Split temporale identico a tutti i notebook: 80% piu' vecchio a train
    (di cui i primi 85% `fit` e gli ultimi 15% `calib`), 20% piu' recente a test.
    """
    ft = features.build_feature_table(save=True)
    keep = ["order_id", "purchase_date", "delivery_days", "estimated_days"]
    df = ft[keep + TOP_FEATURES + EXTRA_COLS].copy()
    df["purchase_date"] = pd.to_datetime(df["purchase_date"])
    for c in CAT_FEATURES:
        df[c] = df[c].astype("category")
    df = df.sort_values("purchase_date").reset_index(drop=True)

    n_train = int(len(df) * 0.8)
    n_fit = int(n_train * 0.85)
    split = np.full(len(df), "test", dtype=object)
    split[:n_train] = "calib"
    split[:n_fit] = "fit"
    df["split"] = split
    return df


def addestra(fit_df: pd.DataFrame) -> XGBRegressor:
    model = XGBRegressor(
        objective=asymmetric_mse,
        enable_categorical=True,
        tree_method="hist",
        random_state=SEED,
        **ARCH,
    )
    model.fit(fit_df[TOP_FEATURES], fit_df["delivery_days"])
    return model


# --- Aggregazioni per la dashboard ----------------------------------------


def _profilo(frame: pd.DataFrame, gruppo) -> pd.DataFrame:
    g = frame.groupby(gruppo, observed=True)
    return pd.DataFrame(
        {
            "n_ordini": g.size(),
            "MAE": g["abs_err"].mean(),
            "anticipi_pct": g.apply(lambda d: (d["err"] < 0).mean() * 100, include_groups=False),
            "errore_medio": g["err"].mean(),
        }
    )


def _records(frame: pd.DataFrame, nome_indice: str) -> list[dict]:
    out = frame.round(2).reset_index()
    out.columns = [nome_indice] + list(out.columns[1:])
    out[nome_indice] = out[nome_indice].astype(str)
    return out.to_dict("records")


def metriche_principali(test: pd.DataFrame) -> dict:
    risparmio = test["estimated_days"] - test["pred"]
    early = test.loc[test["err"] < 0, "err"]
    return dict(
        MAE_giorni=round(test["abs_err"].mean(), 2),
        quota_anticipi=round((test["err"] < 0).mean(), 4),
        MAE_baseline_giorni=round(test["err_baseline"].abs().mean(), 2),
        quota_anticipi_baseline=round((test["err_baseline"] < 0).mean(), 4),
        promessa_media_baseline=round(test["estimated_days"].mean(), 1),
        promessa_media_modello=round(test["pred"].mean(), 1),
        giorni_promessa_risparmiati_media=round(risparmio.mean(), 2),
        giorni_promessa_risparmiati_mediana=round(risparmio.median(), 2),
        quota_ordini_con_promessa_piu_corta=round((risparmio > 0).mean(), 3),
        consegna_reale_media=round(test["delivery_days"].mean(), 1),
        quota_sovrastime=round((test["err"] > 0).mean(), 4),
        errore_mediano=round(test["err"].median(), 2),
        ritardo_mediano_quando_anticipa=round(-early.median(), 2),
        ritardo_medio_quando_anticipa=round(-early.mean(), 2),
        ritardo_peggiore=round(-early.min(), 1),
        quota_ritardi_oltre_1gg=round((test["err"] < -1).mean(), 4),
        quota_ritardi_oltre_3gg=round((test["err"] < -3).mean(), 4),
        quota_ritardi_oltre_5gg=round((test["err"] < -5).mean(), 4),
    )


def distribuzione_errore(test: pd.DataFrame) -> dict:
    q = [0.01, 0.05, 0.25, 0.50, 0.75, 0.95, 0.99]
    percentili = [
        dict(
            percentile=f"p{int(p * 100)}",
            modello=round(test["err"].quantile(p), 1),
            baseline=round(test["err_baseline"].quantile(p), 1),
        )
        for p in q
    ]
    dentro = [
        dict(
            soglia=s,
            modello=round((test["abs_err"] <= s).mean() * 100, 1),
            baseline=round((test["err_baseline"].abs() <= s).mean() * 100, 1),
        )
        for s in (1, 2, 3, 5, 7, 10)
    ]
    return dict(percentili=percentili, entro_soglia=dentro)


def segmenti(test: pd.DataFrame) -> dict:
    per_dist = _profilo(test, "fascia_distanza")
    per_peso = _profilo(test, "fascia_peso")
    top_stati = test["customer_state"].value_counts().head(12).index
    per_stato = _profilo(test, "customer_state").loc[top_stati]
    top_cat = test["main_category"].value_counts().head(10).index
    per_cat = _profilo(test, "main_category").loc[top_cat]
    return dict(
        distanza=_records(per_dist, "fascia"),
        peso=_records(per_peso, "fascia"),
        stato=_records(per_stato, "stato"),
        categoria=_records(per_cat, "categoria"),
    )


def casi_strani(test: pd.DataFrame, fit_df: pd.DataFrame, mae: float, early: float) -> dict:
    has_na = test[TOP_FEATURES].isna().any(axis=1)
    mancanti = dict(
        per_colonna={
            c: round(v * 100, 2)
            for c, v in (test[TOP_FEATURES].isna().mean()).items()
            if v > 0
        },
        con_mancanti=dict(
            n=int(has_na.sum()),
            MAE=round(test.loc[has_na, "abs_err"].mean(), 2),
            anticipi_pct=round((test.loc[has_na, "err"] < 0).mean() * 100, 2),
        ),
        completi=dict(
            n=int((~has_na).sum()),
            MAE=round(test.loc[~has_na, "abs_err"].mean(), 2),
            anticipi_pct=round((test.loc[~has_na, "err"] < 0).mean() * 100, 2),
        ),
    )

    freq_train = fit_df["main_category"].value_counts()
    rara = test["main_category"].map(freq_train).fillna(0) < 100
    mai_viste = set(test["main_category"].dropna().unique()) - set(
        freq_train[freq_train > 0].index
    )
    rarita = dict(
        rare=dict(
            n=int(rara.sum()),
            MAE=round(test.loc[rara, "abs_err"].mean(), 2),
            anticipi_pct=round((test.loc[rara, "err"] < 0).mean() * 100, 2),
        ),
        comuni=dict(
            n=int((~rara).sum()),
            MAE=round(test.loc[~rara, "abs_err"].mean(), 2),
            anticipi_pct=round((test.loc[~rara, "err"] < 0).mean() * 100, 2),
        ),
        categorie_mai_viste=len(mai_viste),
    )

    estremi = []
    for nome, col in [
        ("distanza", "distance_km_mean"),
        ("peso", "total_weight_g"),
        ("spedizione", "total_freight"),
        ("ore approvazione", "approval_hours"),
    ]:
        mask = test[col] > test[col].quantile(0.99)
        estremi.append(
            dict(
                caso=f"{nome} > p99",
                n_ordini=int(mask.sum()),
                MAE=round(test.loc[mask, "abs_err"].mean(), 2),
                anticipi_pct=round((test.loc[mask, "err"] < 0).mean() * 100, 2),
                previsione_media=round(test.loc[mask, "pred"].mean(), 2),
            )
        )
    estremi.append(
        dict(
            caso="tutto il test",
            n_ordini=int(len(test)),
            MAE=round(mae, 2),
            anticipi_pct=round(early * 100, 2),
            previsione_media=round(test["pred"].mean(), 2),
        )
    )

    coda = test[test["abs_err"] > 20]
    sovra, ant = coda[coda["err"] > 0], coda[coda["err"] < 0]
    lente = test["delivery_days"] > 30
    anatomia = dict(
        n_coda=int(len(coda)),
        quota_coda=round(len(coda) / len(test), 4),
        sovrastime=dict(
            n=int(len(sovra)),
            reale_mediana=round(sovra["delivery_days"].median(), 1),
            previsto_mediana=round(sovra["pred"].median(), 1),
            distanza_mediana=round(sovra["distance_km_mean"].median(), 0),
        ),
        anticipi=dict(
            n=int(len(ant)),
            reale_mediana=round(ant["delivery_days"].median(), 1),
            previsto_mediana=round(ant["pred"].median(), 1),
            distanza_mediana=round(ant["distance_km_mean"].median(), 0),
        ),
        consegne_oltre_30gg=dict(
            n=int(lente.sum()),
            quota=round(lente.mean(), 4),
            quota_anticipati=round((test.loc[lente, "err"] < 0).mean(), 3),
            peso_sul_MAE=round(
                test.loc[lente, "abs_err"].sum() / test["abs_err"].sum(), 3
            ),
        ),
    )
    return dict(
        mancanti=mancanti, rarita=rarita, estremi=estremi, anatomia_coda=anatomia
    )


def errori_baseline(test: pd.DataFrame) -> dict:
    """Il decile peggiore della baseline: chi sono e come se la cava il modello (nb 03)."""
    soglia = test["err_baseline"].abs().quantile(0.90)
    difficile = test["err_baseline"].abs() >= soglia
    alto, resto = test[difficile], test[~difficile]

    numeriche = [
        "distance_km_max",
        "distance_km_mean",
        "total_freight",
        "total_price",
        "total_weight_g",
        "total_volume_cm3",
        "n_items",
        "seller_load_max",
        "approval_hours",
    ]
    confronto = [
        dict(
            feature=c,
            media_errore_alto=round(alto[c].mean(), 2),
            media_resto=round(resto[c].mean(), 2),
            rapporto=round(alto[c].mean() / resto[c].mean(), 2),
        )
        for c in numeriche
    ]
    confronto.sort(key=lambda r: -r["rapporto"])

    q_alto = alto["customer_state"].value_counts(normalize=True)
    q_resto = resto["customer_state"].value_counts(normalize=True)
    stati = [
        dict(
            stato=str(s),
            quota_errore_alto=round(q_alto.get(s, 0) * 100, 1),
            quota_resto=round(q_resto.get(s, 0) * 100, 1),
            rapporto=round(q_alto.get(s, 0) / q_resto[s], 2) if q_resto.get(s, 0) else None,
        )
        for s in q_alto.head(10).index
    ]

    def _riga(frame, nome):
        return dict(
            gruppo=nome,
            n_ordini=int(len(frame)),
            MAE_baseline=round(frame["err_baseline"].abs().mean(), 2),
            anticipi_baseline=round((frame["err_baseline"] < 0).mean() * 100, 2),
            MAE_modello=round(frame["abs_err"].mean(), 2),
            anticipi_modello=round((frame["err"] < 0).mean() * 100, 2),
        )

    return dict(
        soglia_giorni=round(soglia, 1),
        n_ordini=int(difficile.sum()),
        quota_ritardi=round((alto["err_baseline"] > 0).mean() * 100, 1),
        quota_anticipi=round((alto["err_baseline"] < 0).mean() * 100, 1),
        feature=confronto,
        stati=stati,
        confronto=[_riga(alto, "decile peggiore della baseline"), _riga(resto, "resto del test")],
        correlazione_errori=round(
            float(np.corrcoef(test["err_baseline"].abs(), test["abs_err"])[0, 1]), 2
        ),
    )


def importanza(model, calib_df: pd.DataFrame, test: pd.DataFrame) -> dict:
    scorer = make_scorer(perdita_asimmetrica, greater_is_better=False)
    viste = {}
    for nome, parte in [("calib", calib_df), ("test", test)]:
        pi = permutation_importance(
            model,
            parte[TOP_FEATURES],
            parte["delivery_days"],
            n_repeats=5,
            random_state=SEED,
            scoring=scorer,
        )
        viste[nome] = dict(zip(TOP_FEATURES, np.round(pi.importances_mean, 2)))

    gain = model.get_booster().get_score(importance_type="gain")
    righe = [
        dict(
            feature=f,
            gain=round(float(gain.get(f, 0.0)), 1),
            utilita_calib=float(viste["calib"][f]),
            utilita_test=float(viste["test"][f]),
        )
        for f in TOP_FEATURES
    ]
    righe.sort(key=lambda r: -r["gain"])

    # Perche' la geografia "gira": errore medio per fascia nei due periodi.
    fasce = []
    for nome, parte in [("calib", calib_df), ("test", test)]:
        p = parte.copy()
        p["err"] = model.predict(p[TOP_FEATURES]) - p["delivery_days"]
        p["fascia"] = pd.cut(
            p["distance_km_mean"],
            [-1, 200, 1000, np.inf],
            labels=["<200km", "200-1000km", ">1000km"],
        )
        fasce.append(p.groupby("fascia", observed=True)["err"].mean().rename(nome))
    deriva = pd.concat(fasce, axis=1).round(1).reset_index()
    deriva["fascia"] = deriva["fascia"].astype(str)

    return dict(righe=righe, errore_per_fascia=deriva.to_dict("records"))


def sensitivita(model, test: pd.DataFrame) -> dict:
    """Partial dependence calcolata a mano (l'obiettivo custom confonde sklearn)."""
    base = test.sample(min(3000, len(test)), random_state=SEED)[TOP_FEATURES].copy()
    griglie = {
        "distance_km_mean": np.linspace(0, 3000, 25),
        "total_freight": np.linspace(0, 120, 25),
        "total_weight_g": np.linspace(0, 20000, 25),
        "approval_hours": np.linspace(0, 120, 25),
    }
    out = {}
    for feat, grid in griglie.items():
        valori = [float(model.predict(base.assign(**{feat: v})).mean()) for v in grid]
        out[feat] = dict(
            x=[float(v) for v in grid],
            y=[round(v, 2) for v in valori],
            p1=round(float(test[feat].quantile(0.01)), 1),
            p99=round(float(test[feat].quantile(0.99)), 1),
        )
    return out


def analisi_feature(df: pd.DataFrame) -> dict:
    """Perche' proprio queste feature (materiale del notebook 02)."""
    numeriche = [
        "distance_km_mean",
        "distance_km_max",
        "total_weight_g",
        "total_volume_cm3",
        "approval_hours",
        "total_freight",
        "seller_load_max",
    ]
    spearman = [
        dict(
            feature=c,
            copertura=round(df[c].notna().mean() * 100, 1),
            spearman=round(float(df[c].corr(df["delivery_days"], method="spearman")), 3),
            mediana=round(float(df[c].median()), 1),
        )
        for c in numeriche
    ]
    spearman.sort(key=lambda r: -abs(r["spearman"]))

    # Perche' teniamo sia la media sia il max della distanza.
    multi = df["n_sellers"] > 1
    diverse = (df["distance_km_max"] - df["distance_km_mean"]).abs() > 1
    mean_vs_max = dict(
        correlazione=round(
            float(df["distance_km_mean"].corr(df["distance_km_max"])), 3
        ),
        quota_ordini_multi_venditore=round(float(multi.mean()) * 100, 1),
        quota_ordini_con_distanze_diverse=round(float(diverse.mean()) * 100, 1),
        spearman_mean=round(
            float(df["distance_km_mean"].corr(df["delivery_days"], method="spearman")), 3
        ),
        spearman_max=round(
            float(df["distance_km_max"].corr(df["delivery_days"], method="spearman")), 3
        ),
        delta_medio_quando_diverse=round(
            float((df.loc[diverse, "distance_km_max"] - df.loc[diverse, "distance_km_mean"]).mean()), 1
        ),
        consegna_media_multi=round(float(df.loc[multi, "delivery_days"].mean()), 1),
        consegna_media_singolo=round(float(df.loc[~multi, "delivery_days"].mean()), 1),
    )

    def _fasce(col, bins, labels):
        b = pd.cut(df[col], bins, labels=labels)
        g = df.groupby(b, observed=True)["delivery_days"]
        out = pd.DataFrame(
            {"media": g.mean().round(1), "mediana": g.median().round(1), "n_ordini": g.size()}
        ).reset_index()
        out.columns = ["fascia", "media", "mediana", "n_ordini"]
        out["fascia"] = out["fascia"].astype(str)
        return out.to_dict("records")

    fasce = dict(
        distanza=_fasce(
            "distance_km_mean",
            [-1, 50, 200, 500, 1000, 2000, np.inf],
            ["<50km", "50-200", "200-500", "500-1000", "1000-2000", ">2000km"],
        ),
        peso=_fasce(
            "total_weight_g",
            [-1, 250, 500, 1100, 2800, np.inf],
            ["<250g", "250-500g", "500g-1.1kg", "1.1-2.8kg", ">2.8kg"],
        ),
        approvazione=_fasce(
            "approval_hours",
            [-1, 1, 6, 24, 72, np.inf],
            ["<1h", "1-6h", "6-24h", "1-3g", ">3g"],
        ),
        spedizione=_fasce(
            "total_freight",
            [-1, 10, 15, 20, 30, np.inf],
            ["<10 R$", "10-15", "15-20", "20-30", ">30 R$"],
        ),
    )

    g = df.groupby("main_category", observed=True)["delivery_days"]
    cat = pd.DataFrame({"media": g.mean().round(1), "n_ordini": g.size()})
    cat = cat[cat["n_ordini"] >= 300].sort_values("media")
    categorie = dict(
        veloci=cat.head(5).reset_index().rename(columns={"main_category": "categoria"}).to_dict("records"),
        lente=cat.tail(5).reset_index().rename(columns={"main_category": "categoria"}).to_dict("records"),
    )

    return dict(
        spearman=spearman,
        mean_vs_max=mean_vs_max,
        fasce=fasce,
        categorie=categorie,
        nulli={
            c: round(float(df[c].isna().mean()) * 100, 2)
            for c in TOP_FEATURES
            if df[c].isna().any()
        },
    )


def deriva_temporale(df: pd.DataFrame) -> list[dict]:
    """Le consegne accelerano nel tempo: il fatto che regge mezza narrazione."""
    m = df.copy()
    m["mese"] = m["purchase_date"].dt.to_period("M").astype(str)
    g = m.groupby("mese", observed=True)
    out = pd.DataFrame(
        {
            "consegna_media": g["delivery_days"].mean().round(2),
            "promessa_media": g["estimated_days"].mean().round(2),
            "n_ordini": g.size(),
        }
    ).reset_index()
    return out[out["n_ordini"] >= 50].to_dict("records")


# --- Export ----------------------------------------------------------------


def _json_default(o):
    """numpy/pandas -> tipi Python, altrimenti json.dumps si ferma sui float32."""
    if isinstance(o, np.generic):
        return o.item()
    if isinstance(o, (np.ndarray, pd.Index)):
        return list(o)
    if isinstance(o, pd.Timestamp):
        return str(o.date())
    raise TypeError(f"non serializzabile: {type(o).__name__}")


def esporta() -> dict:
    df = prepara_dati()
    fit_df = df[df["split"] == "fit"]
    calib_df = df[df["split"] == "calib"]
    test = df[df["split"] == "test"].copy()

    model = addestra(fit_df)
    # float64: XGBoost restituisce float32 e i round finirebbero nel JSON con
    # una coda di decimali spuri (18.200000762939453).
    test["pred"] = model.predict(test[TOP_FEATURES]).astype("float64")
    test["err"] = test["pred"] - test["delivery_days"]
    test["abs_err"] = test["err"].abs()
    test["err_baseline"] = test["estimated_days"] - test["delivery_days"]
    test["fascia_distanza"] = pd.cut(
        test["distance_km_mean"],
        [-1, 50, 200, 500, 1000, 2000, np.inf],
        labels=["<50km", "50-200", "200-500", "500-1000", "1000-2000", ">2000km"],
    )
    test["fascia_peso"] = pd.cut(
        test["total_weight_g"],
        [-1, 500, 2000, 10000, np.inf],
        labels=["<0.5kg", "0.5-2kg", "2-10kg", ">10kg"],
    )

    mae = float(test["abs_err"].mean())
    early = float((test["err"] < 0).mean())
    print(f"fit {len(fit_df):,} | calib {len(calib_df):,} | test {len(test):,}")
    print(f"modello : MAE {mae:.2f} gg | anticipi {early:.1%}")
    print(f"baseline: MAE {test['err_baseline'].abs().mean():.2f} gg | "
          f"anticipi {(test['err_baseline'] < 0).mean():.1%}")

    num_features = [c for c in TOP_FEATURES if c not in CAT_FEATURES]
    intervalli = {
        c: {
            "p1": round(float(test[c].quantile(0.01)), 2),
            "p25": round(float(test[c].quantile(0.25)), 2),
            "mediana": round(float(test[c].median()), 2),
            "p75": round(float(test[c].quantile(0.75)), 2),
            "p99": round(float(test[c].quantile(0.99)), 2),
        }
        for c in num_features
    }

    metriche = dict(
        modello="XGBoost MSE asimmetrica (penalty=5), architettura Sez. 9 di 01_eda",
        nota="stima un livello prudente (expectile ~83%), non il giorno tipico",
        penalty=PENALTY,
        architettura={k: (round(v, 6) if isinstance(v, float) else v) for k, v in ARCH.items()},
        addestrato_su=dict(
            righe=int(len(fit_df)),
            dal=str(fit_df["purchase_date"].min().date()),
            al=str(fit_df["purchase_date"].max().date()),
        ),
        calibrazione=dict(
            righe=int(len(calib_df)),
            dal=str(calib_df["purchase_date"].min().date()),
            al=str(calib_df["purchase_date"].max().date()),
        ),
        test=dict(
            righe=int(len(test)),
            dal=str(test["purchase_date"].min().date()),
            al=str(test["purchase_date"].max().date()),
        ),
        metriche_test=metriche_principali(test),
        distribuzione_errore=distribuzione_errore(test),
        segmenti=segmenti(test),
        segmenti_sopra_soglia_5pct=["distanza < 50km", "peso > 10kg", "stato BA", "stato SP"],
        casi_strani=casi_strani(test, fit_df, mae, early),
        errori_baseline=errori_baseline(test),
        importanza=importanza(model, calib_df, test),
        sensitivita=sensitivita(model, test),
        analisi_feature=analisi_feature(df),
        deriva_temporale=deriva_temporale(df),
        confronto_modelli=ALTRI_MODELLI,
        grid_penalty=dict(
            default=[
                dict(zip(["penalty", "mae_calib", "anticipi_calib", "mae_test", "anticipi_test"], r))
                for r in GRID_PENALTY_DEFAULT
            ],
            tunata=[
                dict(zip(["penalty", "mae_calib", "anticipi_calib", "mae_test", "anticipi_test"], r))
                for r in GRID_PENALTY_TUNATA
            ],
        ),
        features=TOP_FEATURES,
        features_categoriche=CAT_FEATURES,
        categorie={c: sorted(map(str, df[c].cat.categories)) for c in CAT_FEATURES},
        intervalli_input=intervalli,
    )

    MODELS_DIR.mkdir(exist_ok=True)
    model.save_model(MODELS_DIR / "xgb_delivery_days.json")
    (MODELS_DIR / "metriche.json").write_text(
        json.dumps(metriche, indent=2, ensure_ascii=False, default=_json_default),
        encoding="utf-8",
    )

    # Tabella ordini: tutto il periodo per le distribuzioni, previsioni sul solo test.
    ordini = df.copy()
    ordini["pred"] = np.nan
    ordini.loc[test.index, "pred"] = test["pred"]
    ordini.loc[test.index, "err"] = test["err"]
    ordini.loc[test.index, "err_baseline"] = test["err_baseline"]
    for c in CAT_FEATURES:
        ordini[c] = ordini[c].astype(str)
    ordini.to_parquet(MODELS_DIR / "ordini.parquet", index=False)

    for nome in ("xgb_delivery_days.json", "metriche.json", "ordini.parquet"):
        kb = (MODELS_DIR / nome).stat().st_size / 1024
        print(f"  models/{nome}  ({kb:,.0f} KB)")
    return metriche


if __name__ == "__main__":
    esporta()
