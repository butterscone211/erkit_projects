"""Eurostat SDMX 2.1 (no key). Datasets get renamed: HICP moved from prc_hicp_manr to
prc_hicp_minr (COICOP 2018) in 2026, so check the last date after every update."""
import io

import pandas as pd

from erkit.http import fetch
from erkit.sources._tidy import tidy

BASE = "https://ec.europa.eu/eurostat/api/dissemination/sdmx/2.1/data"


def fetch_series(dataset: str, key: str, start: str | None = None, name: str = "eurostat") -> pd.DataFrame:
    params = {"format": "SDMX-CSV"}
    if start:
        params["startPeriod"] = start
    raw = fetch(f"{BASE}/{dataset}/{key}", name=name, params=params)
    df = pd.read_csv(io.BytesIO(raw))
    return tidy(df, "TIME_PERIOD", "OBS_VALUE")
