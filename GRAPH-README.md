# MANTIS Catalyst Graph

Time anchored graph of the MANTIS ALPHA pre-PDUFA book. Catalysts are pinned to their action dates, issuers float beside them, and shared risk factors sit in a band at the top so correlated tail risk shows as fan-in. Clicking a node opens the full MANTIS read: score and class, window status, effective exit, entry and exit bands, market snapshot with same day reads, penalties, record, verified against assumed.

Research model output, not investment advice.

## Layout

```
graph/index.html                 the graph page (self contained; loads d3 from cdnjs)
graph/data/graph-data.json       the book: tickers, catalysts, factors, indications
graph/data/market.json           market snapshot, one entry per ticker
scripts/refresh_market.py        Alpha Vantage refresh within a daily call budget
.github/workflows/               nightly refresh on weekdays
dashboard-link.snippet.html      one line to add to the existing dashboard
```

This drop sits alongside the existing MANTIS ALPHA PHARMA dashboard (`index.html` at the repository root). IMPLEMENTATION.md has the step by step.

The page reads `graph/data/market.json` and `graph/data/graph-data.json` at load, so editing either file in the repo changes the live site without rebuilding. Opened from disk (file URL) the page falls back to the snapshot embedded at build time.

## Alpha Vantage budget

The free tier allows 25 calls a day at one per second; bulk quotes are premium only. The refresh script spends the budget in priority order: active book by nearest effective exit, then watch names, then reference names. Each ticker costs one `GLOBAL_QUOTE`; a `COMPANY_OVERVIEW` (52 week range, 50 and 200 day averages, market cap, float) is added when the stored one is older than seven days. On a premium key raise `AV_BUDGET` in the workflow.

The claude.ai artifact version of the same page also calls Alpha Vantage on demand when a card opens, through the viewer's own connector, and writes the result to the artifact's shared data layer.

## Model

Entry band T-150 to T-90 with a fallback to T-60. Exit window T-14 to T-7. Effective exit is the earlier of T-7 and any scheduled risk date ahead less three days rolled back to a business day. Past risk dates never set a future exit. Names at score 2 never show an entry status. Every figure in `record` is a model recorded window measure, not a realised result and not a forecast.

Lifecycle values: active, extended, watch, approved, complete response, acquisition, window closed. Reclassify rather than delete so the record stays auditable.
