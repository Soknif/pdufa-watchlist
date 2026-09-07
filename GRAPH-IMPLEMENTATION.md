# Adding the catalyst graph to the MANTIS ALPHA PHARMA site

The dashboard stays at the root of the repository exactly as it is. The graph is a second page at `/graph/`, with its own data folder, and one nightly job refreshes market data for it. Nothing in this drop overwrites an existing file.

## What lands in the repository

```
<your repo>/
  index.html                          existing dashboard, unchanged
  data.json                           existing dashboard data, unchanged
  graph/index.html                    the graph page (new)
  graph/data/graph-data.json          the book as a graph model (new)
  graph/data/market.json              market snapshot the graph reads (new)
  scripts/refresh_market.py           Alpha Vantage refresh, writes graph/data/market.json (new)
  .github/workflows/refresh-market.yml nightly job on weekdays (new)
  dashboard-link.snippet.html         one line to link the dashboard to the graph (optional)
```

## Step 1. Copy the files in

Unzip the drop next to your repository and copy the `graph` folder, the `scripts` folder and the `.github` folder into the repository root. Keep the folder names; the page finds its data at `graph/data/` relative to itself and the script writes there.

```bash
unzip mantis-graph-drop.zip -d mantis-graph-drop
cp -r mantis-graph-drop/graph mantis-graph-drop/scripts mantis-graph-drop/.github  path/to/your-repo/
```

If your repository already has a `.github/workflows` folder, only the new file `refresh-market.yml` is added.

## Step 2. Link the two pages

Open your `index.html`, find the `.topbar` div near the top of the body, and paste the line from `dashboard-link.snippet.html` after the `live-pill` div. That adds a "Catalyst graph" pill. The graph already carries a "Dashboard" pill in its header that points back to `../`, so the two pages link both ways.

## Step 3. Commit and push

```bash
cd path/to/your-repo
git add graph scripts .github index.html
git commit -m "Add catalyst graph page and nightly market refresh"
git push
```

GitHub Pages redeploys on the push. The graph is then live at `https://<user>.github.io/<repo>/graph/` and the dashboard stays at `https://<user>.github.io/<repo>/`.

## Step 4. Add the Alpha Vantage key

Repository Settings, Secrets and variables, Actions, New repository secret. Name `ALPHAVANTAGE_API_KEY`, value your key. The workflow reads it from there; it never appears in the page or the commits.

## Step 5. Run the refresh once by hand

Actions tab, "Refresh market data", Run workflow. Leave the budget at 24 on the free key. The job pulls quotes in priority order (active book by nearest effective exit first), writes `graph/data/market.json` and commits it; Pages redeploys and the graph header shows "feed: repo data" with the new date. After that the job runs on its own at 21:30 UTC on weekdays. If you move to a premium key, raise the budget input or the `AV_BUDGET` default in the workflow.

## Step 6. Check the page

Open `/graph/` and confirm three things in the header: the as of date is today, the feed pill reads "repo data" with the latest trading day, and the macro regime shows. Click SVRA or PRAX; the market block should show a source tag of `alpha_vantage` once the workflow has run (before that it reads `snapshot`, the 4 September close embedded at build).

## Keeping the model current

Edit `graph/data/graph-data.json` to change scores, dates, factors or lifecycle; the page reads it at load, no rebuild. Add a catalyst by copying an existing entry and giving it a new `id` of the form `TKR:YYYY-MM-DD`. Put advisory committees or briefing documents in `risk_dates`; the effective exit follows automatically. Reclassify resolved names by lifecycle rather than deleting them.

The claude.ai artifact of the same graph reads market data from its own shared data layer and can call Alpha Vantage on demand through your connector; the two copies are independent, so edits to the repo's `graph-data.json` do not flow into the artifact by themselves.

## If something does not show

Blank graph with "d3 is not defined" in the console: the page loads d3 from cdnjs; a blocked CDN in your network is the usual cause.
Feed pill says "embedded snapshot": `graph/data/market.json` was not found at that path. Check the folder name.
Workflow fails with "ALPHAVANTAGE_API_KEY is not set": the secret name does not match.
Workflow logs "rate limit": the day's 25 free calls are spent; the script stops and keeps what it has.
