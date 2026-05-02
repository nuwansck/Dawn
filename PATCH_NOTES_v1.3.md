# Dawn v1.3 Patch Notes

## Purpose

Version label update from `Dawn v1.2.3` to `Dawn v1.3`.

## Strategy / risk behavior

No strategy behavior was changed from v1.2.3. This version keeps the realistic M15 exit model:

- Pair: `XAU_USD` / XAU/USD
- Signal timeframe: M15
- Trend timeframe: H1
- SL: 50% x range
- SL clamp: $15-$35
- TP: 100% x range
- RR cap: 1:2.5
- Daily safety: 2 losses/day, 2 trades/day, daily loss stop $150

## Why this version exists

This is a clean version bump so Telegram, settings, and logs show `Dawn v1.3` instead of `Dawn v1.2.x`.
