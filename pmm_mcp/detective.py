"""
Detective heuristics — ported from Public Money Mirror's
backend/app/services/detective.py + investigative_tools.py. Pure functions, no
DB, no LLM. Deterministic.

What we keep:
  - EFFICIENCY_BENCHMARKS (typical % of budget per category, EU averages)
  - RED_FLAGS thresholds
  - detect_anomalies(distribution) — flags below/above benchmark
  - detect_vendor_concentration(distribution) — flags single-vendor risk on big categories
  - compute_distribution(items) — groups + percent shares + top-N

What we drop (lives in the full PMM SaaS, not in this MCP):
  - DB-backed budget item queries
  - LLM-based question parsing
  - Stripe / billing / recovery kit generation
"""

from __future__ import annotations

from typing import Any

# Typical share of a national budget per category, used as benchmarks for
# "spends a lot more / less than peers" anomaly checks. EU-average informed.
EFFICIENCY_BENCHMARKS: dict[str, dict[str, Any]] = {
    "Arbeit und Soziales": {"typical_range": (35, 42), "efficiency_score": 0.85},
    "Verteidigung": {"typical_range": (8, 14), "efficiency_score": 0.75},
    "Bundesschuld (Zinsen + Tilgung)": {
        "typical_range": (4, 10),
        "efficiency_score": 0.50,
    },
    "Verkehr und digitale Infrastruktur": {
        "typical_range": (6, 10),
        "efficiency_score": 0.70,
    },
    "Bildung und Forschung": {"typical_range": (5, 9), "efficiency_score": 0.80},
    "Inneres und Heimat": {"typical_range": (2, 5), "efficiency_score": 0.72},
    "Gesundheit": {"typical_range": (3, 6), "efficiency_score": 0.78},
    "Wirtschaft und Klimaschutz": {"typical_range": (2, 5), "efficiency_score": 0.75},
    "Familie, Senioren, Frauen, Jugend": {
        "typical_range": (2, 5),
        "efficiency_score": 0.80,
    },
    "Auswärtiges Amt": {"typical_range": (1, 3), "efficiency_score": 0.80},
    "Ernährung und Landwirtschaft": {"typical_range": (1, 3), "efficiency_score": 0.72},
    "Allgemeine Finanzverwaltung": {"typical_range": (8, 14), "efficiency_score": 0.65},
}

RED_FLAGS: dict[str, dict[str, Any]] = {
    "rapid_increase": {
        "threshold": 0.20,
        "description": "Spending increased > 20% year-over-year",
    },
    "declining_efficiency": {
        "threshold": 0.15,
        "description": "Per-capita spending rising faster than outcomes",
    },
    "concentration": {
        "threshold": 0.60,
        "description": "More than 60% of category spending to single subcategory",
    },
    "below_benchmark": {
        "threshold": 0.10,
        "description": "Spending 10% below typical range for similar category",
    },
    "above_benchmark": {
        "threshold": 0.20,
        "description": "Spending 20% above typical range without clear justification",
    },
}


# ─── compute_distribution ────────────────────────────────────────────


def compute_distribution(
    items: list[dict[str, Any]] | dict[str, float],
    *,
    top_n: int = 10,
) -> dict[str, Any]:
    """
    Group spending into categories, return totals + top-N + Sankey-ready data.

    Args:
      items: either a list of {"category_name": str, "amount_eur": float} dicts,
             OR a flat {"category_name": amount_eur} dict (the format the rest
             of the toolkit expects).
      top_n: how many categories to surface in the ranked list.

    Returns:
      {
        "total_eur":      <float>,
        "category_count": <int>,
        "distribution":   {"category": amount, ...},   # sorted desc
        "top_n": [
          {"category", "amount_eur", "share_pct"},
          ...
        ]
      }
    """
    by_category: dict[str, float] = {}
    if isinstance(items, dict):
        for name, amt in items.items():
            by_category[name] = by_category.get(name, 0.0) + float(amt or 0)
    else:
        for it in items:
            name = it.get("category_name", "Unbekannt")
            by_category[name] = by_category.get(name, 0.0) + float(
                it.get("amount_eur", 0)
            )

    total = sum(by_category.values())
    sorted_items = sorted(by_category.items(), key=lambda x: x[1], reverse=True)
    top = sorted_items[:top_n]

    return {
        "total_eur": total,
        "category_count": len(by_category),
        "distribution": dict(sorted_items),
        "top_n": [
            {
                "category": name,
                "amount_eur": amt,
                "share_pct": (amt / total * 100) if total else 0.0,
            }
            for name, amt in top
        ],
    }


# ─── detect_anomalies ────────────────────────────────────────────────


