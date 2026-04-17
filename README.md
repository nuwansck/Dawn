# Dawn — XAU/USD Session Breakout Bot

**Version:** 1.1
**Instrument:** XAU/USD (gold)
**Timeframe:** M15
**Target:** 35-40+ point intraday swings
**Deployed on:** OANDA (demo first), Railway (Singapore region)

---

## Strategy in one paragraph

Dawn trades breakouts of the prior session's range during the first 90 minutes after London open and NY open. When the London session begins at 15:00 SGT, Dawn watches the Asian session's high and low (07:00–15:00 SGT). If the next completed M15 candle closes above the Asian high, Dawn goes long; below the low, short. Same logic for NY at 20:30 SGT against the prior London range. One trade per window maximum, two windows per day maximum.

## Why this strategy on gold

- London and NY opens bring the highest volume and cleanest directional moves of the gold trading day
- Breaking the prior session's range has meaningful follow-through when combined with a higher-timeframe trend filter
- Binary entry trigger — no scoring ambiguity, no confluence gaming
- Target size naturally in the 35-90 point zone (range × 1.5) — matches where gold actually moves on an intraday basis
- Only 1-2 trades/day — low enough noise to evaluate edge quickly

## Core logic

| Element | Value |
|---|---|
| Range window (London) | 07:00–15:00 SGT (Asian session) |
| Entry window (London) | 15:00–16:30 SGT (first 90 min after open) |
| Range window (NY) | 15:00–20:30 SGT (London + pre-NY) |
| Entry window (NY) | 20:30–22:00 SGT (first 90 min after open) |
| Trigger | M15 candle close beyond range high/low |
| SL | range × 0.50 (clamped $15–$35) |
| TP | range × 1.50 (clamped by max_rr_ratio × SL) |
| Position size | $100 fixed risk per trade |
| Max trades/day | 2 (1 per window) |
| Max losses/day | 2 (hard stop) |

## Filters

1. **Range size:** must be 15–80 points. Too small = noise; too large = volatile trap day.
2. **H1 EMA21 trend filter:** BUY only if H1 close > EMA21; SELL only if below.
3. **Spread limit:** skip if spread > 100 pips (tighter than Rogue's 140 — breakouts need low slippage).
4. **News blackout:** ±30 min around high-impact USD events (reused from Rogue infrastructure).
5. **Friday cutoff:** no new entries after 22:00 SGT Friday.
6. **Direction cooldown:** 120 min after any SL in the same direction.
7. **Consecutive-SL guard:** hard block after 1 SL in same direction.

## Breakeven

At 1× SL profit, Dawn partial-closes 50% of the position and moves SL to the entry price plus the spread (spread-adjusted BE inherited from Rogue v1.3). This converts the remaining 50% into a risk-free runner — either it hits TP or stops at true zero PnL.

## Expected behavior

| Metric | Estimate |
|---|---|
| Trades per week | 4-8 (2 windows × 5 days, many filtered out) |
| Win rate | 45-55% (estimate; no live data yet) |
| Avg win | 35-45 points (range × 1.5, typical range 25-35) |
| Avg loss | 15-25 points (range × 0.5, post-clamp) |
| Max drawdown | 2 losing trades/day × $30-35 = ~$70/day worst case |

## Relationship to Rogue

Dawn is a **sibling bot** to Rogue, not a replacement. Both trade XAU/USD M15. The strategies are different, the accounts are different, the deploys are independent. Compare performance over time to see which (if either) has an edge on gold.

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-17 | Initial Dawn release. Built on Rogue v1.3 infrastructure. Session range breakout strategy replaces CPR scoring. Fixed $100 position sizing. Range-based SL/TP via new `sl_mode: range_based` and `tp_mode: range_based`. Spread-adjusted BE inherited from Rogue v1.3. |
| 1.1 | 2026-04-17 | Post-deploy audit fixes: **(critical)** flipped `session_only: false` so Dawn no longer skips the 15:00-15:59 SGT hour — the legacy Rogue `SESSIONS` tuple in bot.py (Asian 08-15, London 16-20, US 21-23) was pre-gating entries based on hour ranges that don't match Dawn's windows. Dawn now gates solely via `signals.py._active_entry_window`. **(cosmetic)** Telegram signal-update messages now show "Range size" instead of "CPR width" when Dawn engine is active. **(cosmetic)** Same-setup guard reworked to compare setup-name + direction when a pivot isn't present (Dawn's levels have no pivot). |
