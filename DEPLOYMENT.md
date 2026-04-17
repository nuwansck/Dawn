# Dawn Deployment Guide

How to deploy Dawn v1.0 as a **separate** Railway service with its **own** OANDA account, independent from Rogue.

---

## Prerequisites

Before starting, have ready:
- A **new** OANDA demo account (separate from the one Rogue uses)
- Its **API token** (generate from OANDA portal → Manage API Access)
- Its **account ID** (format: `101-003-XXXXXXXX-YYY`, different from Rogue's)
- A Telegram group or channel (new recommended, same-as-Rogue acceptable)
- Railway account with deploy-from-repo or deploy-from-image capability

**Do not re-use Rogue's OANDA credentials.** That would have both bots fighting over the same account balance and orders, which causes real problems.

---

## Step 1 — Create a new OANDA demo account

1. Log into your OANDA portal
2. Go to **Add Sub-Account** (or equivalent — labels change occasionally)
3. Create a new demo sub-account (fxPractice)
4. Fund it to the same balance you have on Rogue's demo (default `$5,000` for fair comparison)
5. Note the account ID — it'll differ from Rogue's by the last 3 digits typically
6. Go to **Manage API Access** → **Generate Token** — grab the new API token

**Important:** an OANDA API token grants access to **all** sub-accounts under that parent. The bot targets one specific account via `OANDA_ACCOUNT_ID`, so make sure that env var points at the new account, not Rogue's.

---

## Step 2 — Create a new Railway service

1. In Railway, create a new service in the same project as Rogue (or a new project — either works)
2. Deploy from the Dawn source (either this repo or the uploaded zip)
3. Set the region to **Singapore** to match Rogue for latency parity
4. Create a new **persistent volume** mounted at `/data` (Dawn's DATA_DIR)
   - Size: 1 GB is plenty (90-day rolling trade history is small JSON)
   - This must be a NEW volume — do not share with Rogue

---

## Step 3 — Environment variables

In the new Railway service's Variables tab, set **exactly these** (do not copy from Rogue's service):

| Variable | Value | Notes |
|---|---|---|
| `OANDA_API_KEY` | *[new token from Step 1]* | The new account's API token |
| `OANDA_ACCOUNT_ID` | *[new account ID from Step 1]* | Format `101-003-XXXXXXXX-YYY` |
| `TELEGRAM_TOKEN` | *[bot token]* | Same bot is fine, or create a new one |
| `TELEGRAM_CHAT_ID` | *[chat/group ID]* | **Recommended: new group** so Dawn and Rogue messages don't interleave |
| `DATA_DIR` | `/data` | Matches the volume mount path |
| `PORT` | *(Railway auto-sets)* | Leave blank, Railway provides this |

---

## Step 4 — Verify before first cycle

After deploy, watch the Railway logs for these specific lines:

```
Dawn v1.0 — Scheduler starting
DATA_DIR : /data
Login success! Balance: $[your new account balance]
```

**If `Login success! Balance:` matches your NEW account balance, the env vars are correct.**

**If it matches Rogue's balance, STOP IMMEDIATELY** — you've set the wrong `OANDA_ACCOUNT_ID`. Fix before the next cycle runs.

---

## Step 5 — Verify the Telegram startup message

Dawn sends a startup message on first boot. It should look like:

```
🌅 Dawn v1.0 started
Mode: DEMO | Balance: $[new account balance]
Pair: XAU/USD (M15)
Strategy: Session Breakout + H1 Trend Filter | Cycle: 5 min
Entry: Binary — first M15 close beyond prior range
Size: $100 per trade (fixed risk)
H1 filter: ✅ HARD

Entry windows (SGT)
  🇬🇧 15:00–16:30  London open  (range 07:00–15:00)
  🗽 20:30–22:00  NY open      (range 15:00–20:30)
Range filter: 15–80 points | SL 50% × range | TP 150% × range

Daily caps: 2 losses, 2 trades | Global: 1 open | Reset: 08:00 SGT
```

If this message doesn't arrive, Telegram env vars are wrong or the chat ID is incorrect. Check the Railway logs for `Telegram sent!` vs error messages.

---

## Step 6 — First cycle behavior

Outside the London (15:00–16:30 SGT) and NY (20:30–22:00 SGT) entry windows, every 5-minute cycle will log:

```
=== Dawn v1.0 | [timestamp] ===
Outside entry window — idle
```

This is correct and expected. Dawn is **not a continuous-trading bot**. It only trades during the two 90-minute entry windows per day.

**During** an entry window, you'll see log lines like:

```
London range | high=XXXX.XX low=XXXX.XX size=XX.XX candles=N
London waiting | close=XXXX.XX high=XXXX.XX low=XXXX.XX
```

…until a breakout occurs, then:

```
Dawn FIRE | window=London dir=BUY | range=XX.XX sl=XX.XX tp=XX.XX
```

---

## Step 7 — Running alongside Rogue

Once both bots are live, they are **fully independent**:
- Different OANDA accounts → different balances, independent PnL
- Different Railway volumes → different `trade_history.json`, no interference
- Different Telegram groups (if you set it up that way) → clear message streams
- Same strategy infrastructure — both use the same code for broker integration, logging, reporting

You can update one without touching the other. You can stop one without affecting the other.

---

## Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| Logs show `Balance: $[wrong number]` | Wrong `OANDA_ACCOUNT_ID` | Set correct account ID in Railway vars, redeploy |
| No Telegram startup message | Wrong `TELEGRAM_CHAT_ID` or token | Check Railway logs for `Telegram send failed` |
| "Insufficient range data" every cycle during entry window | Timezone misconfig or clock drift | Check DATA_DIR, verify system time is UTC |
| Bot fires but order rejected | Account insufficient margin or instrument not enabled | Check OANDA account settings — fund to $5K minimum |
| Logs show `Rogue v1.x` instead of `Dawn v1.0` | Deployed wrong codebase to this service | Re-deploy the Dawn zip, ensure correct service |

---

## Rollback

If Dawn misbehaves, rollback is trivial:

1. In Railway, **Pause** the Dawn service (does not delete, just stops)
2. Rogue keeps running on its own service, unaffected
3. Fix the issue locally, redeploy when ready

You can also **Pause** Dawn at any time without affecting open positions on its OANDA account — OANDA's server-side SL/TP remain active even when the bot is offline.

---

## Monitoring during the 2-week evaluation

Track these metrics in parallel with Rogue:

- **Trade count:** Dawn should fire 3-8 trades per week (fewer than Rogue's 15-25)
- **Win rate:** compare directly with Rogue over the same window
- **Avg R-multiple per trade:** (pnl / $100 risk) — should cluster around +1.5R for wins, -1R for losses, +0.5R for BE-runner stops
- **Range-filter block rate:** how often is range outside 15-80? Log search: `range too small` or `range too large`
- **H1 trend-block rate:** how often does the trend filter kill a valid breakout? Log search: `H1 trend BLOCKED`

After 2 weeks, compare Dawn's equity curve against Rogue's. The winner isn't whichever has higher raw PnL — it's whichever has **lower variance** and **more predictable behavior** per trade.
