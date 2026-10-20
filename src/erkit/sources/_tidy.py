import pandas as pd


def tidy(df: pd.DataFrame, date_col: str, value_col: str) -> pd.DataFrame:
    """Standardise any source output to date/value, sorted, numeric, no blanks."""
    out = pd.DataFrame({
        "date": _parse_dates(df[date_col].astype(str)),
        "value": pd.to_numeric(df[value_col], errors="coerce"),
    })
    out = out.dropna().drop_duplicates("date", keep="last").sort_values("date")
    return out.reset_index(drop=True)


def _parse_dates(s: pd.Series) -> pd.Series:
    # Handles 2026-10-20, 2026-09 and 202609 (monthly), 2026-Q3 / 2026Q3 / 20263 (quarterly).
    # Quarterly and monthly dates are stamped at period END, so they line up with prices.
    s = s.str.strip()
    if s.str.fullmatch(r"\d{5}").all():  # CSO quarter code, e.g. 20262
        s = s.str[:4] + "Q" + s.str[4]
    if s.str.fullmatch(r"\d{4}-?Q[1-4]").all():
        q = pd.PeriodIndex(s.str.replace("-", ""), freq="Q")
        return pd.Series(q.to_timestamp(how="end").normalize(), index=s.index)
    if s.str.fullmatch(r"\d{4}M\d{2}").all():
        s = s.str.replace("M", "-")
    if s.str.fullmatch(r"\d{6}").all():
        s = s.str[:4] + "-" + s.str[4:]
    if s.str.fullmatch(r"\d{4}-\d{2}").all():
        m = pd.PeriodIndex(s, freq="M")
        return pd.Series(m.to_timestamp(how="end").normalize(), index=s.index)
    return pd.to_datetime(s)
