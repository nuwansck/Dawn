# Dawn v1.3 Patch Notes

## Purpose
Fix Railway persistent-settings drift where the deployed startup Telegram alert could still show stale values like `TP: 150% x range` and `RR cap: 1:1.5` even though the bundled v1.3 settings had been changed.

## Changes
- Version bumped to `Dawn v1.3`.
- Force-syncs Dawn strategy/risk keys from bundled `settings.json` into `/data/settings.json` on deploy:
  - `tp_mode`
  - `dawn_sl_range_pct`
  - `dawn_tp_range_pct`
  - `dawn_range_min_usd` / `dawn_range_max_usd`
  - `sl_min_usd` / `sl_max_usd`
  - `rr_ratio`
  - `max_rr_ratio`
- Keeps realistic M15 exit defaults:
  - `SL = 50% x range`
  - `TP = 100% x range`
  - `Final SL clamp = $15-$35`
  - `RR cap = 1:2.5`

## Expected startup Telegram after redeploy
- `TP: 100% x range`
- `RR cap: 1:2.5`

If Railway logs show `Updated ... key(s) in persistent settings`, that is expected and means stale persistent values were corrected.
