import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

import model as m

st.title("What the ECB path means for Irish bank earnings")
st.caption("2027 scenario engine for AIB and Bank of Ireland. Inputs from H1 2026 results; "
           "assumptions marked in model.py. Personal research, not investment advice.")

# ---------- controls ----------
with st.sidebar:
    st.header("ECB path for 2027")
    end_rate = st.slider("Deposit rate at end-2027 (%)", 1.00, 3.50, 2.50, 0.25)
    shape = st.radio("Timing of moves", ["front", "even", "back"], index=1, horizontal=True,
                     format_func={"front": "Early", "even": "Spread", "back": "Late"}.get)
    st.header("Assumptions")
    overlays = st.toggle("Include deposit migration and credit overlays", value=True,
                         help="The banks' disclosed sensitivity assumes a static balance sheet. "
                              "Overlays add term-deposit migration and higher impairments when rates rise.")
    m.COE = st.slider("Cost of equity (%)", 9.0, 13.0, 11.0, 0.25) / 100
    m.MIGRATION_PP_PER_100BP = st.slider("Term-deposit migration (pp of deposits per +100bp)", 0.0, 16.0, 8.0, 1.0)

path = m.monthly_path(end_rate, shape)
avg = sum(path) / 12
results = {k: m.run(b, avg, overlays) for k, b in m.BANKS.items()}

# ---------- path chart ----------
months = pd.date_range("2027-01-31", periods=12, freq="ME")
fig = go.Figure()
fig.add_scatter(x=months, y=[m.BASE_RATE] * 12, name="Banks' guidance (2.50%)",
                line=dict(dash="dash", color="#888"))
fig.add_scatter(x=months, y=path, name="Your path", line=dict(shape="hv", width=3))
fig.update_layout(height=260, margin=dict(l=10, r=10, t=30, b=10), yaxis_title="ECB deposit rate (%)",
                  title=f"2027 average {avg:.2f}% vs 2.50% in guidance ({(avg - m.BASE_RATE) * 100:+.0f}bp)",
                  legend=dict(orientation="h", y=-0.25))
st.plotly_chart(fig, width="stretch")

# ---------- KPI tiles ----------
cols = st.columns(2)
for col, (k, r) in zip(cols, results.items()):
    b = m.BANKS[k]
    with col:
        st.subheader(b.name)
        a, c = st.columns(2)
        a.metric("2027 NII", f"€{r['nii']:,.0f}m", f"{r['nii'] - b.nii_2027_base:+,.0f}m vs guidance")
        c.metric("EPS impact", f"{r['d_eps_c']:+.1f}c")
        a.metric("ROTE", f"{r['rote']:.1%}")
        c.metric("Fair value", f"€{r['fair_ps']:.2f}", f"{r['upside']:+.0%} vs €{b.price:.2f}")

# ---------- NII bridge ----------
st.subheader("Where the NII change comes from")
bridge = go.Figure()
for k, r in results.items():
    bridge.add_bar(name=m.BANKS[k].name, x=["Disclosed rate sensitivity", "Deposit migration", "Credit (impairments)"],
                   y=[r["d_nii_disclosed"], r["d_migration"], r["d_credit"]])
bridge.update_layout(barmode="group", height=300, yaxis_title="€m, 2027 pre-tax",
                     margin=dict(l=10, r=10, t=10, b=10), legend=dict(orientation="h", y=-0.2))
if all(abs(r[k]) < 0.5 for r in results.values() for k in ("d_nii_disclosed", "d_migration", "d_credit")):
    st.info("Your path averages 2.50%, the same as the banks' guidance, so there is nothing to bridge. Move the slider.")
else:
    st.plotly_chart(bridge, width="stretch")
st.caption("Disclosed sensitivity: EUR book, instantaneous parallel shift, from each bank's H1 2026 presentation, "
           "scaled linearly to the 2027 average rate. Credit is a pre-tax profit item, shown here for comparison.")

# ---------- fair value grid ----------
st.subheader("Fair value: cost of equity vs end-2027 rate")
bank_key = st.selectbox("Bank", list(m.BANKS), format_func=lambda k: m.BANKS[k].name)
coe_keep = m.COE
grid = {}
for coe in (0.10, 0.105, 0.11, 0.115, 0.12):
    m.COE = coe
    grid[f"{coe:.1%}"] = {f"{e:.2f}%": m.run(m.BANKS[bank_key], sum(m.monthly_path(e, shape)) / 12, overlays)["fair_ps"]
                          for e in (1.75, 2.25, 2.50, 2.75, 3.25)}
m.COE = coe_keep
st.dataframe(pd.DataFrame(grid).T.style.format("€{:.2f}").background_gradient(axis=None, cmap="RdYlGn"),
             width="stretch")
st.caption(f"Rows: cost of equity. Columns: ECB rate at end-2027. Current price €{m.BANKS[bank_key].price:.2f}; "
           f"market-implied ROTE {m.implied_rote(m.BANKS[bank_key]):.1%}.")
