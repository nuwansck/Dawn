# Dawn v1.4 Final — XAU/USD M15 Session Breakout Bot

Dawn v1.4 is a demo-ready OANDA bot for XAU/USD session range breakouts.

## Strategy

| Item | Value |
|---|---|
| Instrument | XAU/USD (`XAU_USD`) |
| Signal timeframe | M15 |
| Trend filter | H1 EMA21 |
| Bot cycle | 5 minutes |
| Entry type | First completed M15 candle close beyond prior range |

## Entry windows — SGT

| Window | Entry time | Range used |
|---|---:|---:|
| London | 15:00–16:30 | 07:00–15:00 |
| New York | 20:30–22:00 | 15:00–20:30 |

## SL/TP

| Setting | Value |
|---|---:|
| Range filter | $15–$80 |
| Raw SL | 50% x range |
| Final SL clamp | $15–$35 |
| TP | 100% x range |
| RR cap | 1:2.5 |

## Safety

- Demo mode by default.
- Max 1 open trade.
- Max 2 trades/day.
- Max 2 losses/day.
- Daily loss stop: $150.
- News filter enabled.
- Telegram startup and trade alerts enabled.

## v1.4 cleanup

- Fixed startup duplication so Telegram shows `Dawn v1.4 started`, not `Dawn v1.3 v1.3 started`.
- Removed dry-run mode from code, settings, scheduler, and Telegram templates.
- Removed old patch-note files and stale documentation from the ZIP.
