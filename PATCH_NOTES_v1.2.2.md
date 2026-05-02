# Dawn v1.2.2 Patch Notes

## Purpose
Tune Dawn for more realistic XAU/USD M15 breakout exits and improve SL/TP visibility.

## Strategy/risk changes
- TP changed from `range × 1.50` to `range × 1.00`.
- `rr_ratio` changed to `2.0` for a cleaner minimum RR expectation.
- `max_rr_ratio` lowered to `2.5` to avoid unrealistic M15 targets after SL clamps.
- `max_trades_day` aligned to `2` because Dawn has only two entry windows: London and NY.
- SL remains `range × 0.50`, clamped between `$15` and `$35`.
- Daily loss stop remains `$150`.

## Telegram improvements
- Startup message now shows dry-run status, signal/trend timeframe, SL raw formula, SL clamp, TP formula, RR cap, daily loss stop, and reset time.
- Trade-open message now includes range high/low/size, raw SL to final SL, TP distance, RR, and broker SL/TP confirmation check.

## Validation
- Python compile check passed for all `.py` files.
- `__pycache__` and `.pyc` files removed from package.
