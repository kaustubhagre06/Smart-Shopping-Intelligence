"""
Apriori Machine Learning Recommendation Engine.
Mines frequent itemsets and association rules (support, confidence, lift),
and generates product recommendations with human-readable explanations.
"""

from typing import Any

import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules

from database.db import get_all_products
from ml.preprocessing import get_preprocessed_basket_data


class AprioriRecommender:
    """Stateful Apriori recommendation model trained on live + historical baskets."""

    def __init__(self, min_support: float = 0.025, min_confidence: float = 0.25, min_lift: float = 1.05):
        self.min_support = min_support
        self.min_confidence = min_confidence
        self.min_lift = min_lift
        self.baskets: list[list[str]] = []
        self.encoded_df: pd.DataFrame = pd.DataFrame()
        self.frequent_itemsets: pd.DataFrame = pd.DataFrame()
        self.rules: pd.DataFrame = pd.DataFrame()
        self.product_lookup: dict[str, dict[str, Any]] = {}

    def train(
        self,
        min_support: float | None = None,
        min_confidence: float | None = None,
        min_lift: float | None = None,
    ) -> dict[str, Any]:
        """Run preprocessing, Apriori frequent itemset mining, and association rule generation."""
        if min_support is not None:
            self.min_support = max(0.005, min(0.8, float(min_support)))
        if min_confidence is not None:
            self.min_confidence = max(0.05, min(1.0, float(min_confidence)))
        if min_lift is not None:
            self.min_lift = max(0.5, min(10.0, float(min_lift)))

        catalog = get_all_products()
        self.product_lookup = {p["name"]: p for p in catalog}

        self.encoded_df, self.baskets = get_preprocessed_basket_data()
        if self.encoded_df.empty or len(self.baskets) < 2:
            self.frequent_itemsets = pd.DataFrame()
            self.rules = pd.DataFrame()
            return self.summary()

        self.frequent_itemsets = apriori(
            self.encoded_df,
            min_support=self.min_support,
            use_colnames=True,
            max_len=4,
        )

        if self.frequent_itemsets.empty:
            self.rules = pd.DataFrame()
            return self.summary()

        rules_df = association_rules(
            self.frequent_itemsets,
            metric="confidence",
            min_threshold=self.min_confidence,
        )
        if not rules_df.empty:
            rules_df = rules_df[rules_df["lift"] >= self.min_lift].copy()
            rules_df = rules_df.sort_values(
                by=["lift", "confidence", "support"], ascending=[False, False, False]
            ).reset_index(drop=True)

        self.rules = rules_df
        return self.summary()

    def ensure_trained(self) -> None:
        if self.rules.empty and not self.baskets:
            self.train()

    def summary(self) -> dict[str, Any]:
        return {
            "total_transactions": len(self.baskets),
            "unique_items": len(self.encoded_df.columns) if not self.encoded_df.empty else 0,
            "frequent_itemsets_count": int(len(self.frequent_itemsets)),
            "rules_count": int(len(self.rules)),
            "min_support": self.min_support,
            "min_confidence": self.min_confidence,
            "min_lift": self.min_lift,
        }

    def recommend_for_items(
        self,
        selected_items: list[str],
        top_n: int = 6,
        min_support: float | None = None,
        min_confidence: float | None = None,
    ) -> dict[str, Any]:
        """
        Recommend products from trained association rules for a list of selected/cart items.
        Rules match whenever rule.antecedents is a non-empty subset of selected_items
        and rule.consequents contains items not already in selected_items.
        """
        if min_support is not None or min_confidence is not None:
            self.train(
                min_support=min_support if min_support is not None else self.min_support,
                min_confidence=min_confidence if min_confidence is not None else self.min_confidence,
            )
        else:
            self.ensure_trained()

        clean_selected = [item.strip() for item in selected_items if item and item.strip() in self.product_lookup]
        selected_set = set(clean_selected)

        if not selected_set:
            return {
                "selected": [],
                "recommendations": [],
                "message": "Select one or more products to generate Apriori association recommendations.",
                "model_summary": self.summary(),
            }

        if self.rules.empty:
            return {
                "selected": clean_selected,
                "recommendations": [],
                "message": "No association rules meet the current support/confidence thresholds. Try lowering the thresholds.",
                "model_summary": self.summary(),
            }

        candidates: dict[str, dict[str, Any]] = {}

        for _, row in self.rules.iterrows():
            antecedents = set(row["antecedents"])
            consequents = set(row["consequents"])

            # Rule applies if user has everything in antecedents, and consequents offer new products
            if not antecedents.issubset(selected_set):
                continue

            new_items = consequents - selected_set
            if not new_items:
                continue

            ant_list = sorted(antecedents)
            ant_label = " & ".join(ant_list)

            for item_name in new_items:
                if item_name not in self.product_lookup:
                    continue

                lift = float(row["lift"])
                confidence = float(row["confidence"])
                support = float(row["support"])
                score = lift * 0.6 + confidence * 0.4

                existing = candidates.get(item_name)
                if existing is None or score > existing["_score"]:
                    product = dict(self.product_lookup[item_name])
                    candidates[item_name] = {
                        "_score": score,
                        "product": product,
                        "matched_antecedents": ant_list,
                        "support": round(support, 4),
                        "confidence": round(confidence, 4),
                        "lift": round(lift, 3),
                        "support_pct": round(support * 100, 1),
                        "confidence_pct": round(confidence * 100, 1),
                        "explanation": (
                            f"Customers who bought {ant_label} also frequently bought {item_name}."
                        ),
                    }

        ranked = sorted(
            candidates.values(),
            key=lambda x: (x["lift"], x["confidence"], x["support"]),
            reverse=True,
        )[:top_n]

        for rec in ranked:
            rec.pop("_score", None)

        message = ""
        if not ranked:
            message = (
                f"No strong association rules found for {', '.join(clean_selected)} "
                f"at support >= {self.min_support:.2%} and confidence >= {self.min_confidence:.0%}."
            )

        return {
            "selected": clean_selected,
            "recommendations": ranked,
            "message": message,
            "model_summary": self.summary(),
        }

    def get_top_rules(self, limit: int = 25) -> list[dict[str, Any]]:
        """Return formatted top association rules for the Dashboard and Recommender Explorer."""
        self.ensure_trained()
        if self.rules.empty:
            return []

        top = self.rules.head(limit)
        formatted = []
        for _, row in top.iterrows():
            ant = sorted(row["antecedents"])
            cons = sorted(row["consequents"])
            formatted.append(
                {
                    "antecedents": ", ".join(ant),
                    "consequents": ", ".join(cons),
                    "support": round(float(row["support"]), 4),
                    "confidence": round(float(row["confidence"]), 4),
                    "lift": round(float(row["lift"]), 3),
                    "support_pct": round(float(row["support"]) * 100, 1),
                    "confidence_pct": round(float(row["confidence"]) * 100, 1),
                    "explanation": f"Customers who bought {' & '.join(ant)} also frequently bought {' & '.join(cons)}.",
                }
            )
        return formatted

    def get_frequent_itemsets(self, min_len: int = 2, limit: int = 15) -> list[dict[str, Any]]:
        """Return top frequent itemsets of size >= min_len."""
        self.ensure_trained()
        if self.frequent_itemsets.empty:
            return []
        df = self.frequent_itemsets.copy()
        df["length"] = df["itemsets"].apply(len)
        df = df[df["length"] >= min_len].sort_values(by=["support", "length"], ascending=[False, False]).head(limit)
        return [
            {
                "items": " + ".join(sorted(row["itemsets"])),
                "length": int(row["length"]),
                "support": round(float(row["support"]), 4),
                "support_pct": round(float(row["support"]) * 100, 1),
            }
            for _, row in df.iterrows()
        ]


# Shared application singleton trained on startup and refreshed after checkouts
recommender_engine = AprioriRecommender()
