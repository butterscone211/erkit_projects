# Irish banks: the ECB matters less than the market thinks

*Draft, personal research, not investment advice. Prices as of 20 October 2026.*

**Bottom line.** Across a range from three cuts to two hikes in 2027, AIB's and Bank of Ireland's net interest income moves by less than 3%. Structural hedges now drive earnings growth, not the ECB. The bigger question for the shares is valuation: at {BOI_ptbv} (Bank of Ireland) and {AIB_ptbv} (AIB) tangible book, the market already prices a sustainable ROTE of about {BOI_implied_rote} and {AIB_implied_rote}, above what either bank earns today.

## 1. Rate sensitivity is small and falling

- Each bank's own disclosure: a +100bp parallel move adds about {BOI_sens} (Bank of Ireland) and {AIB_sens} (AIB) to 2027 NII.
- Bank of Ireland's July hedge addition cut its sensitivity by about 30%. Around 60% of its NII growth to 2028 comes from reinvesting maturing swaps at higher yields.
- Cross-check: Bank of Ireland's unhedged current accounts plus equity are about €12bn. At a 2% deposit beta, a 100bp cut costs about €120m, matching its disclosed €(120)m. The same method implies AIB hedges about €54bn of euro free funds; confirm against its annual report.

## 2. Hikes are not good news once deposits move

Disclosed sensitivities assume a static balance sheet. In 2022-23, Irish household term deposits rose from 2% to 11% of the total and kept rising while the ECB cut. Adding that migration and a modest rise in impairments, two more hikes leave NII roughly flat and profit slightly lower.

[[SCENARIO_TABLE]]

## 3. Valuation: the price assumes the 2028 targets are met

At an 11% cost of equity, both banks screen above fair value in every scenario. The price is fair only if investors accept a cost of equity of about {BOI_implied_coe} (Bank of Ireland) and {AIB_implied_coe} (AIB), or if ROTE reaches the 16% that Bank of Ireland targets for 2028.

## Risks to this view

- Faster hedge reinvestment or loan growth than assumed lifts ROTE without any help from rates.
- Excess capital returned faster than expected (AIB holds about 2 points of CET1 above target).
- A lower cost of equity as Irish bank risk premia compress further.

## Method and sources

Inputs: H1 2026 results and presentations of AIB Group and Bank of Ireland; ECB Data Portal (MIR, BSI) via the erkit pipeline. Assumptions, including AIB's derived tangible book and 2027 NII, are listed in model.py.
