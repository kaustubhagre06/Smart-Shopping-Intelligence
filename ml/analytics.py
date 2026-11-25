"""
Analytics & Plotly visualization builder for the Smart Shopping Intelligence Dashboard.
All metrics and charts are computed dynamically from SQLite transactions and the Apriori model.
"""

import json
from collections import Counter
from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from database.db import get_connection
from ml.recommendation import recommender_engine

ACCENT_PALETTE = [
    "#4F46E5",  # Indigo
    "#7C3AED",  # Violet
    "#2563EB",  # Royal Blue
    "#0EA5E9",  # Sky
    "#10B981",  # Emerald
    "#F59E0B",  # Amber
]


def _fig_to_dict(fig: go.Figure) -> dict[str, Any]:
    return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))


def compute_dashboard_analytics() -> dict[str, Any]:
    """Compute live KPIs, summary tables, and Plotly chart specs from SQLite + Apriori."""
    recommender_engine.ensure_trained()

    conn = get_connection()
    try:
        total_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
        tx_df = pd.read_sql_query(
            "SELECT id, transaction_code, total_amount, item_count, source, created_at FROM transactions",
            conn,
        )
        items_df = pd.read_sql_query(
            """
            SELECT ti.transaction_id, ti.product_id, ti.product_name, ti.quantity, ti.unit_price, p.category
            FROM transaction_items ti
            JOIN products p ON p.id = ti.product_id
            """,
            conn,
        )
    finally:
        conn.close()

    total_transactions = int(len(tx_df))
    checkout_orders = int((tx_df["source"] == "checkout").sum()) if not tx_df.empty else 0
    total_revenue = round(float(tx_df["total_amount"].sum()), 2) if not tx_df.empty else 0.0
    avg_basket_size = round(float(tx_df["item_count"].mean()), 2) if not tx_df.empty else 0.0
    avg_order_value = round(float(tx_df["total_amount"].mean()), 2) if not tx_df.empty else 0.0

    # Empty state safe guard
    if items_df.empty or total_transactions == 0:
        empty_layout = dict(
            template="plotly_white",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            font=dict(family="Inter, sans-serif", color="#0F172A"),
        )
        empty_fig = _fig_to_dict(go.Figure(layout=empty_layout))
        return {
            "kpis": {
                "total_transactions": 0,
                "checkout_orders": 0,
                "total_products": int(total_products),
                "avg_basket_size": 0,
                "avg_order_value": 0,
                "total_revenue": 0.0,
                "rules_count": 0,
            },
            "charts": {
                "popular_products": empty_fig,
                "category_trends": empty_fig,
                "top_combinations": empty_fig,
                "rules_scatter": empty_fig,
                "cooccurrence_heatmap": empty_fig,
            },
            "top_rules": [],
            "top_combinations_list": [],
        }

    # 1. Most Popular Products (Top 12)
    pop_df = (
        items_df.groupby(["product_name", "category"], as_index=False)
        .agg(
            purchases=("transaction_id", "nunique"),
            units=("quantity", "sum"),
            revenue=("unit_price", "sum"),
        )
        .sort_values(by="purchases", ascending=False)
        .head(12)
    )
    pop_sorted = pop_df.sort_values(by="purchases", ascending=True)
    pop_pct = (pop_sorted["purchases"] / total_transactions * 100).round(1)

    fig_popular = go.Figure(
        go.Bar(
            x=pop_sorted["purchases"],
            y=pop_sorted["product_name"],
            orientation="h",
            text=[f"{c} ({p}%)" for c, p in zip(pop_sorted["purchases"], pop_pct)],
            textposition="outside",
            marker=dict(
                color=pop_sorted["purchases"],
                colorscale=[[0, "#818CF8"], [0.5, "#4F46E5"], [1, "#6D28D9"]],
                line=dict(width=0),
            ),
            hovertemplate="<b>%{y}</b><br>Baskets: %{x}<br>Category: %{customdata}<extra></extra>",
            customdata=pop_sorted["category"],
        )
    )
    fig_popular.update_layout(
        margin=dict(l=110, r=55, t=20, b=35),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#0F172A", size=12),
        xaxis=dict(title="Number of Transactions", gridcolor="#E2E8F0", zeroline=False),
        yaxis=dict(title="", automargin=True),
    )

    # 2. Category-wise Shopping Trends
    items_df["line_total"] = items_df["quantity"] * items_df["unit_price"]
    cat_df = (
        items_df.groupby("category", as_index=False)
        .agg(units_sold=("quantity", "sum"), revenue=("line_total", "sum"))
        .sort_values(by="units_sold", ascending=False)
    )

    fig_category = go.Figure(
        go.Pie(
            labels=cat_df["category"],
            values=cat_df["units_sold"],
            hole=0.56,
            marker=dict(colors=ACCENT_PALETTE, line=dict(color="#FFFFFF", width=2.5)),
            textinfo="label+percent",
            textposition="outside",
            hovertemplate="<b>%{label}</b><br>Items Sold: %{value}<br>Revenue: $%{customdata:.2f}<extra></extra>",
            customdata=cat_df["revenue"],
        )
    )
    fig_category.update_layout(
        margin=dict(l=20, r=20, t=25, b=25),
        height=380,
        showlegend=False,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#0F172A", size=12),
        annotations=[
            dict(
                text=f"<b>{int(cat_df['units_sold'].sum())}</b><br><span style='font-size:11px;color:#64748B'>Items Sold</span>",
                x=0.5,
                y=0.5,
                font_size=18,
                showarrow=False,
            )
        ],
    )

    # 3. Top Product Combinations (Frequently Purchased Together)
    freq_combos = recommender_engine.get_frequent_itemsets(min_len=2, limit=10)
    if freq_combos:
        combos_rev = list(reversed(freq_combos))
        fig_combos = go.Figure(
            go.Bar(
                x=[c["support_pct"] for c in combos_rev],
                y=[c["items"] for c in combos_rev],
                orientation="h",
                text=[f"{c['support_pct']}%" for c in combos_rev],
                textposition="outside",
                marker=dict(color="#4F46E5", opacity=0.9),
                hovertemplate="<b>%{y}</b><br>Support: %{x}% of baskets<extra></extra>",
            )
        )
    else:
        fig_combos = go.Figure()

    fig_combos.update_layout(
        margin=dict(l=180, r=45, t=20, b=35),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#0F172A", size=12),
        xaxis=dict(title="Basket Support (%)", gridcolor="#E2E8F0", zeroline=False),
        yaxis=dict(title="", automargin=True),
    )

    # 4. Association Rules Scatter (Support vs Confidence colored by Lift)
    top_rules = recommender_engine.get_top_rules(limit=40)
    if top_rules:
        fig_rules = go.Figure(
            go.Scatter(
                x=[r["support_pct"] for r in top_rules],
                y=[r["confidence_pct"] for r in top_rules],
                mode="markers",
                marker=dict(
                    size=[max(10, min(28, r["lift"] * 7)) for r in top_rules],
                    color=[r["lift"] for r in top_rules],
                    colorscale="Viridis",
                    showscale=True,
                    colorbar=dict(title="Lift"),
                    line=dict(color="#FFFFFF", width=1.2),
                    opacity=0.88,
                ),
                text=[f"{r['antecedents']} -> {r['consequents']}" for r in top_rules],
                customdata=[[r["lift"], r["support_pct"], r["confidence_pct"]] for r in top_rules],
                hovertemplate=(
                    "<b>%{text}</b><br>"
                    "Support: %{customdata[1]}%<br>"
                    "Confidence: %{customdata[2]}%<br>"
                    "Lift: %{customdata[0]}x<extra></extra>"
                ),
            )
        )
    else:
        fig_rules = go.Figure()

    fig_rules.update_layout(
        margin=dict(l=55, r=20, t=20, b=45),
        height=380,
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#0F172A", size=12),
        xaxis=dict(title="Support (%)", gridcolor="#E2E8F0", zeroline=False),
        yaxis=dict(title="Confidence (%)", gridcolor="#E2E8F0", zeroline=False),
    )

    # 5. Co-Occurrence Heatmap for Top 10 Products
    top10_names = pop_df["product_name"].head(10).tolist()
    pair_counts: Counter[tuple[str, str]] = Counter()
    baskets_by_tx = items_df.groupby("transaction_id")["product_name"].apply(set)
    top10_set = set(top10_names)

    for basket in baskets_by_tx:
        filtered = sorted(basket & top10_set)
        for a, b in combinations(filtered, 2):
            pair_counts[(a, b)] += 1
            pair_counts[(b, a)] += 1

    n = len(top10_names)
    matrix = np.zeros((n, n), dtype=int)
    for i, a in enumerate(top10_names):
        for j, b in enumerate(top10_names):
            if i == j:
                matrix[i, j] = int((baskets_by_tx.apply(lambda s: a in s)).sum())
            else:
                matrix[i, j] = pair_counts[(a, b)]

    fig_heatmap = go.Figure(
        go.Heatmap(
            z=matrix.tolist(),
            x=top10_names,
            y=top10_names,
            colorscale=[[0, "#F8FAFC"], [0.4, "#C7D2FE"], [0.75, "#6366F1"], [1, "#312E81"]],
            hovertemplate="<b>%{y}</b> + <b>%{x}</b><br>Co-occurrences: %{z}<extra></extra>",
        )
    )
    fig_heatmap.update_layout(
        margin=dict(l=110, r=20, t=20, b=90),
        height=400,
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(family="Inter, sans-serif", color="#0F172A", size=11),
        xaxis=dict(tickangle=-35),
        yaxis=dict(autorange="reversed"),
    )

    return {
        "kpis": {
            "total_transactions": total_transactions,
            "checkout_orders": checkout_orders,
            "total_products": int(total_products),
            "avg_basket_size": avg_basket_size,
            "avg_order_value": avg_order_value,
            "total_revenue": total_revenue,
            "rules_count": int(len(recommender_engine.rules)),
        },
        "charts": {
            "popular_products": _fig_to_dict(fig_popular),
            "category_trends": _fig_to_dict(fig_category),
            "top_combinations": _fig_to_dict(fig_combos),
            "rules_scatter": _fig_to_dict(fig_rules),
            "cooccurrence_heatmap": _fig_to_dict(fig_heatmap),
        },
        "top_rules": top_rules[:15],
        "top_combinations_list": freq_combos,
    }
