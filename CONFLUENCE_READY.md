# Dawn Bot — Technical Documentation

**Version:** 1.1
**Release date:** 2026-04-17
**Instrument:** XAU/USD M15
**Base:** Rogue v1.3 infrastructure (signals + strategy rewritten)

---

## Overview

Dawn is an automated gold trading bot designed around the London and NY session opens. Unlike CPR-based strategies which trade continuously against pivot levels, Dawn only trades during two 90-minute windows per day: immediately after London opens (15:00 SGT) and immediately after NY opens (20:30 SGT). In each window it watches for a breakout of the previous session's range, fires a single trade on confirmation, and then stands down.

The core thesis: the London and NY opens bring the highest volume and cleanest directional moves of the gold trading day. Breaking out of the preceding session's range during these opens has statistically better follow-through than mid-day breakouts. By restricting entries to two narrow windows per day, Dawn trades less, sleeps more, and avoids mid-session chop.

---

## Strategy

### Windows

| Window | Range Source | Range Hours | Entry Hours | Duration |
|---|---|---|---|---|
| London breakout | Asian session | 07:00–15:00 SGT | 15:00–16:30 SGT | 90 min |
| NY breakout | London + pre-NY | 15:00–20:30 SGT | 20:30–22:00 SGT | 90 min |

### Entry trigger

Binary — no scoring, no confluence, no aggregation:

- **BUY** when the last completed M15 candle closes strictly above the range high
- **SELL** when the last completed M15 candle closes strictly below the range low
- **Wait** otherwise — no interior signals, no wick breaks

One trade per entry window max. Once either side triggers or the window closes, Dawn stands down until the next window.

### Range-size filter (the critical one)

```
15 ≤ range_size ≤ 80  (points)
```

- **< 15 points:** range too narrow, likely dead session / holiday. Breakout is noise.
- **> 80 points:** range already elevated, typically news-driven day. False-breakout probability high.

This filter alone removes maybe 20-30% of potential triggers — and most of them would have been losers.

### H1 EMA21 trend filter

- BUY blocked if H1 close < H1 EMA21
- SELL blocked if H1 close > H1 EMA21

Hard block, inherited from Rogue v1.3. Prevents the worst of all gold trade types: the counter-trend breakout attempt.

### SL / TP

```
SL_raw = range_size × dawn_sl_range_pct   (default 0.50)
SL     = clamp(SL_raw, sl_min_usd, sl_max_usd)   (default 15 ≤ SL ≤ 35)

TP_raw = range_size × dawn_tp_range_pct   (default 1.00)
TP     = min(TP_raw, SL × max_rr_ratio)   (default RR cap 1.5)
```

Both SL and TP scale with the range. Tight range days = tighter SL and smaller TP. Wider range days (within the 80-point cap) = more room on both sides.

### Position sizing

```
position_usd  = dawn_position_usd   (default $100)
units         = position_usd / SL_usd
```

Flat risk. No score tiers. Every Dawn trade risks exactly $100.

---

## Full setting reference

```json
{
  "bot_name": "Dawn v1.1",
  "version": "1.1",
  "demo_mode": true,

  "signal_threshold": 1,

  "dawn_position_usd": 100,
  "dawn_sl_range_pct": 0.50,
  "dawn_tp_range_pct": 1.00,
  "dawn_range_min_usd": 15.0,
  "dawn_range_max_usd": 80.0,

  "sl_mode": "range_based",
  "tp_mode": "range_based",
  "sl_min_usd": 15.0,
  "sl_max_usd": 35.0,
  "rr_ratio": 2.0,
  "max_rr_ratio": 2.5,

  "breakeven_enabled": true,
  "breakeven_spread_adjust": true,
  "breakeven_trigger_usd": 15.0,

  "max_concurrent_trades": 1,
  "max_trades_day": 6,
  "max_losing_trades_day": 2,
  "max_losing_trades_session": 2,

  "max_spread_pips": 100,
  "spread_limits": { "London": 100, "US": 100, "Asian": 140 },

  "session_only": false,
  "session_thresholds": { "London": 1, "US": 1, "Asian": 1 },
  "london_session_enabled": true,
  "us_session_enabled": true,
  "asian_session_enabled": true,

  "max_trades_london": 1,
  "max_trades_us": 1,
  "max_trades_asian": 1,

  "news_filter_enabled": true,
  "friday_cutoff_hour_sgt": 22,

  "same_setup_cooldown_min": 90,
  "consecutive_sl_guard": 1,
  "sl_direction_cooldown_min": 120,

  "daily_report_hour_sgt": 23,
  "daily_report_minute_sgt": 30,

  "h1_trend_filter_enabled": true,
  "h1_ema_period": 21,
  "require_candle_close": true
}
```

