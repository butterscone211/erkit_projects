"""The shared store: one DuckDB file, one long table. Every project reads from here.

observations(series_id, date, value)   - the data, long format
series_meta(series_id, source, description, unit, freq, rows, first_date, last_date, updated_at)
update_log(run_at, series_id, status, rows, message)
"""
from datetime import datetime

import duckdb
import pandas as pd

from erkit import config

SCHEMA = """
CREATE TABLE IF NOT EXISTS observations (
    series_id VARCHAR, date DATE, value DOUBLE, PRIMARY KEY (series_id, date));
CREATE TABLE IF NOT EXISTS series_meta (
    series_id VARCHAR PRIMARY KEY, source VARCHAR, description VARCHAR, unit VARCHAR,
    freq VARCHAR, rows INTEGER, first_date DATE, last_date DATE, updated_at TIMESTAMP);
CREATE TABLE IF NOT EXISTS update_log (
    run_at TIMESTAMP, series_id VARCHAR, status VARCHAR, rows INTEGER, message VARCHAR);
"""


def connect(read_only: bool = False) -> duckdb.DuckDBPyConnection:
    config.DATA_DIR.mkdir(parents=True, exist_ok=True)
    con = duckdb.connect(str(config.DB_PATH), read_only=read_only and config.DB_PATH.exists())
    if not read_only:
        con.execute(SCHEMA)
    return con


def write_series(con, series_id: str, df: pd.DataFrame, meta: dict) -> int:
    """Replace one series in full (sources revise history, so a full refresh is safest)."""
    df = df.assign(series_id=series_id)[["series_id", "date", "value"]]
    con.execute("BEGIN")
    con.execute("DELETE FROM observations WHERE series_id = ?", [series_id])
    con.register("incoming", df)
    con.execute("INSERT INTO observations SELECT series_id, CAST(date AS DATE), value FROM incoming")
    con.unregister("incoming")
    con.execute("DELETE FROM series_meta WHERE series_id = ?", [series_id])
    con.execute(
        "INSERT INTO series_meta VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [series_id, meta.get("source"), meta.get("description"), meta.get("unit"), meta.get("freq"),
         len(df), df["date"].min(), df["date"].max(), datetime.now()],
    )
    con.execute("COMMIT")
    return len(df)


def log(con, series_id: str, status: str, rows: int = 0, message: str = "") -> None:
    con.execute("INSERT INTO update_log VALUES (?, ?, ?, ?, ?)", [datetime.now(), series_id, status, rows, message])


# ---------- read API used by every project ----------

def get(series_id: str, start: str | None = None) -> pd.Series:
    """One series as a date-indexed pandas Series."""
    with connect(read_only=True) as con:
        q = "SELECT date, value FROM observations WHERE series_id = ?"
        args = [series_id]
        if start:
            q += " AND date >= ?"
            args.append(start)
        df = con.execute(q + " ORDER BY date", args).df()
    if df.empty:
        raise KeyError(f"No data for '{series_id}'. Run `erkit update --only {series_id}` first.")
    return df.set_index(pd.to_datetime(df["date"]))["value"].rename(series_id)


def get_many(series_ids: list[str], start: str | None = None, freq: str | None = None) -> pd.DataFrame:
    """Several series side by side. freq='ME' or 'QE' resamples to month/quarter end (last value)."""
    frame = pd.concat([get(s, start) for s in series_ids], axis=1)
    if freq:
        frame = frame.resample(freq).last()
    return frame


def list_series() -> pd.DataFrame:
    with connect(read_only=True) as con:
        return con.execute("SELECT * FROM series_meta ORDER BY series_id").df()
