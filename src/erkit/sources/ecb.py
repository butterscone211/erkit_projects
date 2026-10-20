"""ECB Data Portal (SDMX REST, no key). Find series keys at https://data.ecb.europa.eu
Example key: FM/D.U2.EUR.4F.KR.DFR.LEV = deposit facility rate, daily."""
import io

import pandas as pd

from erkit.http import fetch
from erkit.sources._tidy import tidy

BASE = "https://data-api.ecb.europa.eu/service/data"


def fetch_series(key: str, start: str | None = None, name: str = "ecb") -> pd.DataFrame:
    params = {"format": "csvdata"}
    if start:
        params["startPeriod"] = start
    raw = fetch(f"{BASE}/{key}", name=name, params=params)
    df = pd.read_csv(io.BytesIO(raw))
    return tidy(df, "TIME_PERIOD", "OBS_VALUE")
