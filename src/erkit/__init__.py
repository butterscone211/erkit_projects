"""erkit: one shared research data pipeline.

Every source returns the same tidy shape, every project reads from the same store:

    import erkit
    dfr = erkit.get("ecb_dfr")                 # one series as a pandas Series
    panel = erkit.get_many(["ecb_dfr", "ea_hicp"])  # several, aligned by date
"""
from erkit.store import get, get_many, list_series

__all__ = ["get", "get_many", "list_series"]
