"""Project 1 scenario engine: ECB rate path -> 2027 NII -> profit -> ROTE -> fair value.

Every input is in BANKS below with its source. Assumptions (not disclosed) are marked ASSUMPTION.
The dashboard (app.py) and the note both call run() so the numbers can never disagree.
"""
from dataclasses import dataclass

BASE_RATE = 2.50  # ECB deposit rate the banks' 2027 guidance assumes (both banks, H1 2026)


@dataclass
class Bank:
    name: str
    price: float              # EUR, Euronext Dublin close (pipeline px_aib / px_boi)
    tnav_ps: float            # tangible NAV per share, EUR
    shares_m: float           # shares in issue, millions
    nii_2027_base: float      # EUR m at 2.50% ECB rate
    sens_up_100: float        # EUR m, +100bp parallel, EUR book only (disclosed)
    sens_dn_100: float        # EUR m, -100bp parallel, EUR book only (disclosed, negative)
    pat_base: float           # EUR m, 2027 base profit after tax to ordinary holders
    tax_rate: float
    irish_deposits_bn: float  # deposits exposed to migration into term accounts
    loans_bn: float
    rwa_bn: float
    cet1: float               # current CET1 ratio
    cet1_target: float


BANKS = {
    "BOI": Bank(
        name="Bank of Ireland",
        price=18.40,            # 20 Oct 2026, yfinance BIRG.IR
        tnav_ps=10.85,          # H1 2026 results, TNAV table
        shares_m=943,           # H1 2026 results, shares excl. treasury
        nii_2027_base=3750,     # guidance c.EUR3.75bn, assumes ECB 2.50% in 2027
        sens_up_100=95,         # slide 40, EUR column, after July hedge add
        sens_dn_100=-120,       # slide 40, EUR column
        pat_base=0.150 * 10233, # ASSUMPTION: 2027 ROTE 15% (guidance >14% FY26, >16% FY28) x TNAV EUR10,233m
        tax_rate=0.18,          # H1 2026: PBT 960 vs profit 783
        irish_deposits_bn=88.0, # Irish deposits Jun 2026 (current 77.4 + term 10.6)
        loans_bn=88.0,          # group net loans Jun 2026
        rwa_bn=57.3,            # fully loaded RWA Jun 2026
        cet1=0.155, cet1_target=0.145,
    ),
    "AIB": Bank(
        name="AIB Group",
        price=10.745,           # 20 Oct 2026, yfinance A5G.IR
        tnav_ps=5.88,           # DERIVED: equity 14.1bn - AT1 1.31bn - intangibles 0.56bn, / 2,079m shares
        shares_m=2079,          # DERIVED: interim dividend EUR406m / 19.528c per share
        nii_2027_base=3900,     # ASSUMPTION: FY26 guidance >EUR3.8bn plus c.3% balance sheet growth
        sens_up_100=182,        # H1 2026 presentation, EUR, +100bp
        sens_dn_100=-184,       # H1 2026 presentation, EUR, -100bp
        pat_base=0.147 * 12230, # ASSUMPTION: ROTE held at H1 2026 run-rate (~14.7% on derived TNAV EUR12.2bn)
        tax_rate=0.131,         # H1 2026: tax 142 / PBT 1,081
        irish_deposits_bn=110.0,  # 93% of EUR118.8bn customer deposits are ROI-based
        loans_bn=74.5,
        rwa_bn=56.0,
        cet1=0.161, cet1_target=0.14,
    ),
}

# Scenario paths: average ECB deposit rate across 2027 (monthly path in comments)
SCENARIOS = {
    "A. Guidance (hold)": 2.50,   # 2.50% all year
    "B. Market (2 hikes)": 2.96,  # 2.75% from Dec-26, 3.00% from Mar-27
    "C. Reversal (3 cuts)": 1.94, # 25bp cuts in Feb, Apr, Jun 2027 to 1.75%
}

COE, GROWTH = 0.11, 0.03  # ASSUMPTION: cost of equity 11%, long-run growth 3%

# Overlays the disclosed sensitivity does NOT include (it assumes a static balance sheet)
MIGRATION_PP_PER_100BP = 8.0   # term share rises 8pp per +100bp (2022-23: 2% -> ~11% over 450bp, but lagged)
TERM_GAP_AT_BASE = 1.59        # term rate 1.81% minus overnight 0.22% (Aug 2026, pipeline)
TERM_BETA = 0.59               # 2022-23 cycle, pipeline
COR_BP_PER_100BP = 20.0        # cost of risk +20bp per +100bp of hikes (stress assumption)


