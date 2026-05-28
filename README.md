# pmm-mcp

**Public Money Mirror as Model Context Protocol — citizen-level Bundeshaushalt queries + anomaly heuristics + curated Bundesrechnungshof findings.**

[![Tests](https://img.shields.io/badge/tests-19%2F19-brightgreen?logo=pytest)](tests/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![MCP](https://img.shields.io/badge/Model_Context_Protocol-server-blue)](https://modelcontextprotocol.io)

---

## What it does

Wraps the public-good layer of [Public Money Mirror](https://github.com/mikelninh/Public-Money-Mirror) as MCP tools, so any agent (Claude Desktop, Cursor, custom) can answer citizen questions about the German federal budget:

| You ask Claude… | …pmm-mcp returns |
|---|---|
| "Wie ist der Bundeshaushalt 2024 verteilt?" | Top-N Einzelpläne with shares, total €476.5 Mrd |
| "Wo sind 2024 die größten Abweichungen vom EU-Durchschnitt?" | Ranked anomalies + severity + actual vs typical % |
| "Was sagt der Bundesrechnungshof zu Beratungsleistungen?" | Curated BRH findings with official source URLs |
| "Wie hat sich die Verteidigung von 2024 auf 2025 verändert?" | Year-over-year delta + flag (rapid_increase/stable/decrease) |
| "Bau mir Sankey-Daten für die Visualisierung" | D3-ready nodes + links |

---

## Why this exists

The full Public Money Mirror is a SaaS — auth, Stripe, recovery kits, success-fee invoices, Postgres, the works. That's the right shape for governments and analysts.

But citizens just want answers: *"Wohin fließt mein Steuergeld? Und wo geht etwas schief?"* That's a question an LLM can answer in seconds — **if** the LLM has tools that ground every claim in real numbers and cite the official sources.

`pmm-mcp` is exactly that. Six tools, bundled budget data + BRH findings, no DB needed, no server to run, no API key required. Self-contained. Citizen-level.

---

## Tools exposed

| Tool | Purpose |
|---|---|
| `get_budget(year)` | Federal budget summary per Einzelplan (ministry) — totals + breakdown + official source |
| `compute_distribution(year, top_n)` | Top-N ranked categories with shares of total budget |
| `detect_anomalies(year)` | Flag Einzelpläne whose share falls outside the typical range — plus vendor-concentration warnings on > €1 Mrd categories |
| `lookup_brh_findings(keyword)` | Search the bundled Bundesrechnungshof findings by keyword. Each result cites the official BRH publication URL. |
| `compare_years(category, year_a, year_b)` | Year-over-year delta for one Einzelplan, flagged when > ±20% |
| `compose_sankey_data(year)` | D3-Sankey-compatible nodes + links for visualisation |

---

## Quickstart — Claude Desktop in one minute

```bash
git clone https://github.com/mikelninh/pmm-mcp
cd pmm-mcp
pip install -e .
```

Add to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS):

```json
{
  "mcpServers": {
    "pmm": {
      "command": "pmm-mcp"
    }
  }
}
```

Restart Claude Desktop. Ask:

> *"Zeig mir die Top 5 Einzelpläne im Bundeshaushalt 2024 mit Anteilen."*
> *"Welche Anomalien gibt's 2024?"*
> *"Was sagt der Bundesrechnungshof zu Klimaförderung?"*

**No API key needed.** All six tools work fully offline against the bundled data.

---

## Data sources + honest limits

**What's bundled:**
- `pmm_mcp/data/budget.json` — Einzelplan totals for fiscal years 2024 and 2025, based on the published Bundeshaushaltsplan. Source: [bundeshaushalt.de](https://www.bundeshaushalt.de).
- `pmm_mcp/data/brh_findings.json` — 8 curated Bundesrechnungshof findings (Beratung, BAMF, Klima, IT-Beratung, E-Auto-Bonus, Bundeswehr-Beschaffung, Bürgergeld, Bahninfrastruktur). Each with official source URL.

**Honest limits (read these before relying on output):**
- **Granularity is Einzelplan-level only.** For sub-positions (single budget lines) you need the full PMM SaaS with the Postgres-backed corpus.
- **2024 + 2025 only.** Historical years and live updates are roadmap.
- **The vendor-concentration heuristic is approximate** — without award-level data it flags every category > €1 Mrd as "needs investigation". The full PMM SaaS reads actual award data for confirmed flags. Use as a hint, not a verdict.
- **No daily upstream sync yet.** When the Bundestag passes a Nachtragshaushalt, this MCP doesn't auto-update. The drift-detection pattern from [gitlaw-mcp](https://github.com/mikelninh/gitlaw) is the obvious next move.
- **BRH findings are a curated sample**, not exhaustive. More via PR against `brh_findings.json`.

---

## Test coverage

```
19 passed in ~1s
```

All hermetic — no network calls, no LLM calls, runs anywhere. Covers:

- 3 `get_budget` tests (2024 + 2025 + unknown year error envelope)
- 1 `compute_distribution` (sorted, share sums to ~100%, top-N count)
- 3 `detect_anomalies` (shape of anomalies + vendor warnings + targets-large-only)
- 4 `lookup_brh_findings` (substring match, case-insensitive, empty input, unknown keyword)
- 3 `compare_years` (delta computation, unknown category, flag thresholds)
- 1 `compose_sankey_data` (root + categories, positive values)
- 4 detective pure-function unit tests (empty inputs, JSON-serialisability)

---

## Part of an MCP-server portfolio

`pmm-mcp` is one of five public-good Model Context Protocol servers built on the same architectural pattern — thin MCP wrapper over a small testable core:

- **[gitlaw-mcp](https://github.com/mikelninh/gitlaw)** — German federal law (5,942 statutes), anti-hallucination citation verification, live drift detection
- **[safevoice-mcp](https://github.com/mikelninh/safevoice/tree/main/safevoice_mcp)** — Digital-harassment victim tooling (DE/AT/CH/UK)
- **[grailsense](https://github.com/mikelninh/grailsense)** — NFT collector intelligence over Blockscout
- **[judge-mcp](https://github.com/mikelninh/judge-mcp)** — Domain-agnostic judge + iterate (the meta-tool, MCP-for-MCPs)
- **[pmm-mcp](https://github.com/mikelninh/pmm-mcp)** ← you're here

Together they're an early sketch of what *public-good civic infrastructure* looks like in the LLM era — open source, MIT, verifiable, composable.

---

## Roadmap

- [ ] Daily upstream sync against bundeshaushalt.de (Phase 1a, mirroring [gitlaw-mcp/freshness](https://github.com/mikelninh/gitlaw/tree/main/gitlaw_mcp/freshness))
- [ ] Per-Einzelplan sub-position data ingestion (Einzeltitel level)
- [ ] Historical years (2018-2023) for trend analysis
- [ ] Live vendor-concentration from EU TED tender data
- [ ] Eval harness: how often does Claude misanswer Bundeshaushalt questions without vs. with pmm-mcp
- [ ] Cross-call into [gitlaw-mcp](https://github.com/mikelninh/gitlaw) for legal basis lookups (e.g. "which Haushaltsgesetz applies?")

---

## License

MIT. The Bundeshaushalt and Bundesrechnungshof data this MCP exposes is public domain (Bundesregierung / Bundesrechnungshof published works).
