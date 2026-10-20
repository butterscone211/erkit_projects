"""Source adapters. Each one takes keyword arguments from catalog.yaml and returns a
DataFrame with exactly two columns: date (datetime64) and value (float).

To add a source: write a function with that contract and register it in SOURCES.
"""
from erkit.sources import cso, ecb, edgar, eurostat, prices

SOURCES = {
    "ecb": ecb.fetch_series,
    "eurostat": eurostat.fetch_series,
    "cso": cso.fetch_series,
    "edgar": edgar.fetch_concept,
    "prices": prices.fetch_prices,
}