def run(bank: Bank, avg_rate: float, overlays: bool = True) -> dict:
    d = avg_rate - BASE_RATE
    sens = bank.sens_up_100 if d >= 0 else -bank.sens_dn_100
    d_nii_disclosed = sens * d  # linear in the move, per the bank's own table

    d_migration = d_credit = 0.0
    if overlays and d > 0:
        shift = MIGRATION_PP_PER_100BP * d / 100            # share of deposits moving to term
        gap = (TERM_GAP_AT_BASE + TERM_BETA * d) / 100      # extra cost on each euro that moves
        d_migration = -bank.irish_deposits_bn * 1000 * shift * gap
        d_credit = -bank.loans_bn * 1000 * (COR_BP_PER_100BP * d) / 10000

    d_pbt = d_nii_disclosed + d_migration + d_credit
    d_pat = d_pbt * (1 - bank.tax_rate)
    pat = bank.pat_base + d_pat

    tbv = bank.tnav_ps * bank.shares_m                        # EUR m
    excess = max(bank.cet1 - bank.cet1_target, 0) * bank.rwa_bn * 1000
    core_tbv = tbv - excess
    rote_core = pat / core_tbv
    pt = (rote_core - GROWTH) / (COE - GROWTH)                # justified P/TBV on core equity
    fair_ps = (core_tbv * pt + excess) / bank.shares_m

    return {
        "bank": bank.name, "avg_rate": avg_rate,
        "d_nii_disclosed": d_nii_disclosed, "d_migration": d_migration, "d_credit": d_credit,
        "nii": bank.nii_2027_base + d_nii_disclosed + d_migration,
        "d_eps_c": d_pat / bank.shares_m * 100,
        "rote": pat / tbv, "fair_ps": fair_ps, "upside": fair_ps / bank.price - 1,
    }


def implied_rote(bank: Bank) -> float:
    """ROTE the current price implies, on the same core-equity basis as run()."""
    tbv = bank.tnav_ps * bank.shares_m
    excess = max(bank.cet1 - bank.cet1_target, 0) * bank.rwa_bn * 1000
    core_tbv = tbv - excess
    pt_core = (bank.price * bank.shares_m - excess) / core_tbv
    return (GROWTH + pt_core * (COE - GROWTH)) * core_tbv / tbv


if __name__ == "__main__":
    for key, b in BANKS.items():
        print(f"\n{b.name}: price {b.price:.2f}, P/TBV {b.price / b.tnav_ps:.2f}x, "
              f"market-implied ROTE {implied_rote(b):.1%}, "
              f"NII sensitivity +100bp {b.sens_up_100 / b.nii_2027_base:.1%} of NII")
        for s, r in SCENARIOS.items():
            o = run(b, r)
            print(f"  {s:<22} NII {o['nii']:6.0f}m (disclosed {o['d_nii_disclosed']:+5.0f}, "
                  f"migration {o['d_migration']:+4.0f}, credit {o['d_credit']:+4.0f})  "
                  f"EPS {o['d_eps_c']:+5.1f}c  ROTE {o['rote']:.1%}  fair {o['fair_ps']:.2f} ({o['upside']:+.0%})")


def implied_coe(bank: Bank, rote: float) -> float:
    """Cost of equity at which the current price is fair, given a sustainable ROTE."""
    tbv = bank.tnav_ps * bank.shares_m
    excess = max(bank.cet1 - bank.cet1_target, 0) * bank.rwa_bn * 1000
    core_tbv = tbv - excess
    pt_core = (bank.price * bank.shares_m - excess) / core_tbv
    rote_core = rote * tbv / core_tbv
    return GROWTH + (rote_core - GROWTH) / pt_core


def monthly_path(end_rate: float, shape: str = "even", start: float = BASE_RATE) -> list[float]:
    """12 monthly ECB deposit rates for 2027, moving in 25bp steps from `start` to `end_rate`.
    shape: 'front' (moves in Jan-Apr), 'even' (spread across the year), 'back' (Sep-Dec)."""
    steps = round((end_rate - start) / 0.25)
    if steps == 0:
        return [start] * 12
    window = {"front": (0, 4), "even": (0, 12), "back": (8, 12)}[shape]
    lo, hi = window
    months = [lo + int(i * (hi - lo) / abs(steps)) for i in range(abs(steps))]
    rate, path, step = start, [], 0.25 if steps > 0 else -0.25
    for mth in range(12):
        rate += step * months.count(mth)
        path.append(round(rate, 2))
    return path
