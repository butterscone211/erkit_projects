"""Offline tests: no network needed. Run with `pytest`."""
import pandas as pd

from erkit import config, store
from erkit.checks import run_checks
from erkit.sources._tidy import tidy
from erkit.sources.edgar import _add_fourth_quarters


def test_tidy_parses_all_date_formats():
    cases = {
        "2026-10-20": "2026-10-20",
        "2026-09": "2026-09-30",   # monthly -> month end
        "202609": "2026-09-30",    # CSO monthly code
        "2026Q2": "2026-06-30",    # quarter -> quarter end
        "20262": "2026-06-30",     # CSO quarter code
    }
    for raw, expected in cases.items():
        out = tidy(pd.DataFrame({"d": [raw], "v": ["1.5"]}), "d", "v")
        assert out["date"].iloc[0] == pd.Timestamp(expected), raw
        assert out["value"].iloc[0] == 1.5


def test_tidy_drops_blanks_and_duplicates():
    df = pd.DataFrame({"d": ["2026-01", "2026-02", "2026-02", "2026-03"], "v": ["1", "2", "3", ""]})
    out = tidy(df, "d", "v")
    assert list(out["value"]) == [1.0, 3.0]  # blank dropped, latest duplicate kept


def test_fourth_quarter_derived_from_annual():
    q = pd.DataFrame({"end": ["2025-09-30", "2025-12-31", "2026-03-31"], "val": [10, 20, 30]})
    annual = pd.DataFrame({"start": ["2025-07-01"], "end": ["2026-06-30"], "val": [100]})
    out = _add_fourth_quarters(q, annual)
    assert out.loc[out["end"] == "2026-06-30", "val"].iloc[0] == 40


def test_stale_series_flagged():
    df = pd.DataFrame({"date": pd.to_datetime(["2020-01-31", "2020-02-29"]), "value": [1.0, 2.0]})
    assert any("stale" in i for i in run_checks(df, "M", None))


def test_store_round_trip(tmp_path, monkeypatch):
    monkeypatch.setattr(config, "DATA_DIR", tmp_path)
    monkeypatch.setattr(config, "DB_PATH", tmp_path / "t.duckdb")
    df = pd.DataFrame({"date": pd.to_datetime(["2026-01-31", "2026-02-28"]), "value": [2.0, 2.25]})
    with store.connect() as con:
        store.write_series(con, "test_rate", df, {"source": "test", "freq": "M"})
        store.write_series(con, "test_rate", df, {"source": "test", "freq": "M"})  # re-run is safe
    s = store.get("test_rate")
    assert len(s) == 2 and s.iloc[-1] == 2.25
