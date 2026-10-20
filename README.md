# erkit: shared research data pipeline

One pipeline that pulls free macro, rates and company data into a single local database. Every research project reads from it with one line:

```python
import erkit
dfr = erkit.get("ecb_dfr")                                   # one series
panel = erkit.get_many(["ecb_dfr", "ie_mortgage_rate"], freq="ME")  # aligned by month
```

## How it works

```
catalog.yaml  ──►  erkit update  ──►  sources/ (ECB, Eurostat, CSO, EDGAR, prices)
  (what to fetch)                         │  each returns the same shape: date, value
                                          ▼
                          data/raw/<series>/<date>.csv   (untouched copy, audit trail)
                          data/research.duckdb           (one long table: series_id, date, value)
                                          │
                     checks.py: stale? shrank? odd recent move?  ──►  update_log
                                          │
            projects/p1_irish_banks, p2_ireland_inc, ...  ──►  erkit.get("...")
```

Four design rules make it reusable:

1. **One shape.** Every source returns `date, value`. Monthly and quarterly dates are stamped at period end, so they line up with prices.
2. **One list.** `catalog.yaml` is the only place a series is defined. Add it once, use it everywhere.
3. **One store.** A single DuckDB file. Full refresh per series, because sources revise history.
4. **Fail loudly, not fatally.** One broken source logs an error and the rest still update. Checks flag stale or odd data.

## Setup (once, about 15 minutes)

```bash
git clone <your repo> research && cd research
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
pip install -e ".[dev]"
export ERKIT_USER_AGENT="Kim Tran your@email.com"     # SEC requires a name + email
pytest -q                                              # 5 offline tests should pass
erkit update                                           # pulls every series (2-3 min)
erkit status                                           # what's in the store
python projects/p1_irish_banks/deposit_beta.py         # first real result
```

## Daily use

| Task | Command |
| --- | --- |
| Refresh everything | `erkit update` |
| Refresh one series | `erkit update --only ecb_dfr` |
| Refresh one source | `erkit update --source ecb` |
| See what's stored | `erkit status` |
| Use in a notebook or script | `import erkit; erkit.get("ie_10y")` |
| Query with SQL | `duckdb data/research.duckdb "select * from update_log order by run_at desc limit 20"` |

## Adding a series

1. Find its key on the source site (ECB: data.ecb.europa.eu; Eurostat: ec.europa.eu/eurostat/databrowser; CSO: data.cso.ie; EDGAR concept names: a company's `companyfacts` JSON).
2. Add an entry to `catalog.yaml` with `source`, the key fields, `description`, `unit`, `freq`.
3. Run `erkit update --only <id>` and check the last date it prints.

## Adding a source

Write a function in `src/erkit/sources/` that returns a DataFrame with `date` and `value`, use `erkit.http.fetch` (retries + raw copy), and register it in `sources/__init__.py`.

## Automation

`.github/workflows/update-data.yml` runs the tests and the update every weekday at 07:15 UTC, then commits the refreshed database. Set the repository variable `ERKIT_USER_AGENT` first (Settings > Secrets and variables > Actions > Variables). Dashboards hosted on Streamlit Community Cloud read the committed database.

## Known gotchas (found while building)

- **Eurostat renamed HICP** from `prc_hicp_manr` to `prc_hicp_minr` (COICOP 2018) in 2026. The old dataset still answers but stops at Dec 2025. The staleness check exists for exactly this.
- **CSO tables get replaced** the same way (CPM01 stops at Dec 2025). Check the table's last update date on data.cso.ie.
- **EDGAR has no fiscal Q4 quarter.** Companies report it only inside the 10-K annual figure. `edgar.py` derives Q4 = full year minus Q1-Q3.
- **yfinance is unofficial and rate-limited.** Keep the ticker list modest; the retry handles short blocks.

## Data sources and terms

ECB Data Portal, Eurostat, CSO PxStat and SEC EDGAR are free public APIs. Prices come from Yahoo Finance via yfinance, for personal research only. Cite the original source in every published note.
