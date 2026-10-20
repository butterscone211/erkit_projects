"""The research note. Text lives in note.md; numbers are filled from the model at render time,
so the note and the dashboard always agree."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import pandas as pd
import streamlit as st

import model as m

HERE = Path(__file__).resolve().parents[1]

rows, values = [], {}
for k, b in m.BANKS.items():
    for s, rate in m.SCENARIOS.items():
        r = m.run(b, rate)
        rows.append({"Bank": b.name, "Scenario": s, "2027 avg ECB rate": f"{rate:.2f}%",
                     "NII (€m)": f"{r['nii']:,.0f}", "EPS impact": f"{r['d_eps_c']:+.1f}c",
                     "ROTE": f"{r['rote']:.1%}", "Fair value": f"€{r['fair_ps']:.2f}",
                     "vs price": f"{r['upside']:+.0%}"})
    values[f"{k}_price"] = f"€{b.price:.2f}"
    values[f"{k}_ptbv"] = f"{b.price / b.tnav_ps:.2f}x"
    values[f"{k}_implied_rote"] = f"{m.implied_rote(b):.1%}"
    values[f"{k}_implied_coe"] = f"{m.implied_coe(b, m.run(b, m.BASE_RATE)['rote']):.1%}"
    values[f"{k}_sens"] = f"{b.sens_up_100 / b.nii_2027_base:.1%}"

text = (HERE / "note.md").read_text().format(**values)
head, _, tail = text.partition("[[SCENARIO_TABLE]]")
st.markdown(head)
st.dataframe(pd.DataFrame(rows), hide_index=True, width="stretch")
st.markdown(tail)
st.download_button("Download note (Markdown)", text.replace("[[SCENARIO_TABLE]]", pd.DataFrame(rows).to_markdown(index=False)),
                   file_name="irish-banks-ecb-note.md")