def detect_anomalies(distribution: dict[str, float]) -> list[dict[str, Any]]:
    """
    Flag categories that fall significantly outside their typical share-of-budget
    range, per EFFICIENCY_BENCHMARKS. Returns a list of dicts, one per anomaly.

    A category with no benchmark is silently skipped — we only flag what we
    have a calibrated expectation for.
    """
    anomalies: list[dict[str, Any]] = []
    total = sum(distribution.values())
    if total == 0:
        return anomalies

    for category, amount in distribution.items():
        percentage = (amount / total) * 100
        benchmark = EFFICIENCY_BENCHMARKS.get(category)
        if not benchmark:
            continue
        typical_min, typical_max = benchmark["typical_range"]

        if percentage < typical_min:
            anomalies.append(
                {
                    "category": category,
                    "type": "below_benchmark",
                    "severity": "medium",
                    "actual_pct": round(percentage, 2),
                    "typical_range_pct": [typical_min, typical_max],
                    "delta_pp": round(percentage - typical_min, 2),
                    "description": (
                        f"{category} bekommt {percentage:.1f}% — Erwartung {typical_min}-{typical_max}%. "
                        f"Unter dem typischen Bereich — möglich: Unterinvestition."
                    ),
                }
            )
        elif percentage > typical_max:
            anomalies.append(
                {
                    "category": category,
                    "type": "above_benchmark",
                    "severity": "high" if percentage > typical_max * 1.5 else "medium",
                    "actual_pct": round(percentage, 2),
                    "typical_range_pct": [typical_min, typical_max],
                    "delta_pp": round(percentage - typical_max, 2),
                    "description": (
                        f"{category} bekommt {percentage:.1f}% — Erwartung {typical_min}-{typical_max}%. "
                        f"Deutlich darüber — Begründung prüfen."
                    ),
                }
            )

    return anomalies


# ─── detect_vendor_concentration ─────────────────────────────────────


def detect_vendor_concentration(
    category_spending: dict[str, float],
    vendor_distribution: dict[str, float] | None = None,
) -> list[dict[str, Any]]:
    """
    Flag large categories where a single vendor likely dominates spending —
    a proxy for limited competition.

    Without a real vendor distribution we apply a simple "category > €1 Mrd → flag"
    heuristic, mirroring the PMM SaaS's MVP behaviour. The full SaaS layer reads
    actual award data; the MCP exposes the heuristic for citizen-level reads.
    """
    anomalies: list[dict[str, Any]] = []

    if vendor_distribution is None:
        for category, amount in category_spending.items():
            if amount > 1_000_000_000:
                anomalies.append(
                    {
                        "category": category,
                        "type": "vendor_concentration_suspected",
                        "severity": "high",
                        "top_vendor_share_pct": 45.0,
                        "description": (
                            f"{category}: über €1 Mrd Volumen. Vendor-Konzentration prüfen "
                            f"(Award-Daten erforderlich für endgültige Aussage)."
                        ),
                        "investigation_hint": (
                            "Open data abfragen: bund.de/EU TED — gibt es einen dominanten Bieter "
                            "über die letzten 3 Vergaben? Wettbewerblicher Vergabeprozess dokumentiert?"
                        ),
                        "risk_score": 8,
                    }
                )
        return anomalies

    # With real vendor data: flag any category with > 60% to top vendor
    for category, amount in category_spending.items():
        vendors_for_category = vendor_distribution.get(category, 0.0)
        if (
            amount > 0
            and vendors_for_category / amount > RED_FLAGS["concentration"]["threshold"]
        ):
            anomalies.append(
                {
                    "category": category,
                    "type": "vendor_concentration_confirmed",
                    "severity": "high",
                    "top_vendor_share_pct": round(
                        (vendors_for_category / amount) * 100, 1
                    ),
                    "description": (
                        f"{category}: {(vendors_for_category / amount) * 100:.0f}% gehen an Top-Anbieter."
                    ),
                    "risk_score": 9,
                }
            )

    return anomalies


# ─── compose_sankey_data ─────────────────────────────────────────────


def compose_sankey_data(distribution: dict[str, float]) -> dict[str, Any]:
    """
    Return D3-Sankey-compatible nodes + links: one root "Bundeshaushalt"
    fanning to each category. Useful for the citizen-facing visualisation
    layer (Streamlit / Next.js / agent UI).
    """
    nodes: list[dict[str, Any]] = [{"id": "root", "label": "Bundeshaushalt"}]
    links: list[dict[str, Any]] = []
    for name, amount in distribution.items():
        node_id = f"cat:{name}"
        nodes.append({"id": node_id, "label": name})
        links.append({"source": "root", "target": node_id, "value": float(amount)})
    return {"nodes": nodes, "links": links}
