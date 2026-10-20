"""SEC EDGAR XBRL (no key, but a User-Agent with your email is required).
Look up a company's CIK at https://www.sec.gov/edgar/searchedgar/companysearch"""
import json

import pandas as pd

from erkit.http import fetch
from erkit.sources._tidy import tidy

BASE = "https://data.sec.gov/api/xbrl/companyconcept"


def fetch_concept(cik: int, concept: str, unit: str = "USD", taxonomy: str = "us-gaap",
                  form: str = "10-Q", quarterly: bool = True, name: str = "edgar") -> pd.DataFrame:
    """One reported line item (e.g. Revenues, IncomeLossFromContinuingOperationsBeforeIncomeTaxes...).
    quarterly=True keeps only ~3-month periods, so year-to-date figures don't get mixed in."""
    url = f"{BASE}/CIK{int(cik):010d}/{taxonomy}/{concept}.json"
    data = json.loads(fetch(url, name=name))
    df = pd.DataFrame(data["units"][unit])
    df = df[df["form"].isin(["10-Q", "10-K"])]
    # The same period is restated in later filings: keep the latest filed value
    df = df.sort_values("filed").drop_duplicates(["start", "end"], keep="last") if "start" in df else df
    if not quarterly or "start" not in df:
        return tidy(df.drop_duplicates("end", keep="last"), "end", "val")
    df = df.assign(days=(pd.to_datetime(df["end"]) - pd.to_datetime(df["start"])).dt.days)
    q = df[df["days"].between(80, 100)]
    annual = df[df["days"].between(350, 380)]
    return tidy(_add_fourth_quarters(q, annual), "end", "val")


def _add_fourth_quarters(q: pd.DataFrame, annual: pd.DataFrame) -> pd.DataFrame:
    """Companies report the fiscal Q4 only inside the annual 10-K figure.
    Derive it: Q4 = full year minus the three quarters that fall inside that year."""
    rows = [q[["end", "val"]]]
    for _, yr in annual.iterrows():
        if (q["end"] == yr["end"]).any():
            continue  # Q4 already reported directly
        inside = q[(q["end"] > yr["start"]) & (q["end"] < yr["end"])]
        if len(inside) == 3:
            rows.append(pd.DataFrame({"end": [yr["end"]], "val": [yr["val"] - inside["val"].sum()]}))
    return pd.concat(rows).drop_duplicates("end", keep="last")