---

## Risk profile

Per-trade risk: **$100** (fixed).
Worst day (2 losses): **–$200**.
Typical trade outcomes:

- **Full SL:** –$15 to –$35 per trade (range-dependent)
- **Full TP:** +$22 to +$90 per trade (range × 1.0)
- **Breakeven stop after partial close:** +$8 to +$18 (locked half at 1× SL, runner stops flat)

On a $5,000 account:
- Max daily drawdown: ~4%
- Max weekly drawdown (10 losses): ~14% (but daily caps would stop this — max 2 losses/day × 5 days = 10 losses theoretical ceiling, but direction cooldown makes this unlikely)

---

## Telegram alerts

### Startup

```
🌅 Dawn v1.1 started
Mode: DEMO | Balance: $5,000.00
Pair: XAU/USD (M15)
Strategy: Session Breakout + H1 Trend Filter | Cycle: 5 min
Entry: Binary — first M15 close beyond prior range
Size: $100 per trade (fixed risk)
H1 filter: ✅ HARD

Entry windows (SGT)
  🇬🇧 15:00–16:30  London open  (range 07:00–15:00)
  🗽 20:30–22:00  NY open      (range 15:00–20:30)
Range filter: 15–80 points | SL 50% × range | TP 100% × range

Daily caps: 2 losses, 2 trades | Global: 1 open | Reset: 08:00 SGT
```

### Breakout trigger

The per-trade signal message will show:
- Setup name (e.g. "London Range High Break")
- Range boundaries and size
- SL / TP / RR
- H1 EMA confirmation value

---

## Architecture notes

Dawn reuses all of Rogue v1.3's non-strategy infrastructure:

- `oanda_trader.py` — broker integration (unchanged)
- `database.py` — persistence
- `news_filter.py` + `calendar_fetcher.py` — Forex Factory economic calendar
- `telegram_alert.py` — messaging
- `reporting.py` — daily / weekly / monthly performance reports
- `scheduler.py` — 5-minute trade cycle + report scheduling
- `startup_checks.py` — pre-flight validation
- `reconcile_state.py` — OANDA state reconciliation
- `check_breakeven` in `bot.py` — the spread-adjusted breakeven from Rogue v1.3

Only these files have Dawn-specific logic:
- `signals.py` — complete rewrite (session breakout engine)
- `settings.json` — Dawn-specific keys
- `telegram_templates.py` — `msg_startup` rewritten (other templates inherited)
- `bot.py` — added `range_based` branches in `compute_sl_usd` and `compute_tp_usd`
- `version.py` — BOT_NAME changed

---

## Version History

| Version | Date | Change |
|---|---|---|
| 1.0 | 2026-04-17 | Initial Dawn release. Built on Rogue v1.3 infrastructure. Session range breakout strategy replaces CPR scoring. Fixed $100 position sizing. Range-based SL/TP via new `sl_mode: range_based` and `tp_mode: range_based`. Spread-adjusted BE inherited from Rogue v1.3. |
| 1.1 | 2026-04-17 | Post-deploy audit fixes (4 issues). **Critical 1** — `session_only: false` applied. Root cause: bot.py's legacy Rogue `SESSIONS` tuple (Asian 08-15, London 16-20, US 21-23) was pre-gating entries. With `asian_session_enabled: false` (as in v1.0) hour 15 fell into a disabled session and got blocked — costing Dawn the first hour of the London window (15:00-15:59 SGT), which is the highest-edge hour for session breakouts. **Critical 2** — `max_trades_asian: 0 → 1`. Even with `session_only: false`, the downstream `window_cap` check (bot.py:1436) would still fire at 15:00 SGT because `trades_in_window (0) >= max_trades_asian (0)` evaluates True. Raising the cap to 1 lets the cycle proceed; Dawn's own `_active_entry_window` remains the real gate. Both critical fixes are required — either alone is insufficient. **Cosmetic 1** — Telegram signal-update "CPR width" line replaced with "Range size" when Dawn engine is active. **Cosmetic 2** — Same-setup guard made strategy-agnostic: when levels lack a pivot (non-CPR strategies), it now uses setup-name + direction equality instead of pivot equality. |
