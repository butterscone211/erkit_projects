"""CSO Ireland PxStat (no key). Browse tables at https://data.cso.ie
A table holds many series, so pass filters: {column label: value} picks one series."""
import io

import pandas as pd

from erkit.http import fetch
from erkit.sources._tidy import tidy

BASE = "https://ws.cso.ie/public/api.restful/PxStat.Data.Cube_API.ReadDataset"


def fetch_series(table: str, filters: dict, time_col: str = "Month", name: str = "cso") -> pd.DataFrame:
    raw = fetch(f"{BASE}/{table}/CSV/1.0/en", name=name)
    df = pd.read_csv(io.BytesIO(raw), encoding="utf-8-sig")
    for col, val in filters.items():
        df = df[df[col].astype(str) == str(val)]
    if df.empty:
        raise ValueError(f"CSO {table}: no rows match {filters}. Check the column labels and values.")
    # Use the coded time column (e.g. 202609) when present: it parses reliably
    code_col = next((c for c in df.columns if c.startswith("TLIST")), time_col)
    return tidy(df, code_col, "VALUE")
