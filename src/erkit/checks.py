"""Data quality checks run after every update. A failed check is a warning, not a crash:
you see it in `erkit status` and in the GitHub Actions log."""
import pandas as pd

# How many days old the last observation may be before we call the series stale
MAX_AGE_DAYS = {"D": 7, "M": 75, "Q": 150, "A": 500}


def run_checks(df: pd.DataFrame, freq: str | None, previous_rows: int | None) -> list[str]:
    issues = []
    if df.empty:
        return ["no rows returned"]
    age = (pd.Timestamp.today().normalize() - pd.Timestamp(df["date"].max())).days
    if freq in MAX_AGE_DAYS and age > MAX_AGE_DAYS[freq]:
        issues.append(f"stale: last observation {df['date'].max():%Y-%m-%d} is {age} days old "
                      f"(dataset may have been renamed or discontinued)")
    if previous_rows and len(df) < 0.9 * previous_rows:
        issues.append(f"shrank: {previous_rows} -> {len(df)} rows")
    # Outlier in the NEWEST data only (history has real crises in it, e.g. 2008, 2022).
    # Compares the last 5 moves with the typical move over the previous 3 years of observations.
    diffs = df["value"].diff().dropna()
    if len(diffs) > 60:
        recent, history = diffs.iloc[-5:], diffs.iloc[-(60 + 5):-5]
        typical = history.abs().quantile(0.95)
        if typical > 0 and (recent.abs() > 4 * typical).any():
            big = df.loc[recent.abs().idxmax(), "date"]
            issues.append(f"outlier: unusually large recent move on {pd.Timestamp(big):%Y-%m-%d}, eyeball it")
    return issues
