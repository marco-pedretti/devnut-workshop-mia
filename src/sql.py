"""Layer SQL per esplorare le tabelle con query invece che solo con pandas.

Usa sqlite3 (libreria standard: nessuna installazione), quindi funziona in
qualsiasi ambiente senza toccare uv.lock. Le nove tabelle grezze e la tabella
ordine del Gruppo 3 vengono caricate in un database in memoria.

Esempio
-------
    from src.sql import query, list_tables

    list_tables()
    query("SELECT order_status, COUNT(*) AS n FROM orders GROUP BY order_status")

Nota sulle date: SQLite salva i timestamp come testo. Le colonne data-derivate
(delivery_days, estimated_days) sono gia' calcolate in pandas dentro
build_order_table, quindi in SQL le trovate come numeri gia' pronti.
"""

from __future__ import annotations

import sqlite3

import pandas as pd

from . import data_loader

# Connessione condivisa a livello di modulo: costruita una sola volta,
# riusata da tutte le chiamate a query().
_CONNECTION: sqlite3.Connection | None = None


def build_connection(include_order_table: bool = True) -> sqlite3.Connection:
    """Crea un database SQLite in memoria con le tabelle caricate.

    Parameters
    ----------
    include_order_table : bool
        Se True, aggiunge la tabella ordine del Gruppo 3 (con target e baseline).
    """
    con = sqlite3.connect(":memory:")

    for name, df in data_loader.load_all_raw().items():
        df.to_sql(name, con, index=False, if_exists="replace")

    if include_order_table:
        order_table = data_loader.build_order_table()
        order_table.to_sql("order_table", con, index=False, if_exists="replace")

    return con


def get_connection() -> sqlite3.Connection:
    """Restituisce la connessione condivisa, costruendola alla prima chiamata."""
    global _CONNECTION
    if _CONNECTION is None:
        _CONNECTION = build_connection()
    return _CONNECTION


def query(sql: str, con: sqlite3.Connection | None = None) -> pd.DataFrame:
    """Esegue una query SQL e restituisce il risultato come DataFrame.

    Se non passi una connessione, usa quella condivisa del modulo.
    """
    return pd.read_sql_query(sql, con or get_connection())


def list_tables(con: sqlite3.Connection | None = None) -> pd.DataFrame:
    """Elenca le tabelle disponibili nel database."""
    return query(
        "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name", con
    )


def reset_connection() -> None:
    """Chiude e dimentica la connessione condivisa (ricostruita al prossimo uso)."""
    global _CONNECTION
    if _CONNECTION is not None:
        _CONNECTION.close()
        _CONNECTION = None


if __name__ == "__main__":
    print("Tabelle disponibili:")
    print(list_tables().to_string(index=False))
    print()
    print(query("SELECT order_status, COUNT(*) AS n FROM orders GROUP BY order_status"))
