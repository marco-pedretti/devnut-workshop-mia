"""Feature consigliate nella slide per il Gruppo 3 (Giorni di consegna).

Slide 10 - piste sulle feature:
    distanza venditore-cliente, peso e volume, tempo di approvazione del
    pagamento, categoria, carico del venditore nel periodo.

Ogni funzione costruisce UNA famiglia di feature a grana-ordine e lascia
esplicito il punto di decisione (quale aggregato, quale finestra, perche'),
cosi' e' difendibile nel README di sintesi.

Vincoli:
- Il target `delivery_days` e' la consegna dell'ULTIMO articolo: per gli
  aggregati per-articolo riportiamo sia la media sia il max (il venditore piu'
  lontano/lento e' il collo di bottiglia).
- Il carico del venditore usa una finestra temporale STRETTAMENTE causale
  (solo ordini precedenti all'acquisto corrente): niente leakage.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import data_loader

EARTH_RADIUS_KM = 6371.0


# --- Geolocalizzazione ----------------------------------------------------

def zip_centroids(geolocation: pd.DataFrame) -> pd.DataFrame:
    """Un punto (lat, lng) per prefisso CAP.

    geolocation ha molte righe per CAP: usiamo la MEDIANA (robusta agli
    outlier di lat/lng piu' della media).
    """
    return (
        geolocation.groupby("geolocation_zip_code_prefix")
        .agg(lat=("geolocation_lat", "median"), lng=("geolocation_lng", "median"))
        .reset_index()
        .rename(columns={"geolocation_zip_code_prefix": "zip_prefix"})
    )


def _haversine_km(lat1, lng1, lat2, lng2):
    """Distanza sulla superficie terrestre (km) tra array di coordinate."""
    lat1, lng1, lat2, lng2 = map(np.radians, (lat1, lng1, lat2, lng2))
    dlat = lat2 - lat1
    dlng = lng2 - lng1
    a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlng / 2) ** 2
    return 2 * EARTH_RADIUS_KM * np.arcsin(np.sqrt(a))


def distance_features(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Distanza venditore-cliente per ordine: media e max sugli articoli.

    Decisione: media E max. Il target e' l'arrivo dell'ultimo articolo, quindi
    il venditore piu' lontano (max) e' spesso piu' predittivo della media.
    """
    centroids = zip_centroids(raw["geolocation"])

    # Un articolo = un venditore. Attacchiamo il CAP del venditore.
    items = raw["order_items"][["order_id", "seller_id"]].merge(
        raw["sellers"][["seller_id", "seller_zip_code_prefix"]], on="seller_id", how="left"
    )
    # Il cliente e' uno per ordine: CAP cliente via orders -> customers.
    cust = raw["orders"][["order_id", "customer_id"]].merge(
        raw["customers"][["customer_id", "customer_zip_code_prefix"]],
        on="customer_id", how="left",
    )
    items = items.merge(cust[["order_id", "customer_zip_code_prefix"]], on="order_id", how="left")

    # Coordinate dei due estremi.
    items = items.merge(
        centroids.rename(columns={"zip_prefix": "seller_zip_code_prefix", "lat": "s_lat", "lng": "s_lng"}),
        on="seller_zip_code_prefix", how="left",
    ).merge(
        centroids.rename(columns={"zip_prefix": "customer_zip_code_prefix", "lat": "c_lat", "lng": "c_lng"}),
        on="customer_zip_code_prefix", how="left",
    )

    items["distance_km"] = _haversine_km(items["s_lat"], items["s_lng"], items["c_lat"], items["c_lng"])

    return (
        items.groupby("order_id")
        .agg(distance_km_mean=("distance_km", "mean"), distance_km_max=("distance_km", "max"))
        .reset_index()
    )


# --- Peso e volume --------------------------------------------------------

def weight_volume_features(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Peso e volume totali dell'ordine (somma sugli articoli)."""
    products = raw["products"].copy()
    products["volume_cm3"] = (
        products["product_length_cm"] * products["product_height_cm"] * products["product_width_cm"]
    )
    items = raw["order_items"][["order_id", "product_id"]].merge(
        products[["product_id", "product_weight_g", "volume_cm3"]], on="product_id", how="left"
    )
    return (
        items.groupby("order_id")
        .agg(total_weight_g=("product_weight_g", "sum"), total_volume_cm3=("volume_cm3", "sum"))
        .reset_index()
    )


# --- Tempo di approvazione del pagamento ---------------------------------

def payment_approval_features(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Ore tra acquisto e approvazione del pagamento (noto vicino al checkout)."""
    orders = raw["orders"]
    approval_h = (
        orders["order_approved_at"] - orders["order_purchase_timestamp"]
    ).dt.total_seconds() / 3600.0
    return pd.DataFrame({"order_id": orders["order_id"], "approval_hours": approval_h})


# --- Categoria ------------------------------------------------------------

def category_features(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Categoria principale dell'ordine (la piu' frequente tra gli articoli), in EN.

    Decisione: categoria prevalente (mode). Un ordine puo' contenere piu'
    categorie; per un target a grana-ordine ne serve una sola.
    """
    trans = raw["category_translation"]
    items = raw["order_items"][["order_id", "product_id"]].merge(
        raw["products"][["product_id", "product_category_name"]], on="product_id", how="left"
    ).merge(trans, on="product_category_name", how="left")

    # Categoria prevalente per ordine (prima in caso di parita').
    def _mode(s: pd.Series):
        m = s.dropna()
        return m.mode().iloc[0] if not m.empty else np.nan

    cat = (
        items.groupby("order_id")["product_category_name_english"]
        .apply(_mode)
        .reset_index()
        .rename(columns={"product_category_name_english": "main_category"})
    )
    return cat


# --- Carico del venditore (causale) --------------------------------------

def seller_load_features(raw: dict[str, pd.DataFrame], window_days: int = 30) -> pd.DataFrame:
    """Carico del venditore: quanti ordini aveva gia' preso nei `window_days`
    precedenti all'acquisto corrente.

    STRETTAMENTE CAUSALE: conta solo ordini con timestamp < quello corrente
    (ordine corrente escluso). Il bucket per mese di calendario NON e' causale
    perche' includerebbe ordini successivi nello stesso mese.

    Decisione: finestra di 30 giorni. Aggregato a grana-ordine con media e max
    (un ordine multi-venditore ha piu' carichi).
    """
    # Un record per (ordine, venditore) con il timestamp di acquisto.
    sv = raw["order_items"][["order_id", "seller_id"]].drop_duplicates().merge(
        raw["orders"][["order_id", "order_purchase_timestamp"]], on="order_id", how="left"
    )
    sv = sv.dropna(subset=["order_purchase_timestamp"])
    window = np.timedelta64(window_days, "D")

    def _prior_count(group: pd.DataFrame) -> pd.Series:
        ts = group["order_purchase_timestamp"].to_numpy("datetime64[ns]")
        order = np.argsort(ts, kind="mergesort")
        ts_sorted = ts[order]
        # Ordini strettamente precedenti: [t - window, t)
        hi = np.searchsorted(ts_sorted, ts_sorted, side="left")          # esclude il corrente e i pari-tempo
        lo = np.searchsorted(ts_sorted, ts_sorted - window, side="left")  # inizio finestra
        counts = np.empty(len(ts), dtype="int64")
        counts[order] = hi - lo
        return pd.Series(counts, index=group.index)

    sv["seller_load"] = (
        sv.groupby("seller_id", group_keys=False)[["order_purchase_timestamp"]]
        .apply(_prior_count)
    )
    return (
        sv.groupby("order_id")
        .agg(seller_load_mean=("seller_load", "mean"), seller_load_max=("seller_load", "max"))
        .reset_index()
    )


# --- Calendario ------------------------------------------------------------

def calendar_features(raw: dict[str, pd.DataFrame]) -> pd.DataFrame:
    """Feature di calendario dell'acquisto: mese, giorno settimana, weekend.

    Note al checkout (nessun leakage): dipendono solo da `order_purchase_timestamp`.
    """
    ts = raw["orders"]["order_purchase_timestamp"]
    return pd.DataFrame({
        "order_id": raw["orders"]["order_id"],
        "purchase_month": ts.dt.month,
        "purchase_dayofweek": ts.dt.dayofweek,
        "purchase_is_weekend": ts.dt.dayofweek.isin([5, 6]).astype(int),
    })


# --- Storico della rotta (target encoding causale) ------------------------

def _causal_prior_mean(frame: pd.DataFrame, group_cols: list[str], window_days: int | None = None):
    """Media del target dentro ogni gruppo, usando SOLO consegne gia' concluse.

    Per ogni riga considera le consegne dello stesso gruppo con
    `delivered_ts < purchase_ts` della riga corrente: e' l'informazione davvero
    disponibile al checkout. Ordinare per data di acquisto NON basterebbe (un
    ordine acquistato prima ma consegnato dopo non e' ancora osservabile).

    `window_days` limita la media alle consegne concluse negli ultimi N giorni.
    Serve perche' i tempi di consegna calano nel tempo (vedi 01_eda, Sez. 8): una
    media espandente su tutta la storia resta ancorata al passato e sovrastima.
    """
    purchase = frame["purchase_ts"].to_numpy("datetime64[ns]")
    delivered = frame["delivered_ts"].to_numpy("datetime64[ns]")
    y = frame["delivery_days"].to_numpy(dtype=float)

    mean = np.full(len(frame), np.nan)
    n_prior = np.zeros(len(frame), dtype="int64")

    for positions in frame.groupby(group_cols, observed=True).indices.values():
        order = np.argsort(delivered[positions], kind="mergesort")
        d_sorted = delivered[positions][order]
        csum = np.concatenate(([0.0], np.cumsum(y[positions][order])))
        p = purchase[positions]
        hi = np.searchsorted(d_sorted, p, side="left")
        if window_days is None:
            lo = np.zeros_like(hi)
        else:
            lo = np.searchsorted(d_sorted, p - np.timedelta64(window_days, "D"), side="left")
        n = hi - lo
        n_prior[positions] = n
        mean[positions] = np.where(n > 0, (csum[hi] - csum[lo]) / np.maximum(n, 1), np.nan)

    return mean, n_prior


def route_history_features(raw: dict[str, pd.DataFrame], window_days: int | None = 60) -> pd.DataFrame:
    """Giorni di consegna storici sulla rotta (stato venditore -> stato cliente).

    Decisione: target encoding causale, su finestra mobile di `window_days`.
    L'analisi errori (notebook 03) ha mostrato che alcuni stati cliente (RJ, PA,
    PE) sbagliano molto piu' di quanto la sola distanza in linea d'aria spieghi:
    la media storica della rotta cattura i fattori logistici (congestione, hub)
    che la distanza ignora.

    La finestra mobile e' il punto chiave: con la media espandente la feature
    PEGGIORA il modello (resta ancorata ai tempi lunghi del 2016-17 mentre i
    tempi reali calano). Confronto misurato nel notebook 04.

    Oltre alla rotta teniamo il livello piu' aggregato (solo stato cliente) come
    ripiego per le rotte rare, e il numero di consegne osservate nella finestra
    come misura di affidabilita' della media.
    """
    orders = raw["orders"]
    delivered = orders[
        (orders["order_status"] == "delivered")
        & orders["order_delivered_customer_date"].notna()
    ][["order_id", "customer_id", "order_purchase_timestamp", "order_delivered_customer_date"]]

    frame = delivered.merge(
        raw["customers"][["customer_id", "customer_state"]], on="customer_id", how="left"
    )

    # Stato del venditore prevalente dell'ordine (gli ordini multi-venditore sono ~3%).
    seller_state = (
        raw["order_items"][["order_id", "seller_id"]]
        .merge(raw["sellers"][["seller_id", "seller_state"]], on="seller_id", how="left")
        .dropna(subset=["seller_state"])
        .groupby(["order_id", "seller_state"], observed=True)
        .size()
        .reset_index(name="n")
        .sort_values(["order_id", "n"], ascending=[True, False])
        .drop_duplicates("order_id")[["order_id", "seller_state"]]
    )
    frame = frame.merge(seller_state, on="order_id", how="left")

    frame["purchase_ts"] = frame["order_purchase_timestamp"]
    frame["delivered_ts"] = frame["order_delivered_customer_date"]
    frame["delivery_days"] = (
        frame["delivered_ts"] - frame["purchase_ts"]
    ).dt.total_seconds() / 86400.0
    frame["route"] = frame["seller_state"].astype(str) + "->" + frame["customer_state"].astype(str)

    route_mean, route_n = _causal_prior_mean(frame, ["route"], window_days)
    state_mean, _ = _causal_prior_mean(frame, ["customer_state"], window_days)

    return pd.DataFrame({
        "order_id": frame["order_id"],
        "route_prior_days": route_mean,
        "route_prior_n": route_n,
        "cust_state_prior_days": state_mean,
    })


# --- Tabella feature completa --------------------------------------------

def build_feature_table(save: bool = False) -> pd.DataFrame:
    """Tabella ordine (target + baseline) arricchita con le feature consigliate."""
    raw = data_loader.load_all_raw()
    table = data_loader.build_order_table()

    for feats in (
        distance_features(raw),
        weight_volume_features(raw),
        payment_approval_features(raw),
        category_features(raw),
        seller_load_features(raw),
        calendar_features(raw),
        route_history_features(raw),
    ):
        table = table.merge(feats, on="order_id", how="left")

    if save:
        data_loader.PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        table.to_parquet(data_loader.PROCESSED_DIR / "feature_table.parquet", index=False)
    return table


if __name__ == "__main__":
    t = build_feature_table()
    print(f"feature_table: {t.shape[0]:,} righe x {t.shape[1]} colonne")
