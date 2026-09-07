"""Refresh graph/data/market.json from Alpha Vantage within a daily call budget.

Runs in GitHub Actions (see .github/workflows/refresh-market.yml) or locally:

    ALPHAVANTAGE_API_KEY=... python scripts/refresh_market.py --budget 24

Priority order: tickers on the active book sorted by nearest effective exit,
then watch names, then resolved reference names. Each ticker costs one
GLOBAL_QUOTE call; a COMPANY_OVERVIEW call (52 week range, 50 and 200 day
averages, market cap, float) is added only when the stored overview is older
than seven days and budget remains. The free tier allows 25 calls a day at
one per second; set --budget higher on a premium key.
"""
import argparse, datetime as dt, json, os, sys, time, urllib.parse, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GRAPH = os.path.join(ROOT, "graph", "data", "graph-data.json")
MARKET = os.path.join(ROOT, "graph", "data", "market.json")
API = "https://www.alphavantage.co/query"
BOOK = {"active", "extended"}
RESOLVED = {"approved", "complete response", "acquisition", "window closed"}


def get(params, key):
    params = dict(params, apikey=key)
    url = API + "?" + urllib.parse.urlencode(params)
    with urllib.request.urlopen(url, timeout=30) as r:
        body = json.loads(r.read().decode())
    if "Note" in body or "Information" in body or body.get("error"):
        raise RuntimeError(body.get("Note") or body.get("Information") or body["error"])
    return body


def num(v):
    try:
        return float(str(v).replace("%", ""))
    except (TypeError, ValueError):
        return None


def fmt_cap(v):
    n = num(v)
    if n is None:
        return None
    return f"{n/1e9:.2f}B" if n >= 1e9 else f"{n/1e6:.0f}M"


def priority(graph, today):
    """Tickers in refresh priority order, US listings only."""
    listing = {t["tkr"]: t.get("listing") for t in graph["tickers"]}
    rows = []
    for c in graph["catalysts"]:
        if listing.get(c["tkr"]) != "NASDAQ":
            continue
        life = c.get("lifecycle")
        rank = 0 if life in BOOK else 1 if life == "watch" else 2
        d = c.get("pdufa")
        dist = (dt.date.fromisoformat(d) - today).days if d else 9999
        if dist < -7 and rank == 0:
            rank = 2
        rows.append((rank, abs(dist), c["tkr"]))
    seen, out = set(), []
    for _, _, t in sorted(rows):
        if t not in seen:
            seen.add(t); out.append(t)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--budget", type=int, default=int(os.environ.get("AV_BUDGET", "24")))
    ap.add_argument("--overview-age", type=int, default=7)
    args = ap.parse_args()
    key = os.environ.get("ALPHAVANTAGE_API_KEY")
    if not key:
        sys.exit("ALPHAVANTAGE_API_KEY is not set")
    today = dt.date.today()
    graph = json.load(open(GRAPH))
    market = json.load(open(MARKET)) if os.path.exists(MARKET) else {}
    meta = market.pop("_meta", {})
    order = priority(graph, today)
    budget = args.budget
    quotes = overviews = 0
    for t in order:
        if budget <= 0:
            break
        m = market.get(t, {})
        try:
            q = get({"function": "GLOBAL_QUOTE", "symbol": t, "datatype": "json"}, key)["Global Quote"]
            budget -= 1; quotes += 1; time.sleep(1.1)
            if q.get("05. price"):
                m.update(price=num(q["05. price"]), prev_close=num(q["08. previous close"]),
                         chg_pct=num(q["10. change percent"]), vol=num(q["06. volume"]),
                         asof=q["07. latest trading day"], ccy="USD", source="alpha_vantage", stale=False)
        except Exception as e:
            print(f"{t}: quote failed: {e}"); budget -= 1
            if "per day" in str(e) or "rate limit" in str(e).lower():
                break
            continue
        stale_overview = not m.get("overview_asof") or (today - dt.date.fromisoformat(m["overview_asof"])).days > args.overview_age
        if stale_overview and budget > 0:
            try:
                v = get({"function": "OVERVIEW", "symbol": t}, key)
                budget -= 1; overviews += 1; time.sleep(1.1)
                if v.get("Symbol"):
                    m.update(hi52=num(v.get("52WeekHigh")), lo52=num(v.get("52WeekLow")),
                             sma50=num(v.get("50DayMovingAverage")), sma200=num(v.get("200DayMovingAverage")),
                             mcap=fmt_cap(v.get("MarketCapitalization")), mcap_raw=num(v.get("MarketCapitalization")),
                             float=num(v.get("SharesFloat")), shares_out=num(v.get("SharesOutstanding")),
                             analyst_target=num(v.get("AnalystTargetPrice")), overview_asof=today.isoformat())
            except Exception as e:
                print(f"{t}: overview failed: {e}"); budget -= 1
        market[t] = m
    meta.update(source="Alpha Vantage REST via scripts/refresh_market.py", refreshed=dt.datetime.utcnow().isoformat(timespec="seconds") + "Z",
                calls={"quotes": quotes, "overviews": overviews})
    market["_meta"] = meta
    json.dump(market, open(MARKET, "w"), indent=1, ensure_ascii=False)
    print(f"refreshed {quotes} quotes and {overviews} overviews; wrote {MARKET}")


if __name__ == "__main__":
    main()
