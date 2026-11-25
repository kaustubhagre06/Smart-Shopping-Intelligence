"""
Data cleaning and market-basket preprocessing module.
Loads historical CSV + live SQLite transactions, cleans item tokens,
filters invalid/empty baskets, and encodes transactions into a boolean DataFrame.
"""

import os
from typing import Tuple

import pandas as pd
from mlxtend.preprocessing import TransactionEncoder

from database.db import TRANSACTIONS_CSV, get_all_baskets_from_db, get_all_products


def load_raw_transactions() -> list[list[str]]:
    """
    Load transactions primarily from SQLite (which holds seeded CSV + new checkout orders).
    Falls back to data/transactions.csv if DB has no baskets yet.
    """
    baskets = get_all_baskets_from_db()
    if baskets:
        return baskets

    if not os.path.exists(TRANSACTIONS_CSV):
        return []

    df = pd.read_csv(TRANSACTIONS_CSV)
    if df.empty or "items" not in df.columns:
        return []

    parsed: list[list[str]] = []
    for raw in df["items"].dropna():
        items = [token.strip() for token in str(raw).split(",") if token.strip()]
        if items:
            parsed.append(items)
    return parsed


def clean_baskets(raw_baskets: list[list[str]], valid_names: set[str]) -> list[list[str]]:
    """
    Clean and normalize transaction baskets:
    - Strip whitespace
    - Deduplicate items within the same transaction
    - Keep only valid catalog items
    - Drop empty baskets
    """
    cleaned: list[list[str]] = []
    for basket in raw_baskets:
        unique_items = sorted({item.strip() for item in basket if item and item.strip() in valid_names})
        if unique_items:
            cleaned.append(unique_items)
    return cleaned


def encode_baskets(cleaned_baskets: list[list[str]]) -> pd.DataFrame:
    """Convert cleaned baskets into a one-hot boolean DataFrame for Apriori."""
    if not cleaned_baskets:
        return pd.DataFrame()
    encoder = TransactionEncoder()
    encoded_array = encoder.fit(cleaned_baskets).transform(cleaned_baskets)
    return pd.DataFrame(encoded_array, columns=encoder.columns_)


def get_preprocessed_basket_data() -> Tuple[pd.DataFrame, list[list[str]]]:
    """End-to-end preprocessing pipeline returning (encoded_df, cleaned_baskets)."""
    catalog = get_all_products()
    valid_names = {p["name"] for p in catalog}
    raw_baskets = load_raw_transactions()
    cleaned_baskets = clean_baskets(raw_baskets, valid_names)
    encoded_df = encode_baskets(cleaned_baskets)
    return encoded_df, cleaned_baskets
