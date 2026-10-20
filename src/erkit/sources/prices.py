"""Daily close prices via yfinance (free, unofficial, rate-limited: keep requests modest).
Tickers use Yahoo symbols, e.g. AIBG.L, BIRG.IR, RYA.IR, BZ=F (Brent), EURUSD=X."""
import pandas as pd


def fetch_prices(ticker: str, start: str = "2015-01-01", field: str = "Close", name: str = "prices") -> pd.DataFrame:
    import yfinance as yf

    hist = yf.Ticker(ticker).history(start=start, auto_adjust=True)
    if hist.empty:
        raise RuntimeError(f"No price data for {ticker} (wrong symbol or rate-limited)")
    out = pd.DataFrame({"date": hist.index.tz_localize(None).normalize(), "value": hist[field].values})
    return out.dropna().reset_index(drop=True)
