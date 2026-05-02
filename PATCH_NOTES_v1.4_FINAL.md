# Dawn v1.4 Final

## Final cleanup

- Fixed Telegram startup duplication: `Dawn v1.3 v1.3 started` is now `Dawn v1.4 started`.
- Removed dry-run mode completely from code, settings, scheduler, and Telegram startup message.
- Updated all bundled settings to version `1.4`.
- Kept final trading logic unchanged from the realistic TP build:
  - Pair: `XAU_USD` / XAU/USD
  - Signal timeframe: M15
  - Trend filter: H1
  - SL: 50% x range, clamped $15-$35
  - TP: 100% x range
  - RR cap: 1:2.5
  - Daily loss stop: $150
- Removed old patch-note files and Python cache files from the ZIP.

## Expected startup Telegram

```text
🤖 Dawn v1.4
──────────────────────
🌅 Dawn v1.4 started
```
