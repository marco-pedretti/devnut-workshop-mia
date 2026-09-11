"""Caricamento dei CSV grezzi e costruzione della tabella ordine (Gruppo 3).

Gruppo 3 - "Giorni di consegna" (regressione):
    target   = giorni tra acquisto e consegna effettiva
    baseline = stima ufficiale dell'e-commerce (giorni tra acquisto e data stimata)

Tutta la logica sulle date vive qui, in pandas (parse_dates), perche' SQLite
salva i timestamp come testo e il calcolo delle differenze e' scomodo. Il
notebook e la dashboard importano queste funzioni, non le riscrivono.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

# --- Percorsi -------------------------------------------------------------
# src/ -> radice del progetto
PROJECT_ROOT = Path(__file__).resolve().parents[1]
RAW_DIR = PROJECT_ROOT / "data" / "raw"
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

# --- Config per tabella ---------------------------------------------------
# Nome logico -> nome file CSV in data/raw.
RAW_FILES: dict[str, str] = {
    "orders": "olist_orders_dataset.csv",
    "order_items": "olist_order_items_dataset.csv",
    "order_payments": "olist_order_payments_dataset.csv",
    "order_reviews": "olist_order_reviews_dataset.csv",
    "products": "olist_products_dataset.csv",
    "customers": "olist_customers_dataset.csv",
    "sellers": "olist_sellers_dataset.csv",
    "geolocation": "olist_geolocation_dataset.csv",
    "category_translation": "product_category_name_translation.csv",
}

# Colonne da interpretare come date/timestamp per ciascuna tabella.
DATE_COLUMNS: dict[str, list[str]] = {
    "orders": [
        "order_purchase_timestamp",
        "order_approved_at",
        "order_delivered_carrier_date",
        "order_delivered_customer_date",
        "order_estimated_delivery_date",
    ],
    "order_items": ["shipping_limit_date"],
    "order_reviews": ["review_creation_date", "review_answer_timestamp"],
}


def load_raw(name: str) -> pd.DataFrame:
    """Carica una tabella grezza per nome logico (es. "orders").

    I file in data/raw non si modificano mai: qui si legge e basta, con le
    date gia' convertite in datetime.
    """
    if name not in RAW_FILES:
        raise KeyError(
            f"Tabella '{name}' sconosciuta. Disponibili: {sorted(RAW_FILES)}"
        )
    path = RAW_DIR / RAW_FILES[name]
    # utf-8-sig rimuove il BOM (presente su product_category_name_translation),
    # altrimenti la chiave di join contiene un carattere invisibile.
    return pd.read_csv(path, parse_dates=DATE_COLUMNS.get(name), encoding="utf-8-sig")


def load_all_raw() -> dict[str, pd.DataFrame]:
    """Carica tutte e nove le tabelle grezze in un dizionario nome -> DataFrame."""
    return {name: load_raw(name) for name in RAW_FILES}


# --- Aggregazioni delle relazioni 1:N ------------------------------------
# Le relazioni 1:N (order_items, order_payments) vanno portate a grana-ordine
# PRIMA del join, altrimenti il join moltiplica le righe. E' il punto dove,
# come dice la slide 6, "nasce il 90% degli errori".

def aggregate_order_items(order_items: pd.DataFrame) -> pd.DataFrame:
    """Un ordine puo' avere piu' righe articolo: aggrega a grana-ordine."""
    return (
        order_items.groupby("order_id")
        .agg(
            n_items=("order_item_id", "count"),
            n_sellers=("seller_id", "nunique"),
            n_products=("product_id", "nunique"),
            total_price=("price", "sum"),
            total_freight=("freight_value", "sum"),
        )
        .reset_index()
    )


def aggregate_payments(order_payments: pd.DataFrame) -> pd.DataFrame:
    """Un ordine puo' avere piu' transazioni: aggrega a grana-ordine."""
    return (
        order_payments.groupby("order_id")
        .agg(
            n_payments=("payment_sequential", "count"),
            max_installments=("payment_installments", "max"),
            total_payment=("payment_value", "sum"),
        )
        .reset_index()
    )


# --- Tabella ordine (Gruppo 3) -------------------------------------------

def build_order_table(save: bool = False) -> pd.DataFrame:
    """Costruisce la tabella a grana-ordine per il Gruppo 3.

    Contiene gia' il target e la baseline (dati dalla consegna spec), piu'
    alcuni aggregati di base. Le feature vere (distanza, peso/volume, carico
    del venditore, ecc.) sono lasciate come TODO: e' la parte che scrivete voi.

    Parameters
    ----------
    save : bool
        Se True, salva la tabella in data/processed/order_table.parquet.
    """
    raw = load_all_raw()
    orders = raw["orders"]

    # Solo ordini consegnati con data di consegna effettiva nota:
    # senza consegna effettiva non esiste il target.
    delivered = orders[
        (orders["order_status"] == "delivered")
        & orders["order_delivered_customer_date"].notna()
    ].copy()

    # Target: giorni tra acquisto e consegna effettiva.
    delivered["delivery_days"] = (
        delivered["order_delivered_customer_date"]
        - delivered["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400.0

    # Baseline aziendale: stima ufficiale dell'e-commerce (giorni promessi).
    delivered["estimated_days"] = (
        delivered["order_estimated_delivery_date"]
        - delivered["order_purchase_timestamp"]
    ).dt.total_seconds() / 86400.0

    # Chiave per lo split temporale: giorno di acquisto.
    delivered["purchase_date"] = delivered["order_purchase_timestamp"].dt.date

    # Aggregati 1:N gia' portati a grana-ordine (join sicuro: 1:1).
    order_table = (
        delivered.merge(aggregate_order_items(raw["order_items"]), on="order_id", how="left")
        .merge(aggregate_payments(raw["order_payments"]), on="order_id", how="left")
        .merge(
            raw["customers"][
                ["customer_id", "customer_unique_id", "customer_zip_code_prefix",
                 "customer_city", "customer_state"]
            ],
            on="customer_id",
            how="left",
        )
    )

    # TODO (feature engineering - la parte valutata):
    #   - distanza venditore-cliente da geolocation (lat/lng per CAP)
    #   - peso e volume totali da products
    #   - tempo di approvazione del pagamento (approved_at - purchase)
    #   - categoria prodotto (con traduzione EN)
    #   - carico del venditore nel periodo (aggregato causale, no leakage)
    #   - feature di calendario (mese, giorno settimana, festivi)

    if save:
        PROCESSED_DIR.mkdir(parents=True, exist_ok=True)
        order_table.to_parquet(PROCESSED_DIR / "order_table.parquet", index=False)

    return order_table


if __name__ == "__main__":
    ot = build_order_table()
    print(f"order_table: {ot.shape[0]:,} righe x {ot.shape[1]} colonne")
    print(ot[["order_id", "delivery_days", "estimated_days"]].head())
