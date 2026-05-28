"""
pmm-mcp — Public Money Mirror as Model Context Protocol tools.

Exposes citizen-level Bundeshaushalt queries + anomaly heuristics + curated
Bundesrechnungshof (BRH) findings as MCP tools any LLM client can call.

What this MCP is FOR:
  - "Welche Einzelpläne bekommen wie viel Geld?"
  - "Wo sind die größten Abweichungen vom EU-Durchschnitt?"
  - "Was sagt der Bundesrechnungshof zum Thema Beratung / Klima / Asyl?"
  - "Wie hat sich der Bildungshaushalt von 2024 auf 2025 verändert?"

What this MCP is NOT:
  - The full Public Money Mirror SaaS (auth, Stripe, recovery kits, success-fee
    invoices) — that's a separate hosted product
  - A live Bundeshaushalt feed (today: manually-curated annual snapshots; daily
    sync is on the freshness roadmap, mirroring gitlaw-mcp's Phase-1b pattern)
"""

from __future__ import annotations

import json as _json
import logging
import os
import sys
import time
import uuid
from pathlib import Path
from typing import Any

from mcp.server.fastmcp import FastMCP

from pmm_mcp import detective as _detective


HERE = Path(__file__).resolve().parent
BUDGET_FILE = HERE / "data" / "budget.json"
BRH_FILE = HERE / "data" / "brh_findings.json"


log = logging.getLogger("pmm_mcp")


def _log_json(level: int, **fields: Any) -> None:
    fields.setdefault("ts", time.strftime("%Y-%m-%dT%H:%M:%S"))
    log.log(level, _json.dumps(fields, ensure_ascii=False))


def _traced(tool_name: str):
    def decorator(fn):
        def wrapper(*args, **kwargs):
            request_id = uuid.uuid4().hex[:12]
            t0 = time.perf_counter()
            try:
                result = fn(*args, **kwargs)
                _log_json(
                    logging.INFO,
                    msg=f"tool.{tool_name}",
                    request_id=request_id,
                    tool=tool_name,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    status="ok",
                )
                return result
            except Exception as e:  # pragma: no cover — defensive
                _log_json(
                    logging.ERROR,
                    msg=f"tool.{tool_name}",
                    request_id=request_id,
                    tool=tool_name,
                    latency_ms=round((time.perf_counter() - t0) * 1000, 2),
                    status="error",
                    error=f"{type(e).__name__}: {e}",
                )
                return {"error": "internal_error", "message": str(e)}

        wrapper.__name__ = fn.__name__
        wrapper.__doc__ = fn.__doc__
        return wrapper

    return decorator


mcp = FastMCP(
    "pmm",
    host=os.getenv("FASTMCP_HOST", "0.0.0.0"),
    port=int(os.getenv("FASTMCP_PORT", os.getenv("PORT", "8004"))),
)


try:
    from starlette.responses import JSONResponse

    @mcp.custom_route("/health", methods=["GET"])
    async def _health(_request):  # noqa: ANN001
        return JSONResponse({"status": "ok", "service": "pmm-mcp"})
except Exception:  # pragma: no cover
    pass


# ─── Bundled data ────────────────────────────────────────────────────


_budget_cache: dict[str, Any] | None = None
_brh_cache: dict[str, Any] | None = None


def _load_budget() -> dict[str, Any]:
    global _budget_cache
    if _budget_cache is None:
        _budget_cache = _json.loads(BUDGET_FILE.read_text(encoding="utf-8"))
    return _budget_cache


def _load_brh() -> dict[str, Any]:
    global _brh_cache
    if _brh_cache is None:
        _brh_cache = _json.loads(BRH_FILE.read_text(encoding="utf-8"))
    return _brh_cache


# ─── Tool 1: get_budget ──────────────────────────────────────────────


@mcp.tool()
@_traced("get_budget")
def get_budget(year: int = 2024) -> dict[str, Any]:
    """
    Return the federal budget summary for a given fiscal year — totals plus the
    Einzelplan (ministry) breakdown.

    Args:
      year: fiscal year (2024 or 2025 currently bundled).

    Returns:
      {
        "year": 2024,
        "total_eur": 476500000000,
        "currency": "EUR",
        "as_of": "2024-01-01",
        "source": "https://www.bundeshaushalt.de",
        "einzelplaene": {"Arbeit und Soziales": 177000000000, ...}
      }

      Or {"error": "year_not_available", "available_years": [...]} when the
      year isn't in the bundled snapshot.
    """
    budget = _load_budget()
    fy_key = str(year)
    fy = budget["fiscal_years"].get(fy_key)
    if not fy:
        return {
            "error": "year_not_available",
            "available_years": list(budget["fiscal_years"].keys()),
        }
    return {
        "year": year,
        "total_eur": fy["total_eur"],
        "currency": fy["currency"],
        "as_of": fy["as_of"],
        "source": budget["source"],
        "einzelplaene": fy["einzelplaene"],
    }


# ─── Tool 2: compute_distribution ────────────────────────────────────


@mcp.tool()
@_traced("compute_distribution")
def compute_distribution(
    year: int = 2024,
    top_n: int = 10,
) -> dict[str, Any]:
    """
    Compute the distribution + top-N ranking from a year's Einzelplan data.

    Args:
      year:  fiscal year (uses bundled budget)
      top_n: how many categories to surface in the ranked list (default 10)

    Returns:
      {
        "total_eur":      <float>,
        "category_count": <int>,
        "distribution":   {"category": amount, ...},   # sorted desc
        "top_n": [{"category", "amount_eur", "share_pct"}, ...]
      }
    """
    bud = get_budget(year)
    if "error" in bud:
        return bud
    return _detective.compute_distribution(bud["einzelplaene"], top_n=top_n)


