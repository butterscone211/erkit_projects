"""Example: how a project reuses the shared store. First building block of Project 1.

Deposit beta = how much of an ECB rate move Irish banks pass on to savers.
Low beta = banks keep more of the rate rise as net interest income.
"""
import erkit

df = erkit.get_many(
    ["ecb_dfr", "ie_hh_overnight_dep_rate", "ie_hh_term_dep_rate", "ie_mortgage_rate"],
    start="2021-01-01", freq="ME",
).dropna()

def beta(col, start, end):
    d_ecb = df.loc[end, "ecb_dfr"] - df.loc[start, "ecb_dfr"]
    return (df.loc[end, col] - df.loc[start, col]) / d_ecb

cycles = {"2022-23 hiking cycle": ("2022-06-30", "2023-12-31")}
for name, (s, e) in cycles.items():
    print(f"\n{name}: ECB deposit rate {df.loc[s,'ecb_dfr']:.2f}% -> {df.loc[e,'ecb_dfr']:.2f}%")
    for col in ["ie_hh_overnight_dep_rate", "ie_hh_term_dep_rate", "ie_mortgage_rate"]:
        print(f"  {col:<26} beta {beta(col, s, e):5.2f}")

print("\nLatest month:")
print(df.tail(1).T.round(2).to_string(header=False))
