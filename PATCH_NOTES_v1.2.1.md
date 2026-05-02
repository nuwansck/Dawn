# Dawn v1.2.1 Patch Notes

Applied fixes requested:

1. Fixed breakeven `trigger_dist` bug
   - Replaced the bad `trigger_usd=` Telegram argument with `trigger_dist=`.

2. Saved trade state before Telegram
   - Breakeven state is now saved immediately after broker-side SL modification succeeds.
   - Telegram alert failure is caught and logged without breaking the trade cycle.

3. Aligned Dawn windows in `bot.py`
   - Replaced legacy hour-only Asian/London/US windows with minute-aware Dawn windows:
     - London: 15:00–16:30 SGT
     - US/NY: 20:30–22:00 SGT

4. Added closed/missing trade handling
   - If OANDA no longer returns a local open trade, the record is flagged with:
     - `broker_missing`
     - `needs_reconcile`
     - `missing_reason`
     - `missing_detected_at_sgt`

5. Added dry-run mode
   - New setting: `dry_run`
   - New environment override: `DRY_RUN=true`
   - When enabled, the bot calculates the signal and records a DRY_RUN attempt but does not send an OANDA order.

6. Improved Telegram messages
   - Trade-open alerts now show margin mode, required/free margin, margin usage, and adjusted units when applicable.
   - XAU/USD Telegram price display now defaults to 2 decimals.

7. Added daily dollar safety stop
   - New setting: `daily_loss_limit_usd`
   - Default in bundled settings: `150.0`
   - Set `0` to disable.

8. Cleaned API-key logging
   - Logs now show `API Key: configured` or `API Key: missing` instead of printing the first characters of the key.

Validation performed:

- `python -m compileall -q .` completed successfully.
- Quick import checks passed for session-window logic and Telegram templates.
- Removed `__pycache__` directories from the final ZIP.
