## 2026-07-28 — What it is, stack
**Source:** Pappa T session (cross-project status survey), IQ's own 1_Documentation/README.md
**Status:** active

IQ Option Signal Generator — a regime-filtered signal generator for IQ Option
digital-options trading, aimed at avoiding "using the wrong strategy for the
current market condition." Pure-standard-library Python 3.7+ CLI (`main.py`),
optional `yfinance`/`requests` for live market data with a fallback path. Lives
at `Pappa T/IQ/` — folder inside the Pappa T vault repo, not its own git repo, no
git repo of its own at all.

**Signal-generation-only tool — does not place trades.** The user manually enters
candle data (or lets it load demo data), gets a CALL/PUT signal with a 0-100%
confidence score, and executes manually on the IQ Option platform. All signals log
to a dated CSV (`signals_YYYYMMDD.csv`) for later review.

**Core logic (reusable if this pattern recurs elsewhere):**
- **Regime detection**: ADX ≥ 25 → TRENDING, < 25 → RANGING. Strategy is designed
  to excel in RANGING markets; confidence is explicitly halved in TRENDING regimes
  as a built-in warning that reversal signals are riskier there.
- **Signal trigger**: RSI ≤ 30 (oversold) or ≥ 70 (overbought), combined with
  Stochastic K ≤ 20 / ≥ 80 confluence.
- **Confidence scoring**: starts at a 50% base, +15% for extreme RSI (≤20/≥80),
  +10% for Stochastic K/D alignment, +15% ranging-market bonus, +10% for weak ADX
  (<20); trending-market penalty multiplies the whole score by 0.5.
- **Risk management, hardcoded as non-optional stops**: 25% daily-loss hard stop
  (blocks further trading until next session) and a Martingale-step tracker that
  hard-blocks at step 4+ (after 4 consecutive losses) — both framed in the README
  as deliberate account-blowup prevention, not suggestions.

Its `AGENT.md` (in `1_Documentation/`) is the same generic "MASTER AGENT
DIRECTIVE" boilerplate template also found verbatim in `Tenders/AGENT.md` — a
reused project-scaffold template, not project-specific content; see
`tenders-sa.md` for the one place it's worth reading in full.

**Not carried over:** no live trade history, balances, or account data exist in
this project as surveyed — it's a standalone signal tool with no persisted
personal financial results beyond the CSV log format itself.