# ─── Tool 3: detect_anomalies ────────────────────────────────────────


@mcp.tool()
@_traced("detect_anomalies")
def detect_anomalies(year: int = 2024) -> dict[str, Any]:
    """
    Flag Einzelpläne whose share of the budget falls significantly outside the
    typical range (per the EFFICIENCY_BENCHMARKS heuristic, EU-average informed).

    Args:
      year: fiscal year to analyse.

    Returns:
      {
        "year": <int>,
        "anomaly_count": <int>,
        "anomalies": [
          {"category", "type" ("below_benchmark"|"above_benchmark"),
           "severity", "actual_pct", "typical_range_pct", "delta_pp", "description"},
          ...
        ],
        "vendor_concentration_warnings": [
          {"category", "severity", "description", ...},
          ...
        ]
      }
    """
    bud = get_budget(year)
    if "error" in bud:
        return bud
    distribution = bud["einzelplaene"]
    base = _detective.detect_anomalies(distribution)
    vendor = _detective.detect_vendor_concentration(distribution)
    return {
        "year": year,
        "anomaly_count": len(base) + len(vendor),
        "anomalies": base,
        "vendor_concentration_warnings": vendor,
    }


# ─── Tool 4: lookup_brh_findings ─────────────────────────────────────


@mcp.tool()
@_traced("lookup_brh_findings")
def lookup_brh_findings(keyword: str) -> dict[str, Any]:
    """
    Search the bundled set of Bundesrechnungshof (Federal Audit Office) findings
    by keyword. Substring match against keyword tag, title, and finding text.

    Args:
      keyword: search term — e.g. "beratung", "klima", "asyl", "verteidigung",
               "soziales", "verkehr".

    Returns:
      {
        "keyword":     <input>,
        "match_count": <int>,
        "findings": [
          {"id", "year", "title", "finding", "source_url", "severity",
           "estimated_savings_eur" (or null)},
          ...
        ]
      }

    Each finding cites the official BRH publication URL — verifiable.
    """
    kw = (keyword or "").lower().strip()
    if not kw:
        return {"keyword": keyword, "match_count": 0, "findings": []}

    all_findings = _load_brh()["findings"]
    matches = [
        f
        for f in all_findings
        if kw in f.get("keyword", "").lower()
        or kw in f.get("title", "").lower()
        or kw in f.get("finding", "").lower()
    ]
    return {
        "keyword": keyword,
        "match_count": len(matches),
        "findings": matches,
    }


# ─── Tool 5: compare_years ───────────────────────────────────────────


@mcp.tool()
@_traced("compare_years")
def compare_years(
    category: str,
    year_a: int = 2024,
    year_b: int = 2025,
) -> dict[str, Any]:
    """
    Compare an Einzelplan's allocation between two fiscal years — surface the
    absolute delta + percentage change. Flags large year-over-year changes.

    Args:
      category: Einzelplan name (e.g. "Verteidigung", "Bildung und Forschung").
      year_a:   baseline year (default 2024).
      year_b:   comparison year (default 2025).

    Returns:
      {
        "category":      <name>,
        "year_a":        {"year", "amount_eur", "share_pct"},
        "year_b":        {"year", "amount_eur", "share_pct"},
        "delta_eur":     <int>,
        "delta_pct":     <float>,
        "flag":          "rapid_increase" | "rapid_decrease" | "stable"
      }
    """
    a_budget = get_budget(year_a)
    b_budget = get_budget(year_b)
    if "error" in a_budget:
        return a_budget
    if "error" in b_budget:
        return b_budget

    a_amt = a_budget["einzelplaene"].get(category)
    b_amt = b_budget["einzelplaene"].get(category)
    if a_amt is None or b_amt is None:
        return {
            "error": "category_not_found",
            "category": category,
            "available_categories": sorted(
                set(a_budget["einzelplaene"].keys())
                | set(b_budget["einzelplaene"].keys())
            ),
        }

    delta = b_amt - a_amt
    pct = (delta / a_amt * 100) if a_amt else 0.0
    if pct > 20:
        flag = "rapid_increase"
    elif pct < -20:
        flag = "rapid_decrease"
    else:
        flag = "stable"

    return {
        "category": category,
        "year_a": {
            "year": year_a,
            "amount_eur": a_amt,
            "share_pct": round(a_amt / a_budget["total_eur"] * 100, 2),
        },
        "year_b": {
            "year": year_b,
            "amount_eur": b_amt,
            "share_pct": round(b_amt / b_budget["total_eur"] * 100, 2),
        },
        "delta_eur": delta,
        "delta_pct": round(pct, 2),
        "flag": flag,
    }


# ─── Tool 6: compose_sankey_data ─────────────────────────────────────


@mcp.tool()
@_traced("compose_sankey_data")
def compose_sankey_data(year: int = 2024) -> dict[str, Any]:
    """
    Return D3-Sankey-compatible nodes + links for the given fiscal year — useful
    for visualisation layers (agent UI, Streamlit, Next.js dashboards).

    Args:
      year: fiscal year.

    Returns:
      {
        "nodes": [{"id", "label"}, ...],
        "links": [{"source", "target", "value"}, ...]
      }
    """
    bud = get_budget(year)
    if "error" in bud:
        return bud
    return _detective.compose_sankey_data(bud["einzelplaene"])


# ─── Entry point ─────────────────────────────────────────────────────


def main() -> None:
    logging.basicConfig(
        level=os.getenv("LOG_LEVEL", "INFO"),
        format="%(message)s",
        stream=sys.stderr,
    )
    transport = os.getenv("MCP_TRANSPORT", "stdio").lower()
    if transport in ("sse", "streamable-http"):
        mcp.run(transport=transport)
    else:
        mcp.run()


if __name__ == "__main__":
    main()
