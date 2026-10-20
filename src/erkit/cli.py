"""Command line:  erkit update | erkit update --only ecb_dfr | erkit update --source ecb | erkit status"""
import argparse
import sys

import yaml

from erkit import config, store
from erkit.checks import run_checks
from erkit.sources import SOURCES


def load_catalog() -> dict:
    with open(config.CATALOG_PATH) as f:
        return yaml.safe_load(f)["series"]


def update(only: list[str] | None = None, source: str | None = None) -> int:
    catalog = load_catalog()
    failures = 0
    with store.connect() as con:
        prev = dict(con.execute("SELECT series_id, rows FROM series_meta").fetchall())
        for sid, spec in catalog.items():
            if only and sid not in only:
                continue
            if source and spec["source"] != source:
                continue
            params = {k: v for k, v in spec.items() if k not in ("source", "description", "unit", "freq")}
            try:
                df = SOURCES[spec["source"]](**params, name=sid)
                rows = store.write_series(con, sid, df, spec)
                issues = run_checks(df, spec.get("freq"), prev.get(sid))
                status = "warn" if issues else "ok"
                store.log(con, sid, status, rows, "; ".join(issues))
                flag = "WARN " + "; ".join(issues) if issues else "ok"
                print(f"{sid:<22} {rows:>6} rows  last {df['date'].max():%Y-%m-%d}  {flag}")
            except Exception as e:  # one bad source must not stop the rest
                failures += 1
                store.log(con, sid, "error", 0, str(e)[:500])
                print(f"{sid:<22} ERROR {e}", file=sys.stderr)
    return failures


def status() -> None:
    meta = store.list_series()
    if meta.empty:
        print("Store is empty. Run `erkit update`.")
        return
    print(meta[["series_id", "source", "freq", "rows", "last_date", "updated_at"]].to_string(index=False))


def main() -> None:
    p = argparse.ArgumentParser(prog="erkit")
    sub = p.add_subparsers(dest="cmd", required=True)
    u = sub.add_parser("update", help="fetch series from catalog.yaml into the store")
    u.add_argument("--only", nargs="+", help="series ids to update")
    u.add_argument("--source", help="update one source only, e.g. ecb")
    sub.add_parser("status", help="list series in the store")
    args = p.parse_args()
    if args.cmd == "update":
        sys.exit(1 if update(args.only, args.source) else 0)
    status()


if __name__ == "__main__":
    main()
